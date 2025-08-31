"""General responder agent

Provides `run()` which generates a response using the provided LLM provider.
Falls back to a safe message if no LLM is configured.
"""
from __future__ import annotations

from typing import Optional

from app.services.llm.base import LLMProvider


async def run(
    llm: Optional[LLMProvider],
    user_query: str,
    conversation_history: str = "",
) -> str:
    context_info = ""
    if conversation_history:
        context_info += f"\n\n過去の会話:\n{conversation_history}"

    prompt = f"""
    以下の質問に対して、親切で丁寧な回答を提供してください：

    質問: {user_query}
    {context_info}

    製造業とPython技術指導を専門とするAIアシスタントとして、
    可能であれば専門分野との関連性も含めて回答してください。
    日本語で回答してください。

    回答:
    """

    if getattr(llm, "is_configured", False):
        return await llm.generate(prompt)
    return (
        f"ご質問ありがとうございます。「{user_query}」についてですが、現在LLMプロバイダが設定されていないため、詳細な回答を提供できません。"
        "製造業の改善活動やPython技術についてのご質問でしたら、API設定後により具体的なアドバイスを提供できます。"
    )
