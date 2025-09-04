"""Manufacturing advisor agent

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
    """New I/F: AgentInput -> AgentOutput for Manufacturing advisor."""
    log = logger.bind(agent="manufacturing", agent_io_version="v2")

    context_info = ""
    if inp.conversation_history:
        context_info += f"\n\n過去の会話:\n{inp.conversation_history}"
    if inp.file_context:
        context_info += f"\n\n関連ファイル:\n{inp.file_context}"

    prompt = f"""
    あなたは製造業の改善活動を専門とするAIコンサルタントです。
    以下の質問に対して、実践的で具体的なアドバイスを提供してください。

    質問: {inp.user_query}
    {context_info}

    回答の際は以下の点を考慮してください：
    - 製造業の現場で実際に適用できる実践的な提案
    - 改善活動のステップを具体的に説明
    - 可能であれば数値目標や測定方法も含める
    - リスクや注意点も言及する
    - 日本語で丁寧に回答する

    回答:
    """

    try:
        log.info("agent_started")
        if getattr(llm, "is_configured", False):
            content = await llm.generate(prompt)
            log.info("agent_completed")
            return AgentOutput(content=content)
        fallback = "申し訳ございません。現在LLMプロバイダが設定されていないため、製造業に関する詳細なアドバイスを提供できません。API設定を確認してください。"
        log.info("agent_completed", fallback=True)
        return AgentOutput(content=fallback)
    except Exception as e:  # noqa: BLE001
        log.error("agent_error", error=str(e))
        return AgentOutput(content="回答の生成中にエラーが発生しました。", error=str(e))


async def run(
    llm: Optional[LLMProvider],
    user_query: str,
    conversation_history: str = "",
    file_context: str = "",
) -> str:
    """Legacy wrapper: call run_v2 and return content str."""
    # Deprecation notice: prefer run_v2(AgentInput)->AgentOutput
    logger.warning("agent_legacy_run_deprecated", agent="manufacturing")
    out = await run_v2(
        llm,
        AgentInput(
            user_query=user_query,
            conversation_history=conversation_history,
            file_context=file_context,
        ),
    )
    return out.content
