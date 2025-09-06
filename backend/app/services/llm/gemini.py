"""Gemini provider implementing LLMProvider with retry/backoff and fallback"""
from __future__ import annotations

import asyncio
from typing import Optional
import structlog

import google.generativeai as genai

try:
    # Precise 429 detection when available
    from google.api_core.exceptions import ResourceExhausted  # type: ignore
except Exception:  # pragma: no cover - fallback when dependency shape changes
    ResourceExhausted = Exception  # type: ignore

from app.core.config import Settings
from app.services.llm.base import LLMProvider


logger = structlog.get_logger()


class GeminiProvider(LLMProvider):
    """Google Gemini provider with built-in retries and fallback model."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._configured = bool(getattr(settings, "gemini_api_key", ""))
        self._model = None
        self._fallback_model = None

        if not self._configured:
            logger.warning("gemini_not_configured")
            return

        try:
            genai.configure(api_key=self._settings.gemini_api_key)
            model_name = getattr(self._settings, "gemini_model", "gemini-1.5-pro")
            self._model = genai.GenerativeModel(model_name)
        except Exception as e:  # pragma: no cover
            logger.error("gemini_model_init_error", error=str(e))
            self._configured = False
            self._model = None

        # Optional fallback model
        fallback_name = getattr(self._settings, "gemini_fallback_model", None)
        if fallback_name:
            try:
                self._fallback_model = genai.GenerativeModel(fallback_name)
            except Exception as e:  # pragma: no cover
                logger.warning("gemini_fallback_init_failed", error=str(e), model=fallback_name)
                self._fallback_model = None

    @property
    def is_configured(self) -> bool:
        return bool(self._configured and self._model is not None)

    def _is_rate_limit_error(self, e: Exception) -> bool:
        text = str(e).lower()
        return (
            isinstance(e, ResourceExhausted)
            or "429" in text
            or "rate limit" in text
            or "quota" in text
            or "exceeded" in text
        )

    async def generate(self, prompt: str) -> str:
        """Generate text using Gemini with retries and fallback.

        Always returns a string; friendly messages are returned on failure.
        """
        if not self.is_configured:
            return "申し訳ございません。現在Gemini APIが設定されていないため、回答を提供できません。API設定を確認してください。"

        max_retries = getattr(self._settings, "gemini_max_retries", 3)
        base_backoff = float(getattr(self._settings, "gemini_retry_backoff_seconds", 2.0))
        timeout_s = float(getattr(self._settings, "llm_generate_timeout_seconds", 30.0))

        last_err: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                response = await asyncio.wait_for(
                    self._model.generate_content_async(prompt),  # type: ignore[union-attr]
                    timeout=timeout_s,
                )
                text = getattr(response, "text", "")
                text = text.strip() if isinstance(text, str) else ""
                if not text:
                    logger.warning("gemini_empty_text", attempt=attempt + 1)
                    last_err = ValueError("empty response text")
                    break
                return text
            except asyncio.TimeoutError:
                logger.error("gemini_generate_timeout", attempt=attempt + 1, timeout_s=timeout_s)
                last_err = asyncio.TimeoutError(f"timeout after {timeout_s}s")
                break
            except Exception as e:  # Broad catch to ensure graceful degradation
                last_err = e
                if self._is_rate_limit_error(e):
                    backoff = base_backoff * (2 ** attempt)
                    logger.warning(
                        "gemini_rate_limited",
                        attempt=attempt + 1,
                        backoff=backoff,
                        error=str(e),
                    )
                    await asyncio.sleep(backoff)
                    continue
                else:
                    logger.error("gemini_generate_error", attempt=attempt + 1, error=str(e))
                    break

        # Fallback model
        if self._fallback_model is not None:
            try:
                logger.info(
                    "gemini_fallback_try",
                    model=getattr(self._settings, "gemini_fallback_model", None),
                )
                response = await asyncio.wait_for(
                    self._fallback_model.generate_content_async(prompt),  # type: ignore[attr-defined]
                    timeout=timeout_s,
                )
                logger.info(
                    "gemini_fallback_used",
                    model=getattr(self._settings, "gemini_fallback_model", None),
                )
                fb_text = getattr(response, "text", "")
                fb_text = fb_text.strip() if isinstance(fb_text, str) else ""
                if not fb_text:
                    logger.warning("gemini_fallback_empty_text")
                else:
                    return fb_text
            except asyncio.TimeoutError:
                logger.error("gemini_fallback_timeout", timeout_s=timeout_s)
                last_err = asyncio.TimeoutError(f"timeout after {timeout_s}s")
            except Exception as e2:
                logger.error("gemini_fallback_error", error=str(e2))
                last_err = e2

        # Friendly message when throttled or failed
        if last_err and self._is_rate_limit_error(last_err):
            return "現在リクエストが集中しているため回答できません。数十秒後に再度お試しください。"
        if isinstance(last_err, asyncio.TimeoutError):
            return "LLMの応答に時間がかかっています。しばらくしてから再度お試しください。"
        return "申し訳ございません。現在回答を生成できませんでした。しばらくしてからお試しください。"
