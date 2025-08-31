"""Manufacturing advisor agent

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
    file_context: str = "",
) -> str:
    context_info = ""
    if conversation_history:
        context_info += f"\n\n過去の会話:\n{conversation_history}"
    if file_context:
        context_info += f"\n\n関連ファイル:\n{file_context}"

    prompt = f"""
    あなたは製造業の改善活動を専門とするAIコンサルタントです。
    以下の質問に対して、実践的で具体的なアドバイスを提供してください。

    質問: {user_query}
    {context_info}

    回答の際は以下の点を考慮してください：
    - 製造業の現場で実際に適用できる実践的な提案
    - 改善活動のステップを具体的に説明
    - 可能であれば数値目標や測定方法も含める
    - リスクや注意点も言及する
    - 日本語で丁寧に回答する

    回答:
    """

    if getattr(llm, "is_configured", False):
        return await llm.generate(prompt)
    return "申し訳ございません。現在LLMプロバイダが設定されていないため、製造業に関する詳細なアドバイスを提供できません。API設定を確認してください。"
