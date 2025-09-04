"""General responder agent

Provides `run()` which generates a response using the provided LLM provider.
Falls back to a safe message if no LLM is configured.
"""
from __future__ import annotations

from typing import Optional
import structlog

from app.services.llm.base import LLMProvider
from app.services.agents.types import AgentInput, AgentOutput

logger = structlog.get_logger()


async def run_v2(llm: Optional[LLMProvider], inp: AgentInput) -> AgentOutput:
    """New I/F: AgentInput -> AgentOutput.

    旧I/F互換のためのラッパーは `run()` に実装。こちらが実体。
    """
    log = logger.bind(agent="general", agent_io_version="v2")

    context_info = ""
    if inp.conversation_history:
        context_info += f"\n\n過去の会話:\n{inp.conversation_history}"
    if inp.file_context:
        context_info += f"\n\n関連ファイル:\n{inp.file_context}"

    prompt = f"""
    以下の質問に対して、親切で丁寧な回答を提供してください：

    質問: {inp.user_query}
    {context_info}

    製造業とPython技術指導を専門とするAIアシスタントとして、
    可能であれば専門分野との関連性も含めて回答してください。
    日本語で回答してください。

    回答:
    """

    try:
        log.info("agent_started")
        if getattr(llm, "is_configured", False):
            content = await llm.generate(prompt)
            log.info("agent_completed")
            return AgentOutput(content=content)
        fallback = (
            f"ご質問ありがとうございます。「{inp.user_query}」についてですが、現在LLMプロバイダが設定されていないため、詳細な回答を提供できません。"
            "製造業の改善活動やPython技術についてのご質問でしたら、API設定後により具体的なアドバイスを提供できます。"
        )
        log.info("agent_completed", fallback=True)
        return AgentOutput(content=fallback)
    except Exception as e:  # noqa: BLE001
        log.error("agent_error", error=str(e))
        return AgentOutput(content="回答の生成中にエラーが発生しました。", error=str(e))
 # V2-only migration: legacy run() wrapper removed. Use run_v2().
