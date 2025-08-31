"""Python mentor agent

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
    あなたは製造業で使用するPythonの専門講師です。
    以下の質問に対して、実用的で理解しやすい回答を提供してください。

    質問: {user_query}
    {context_info}

    回答の際は以下の点を考慮してください：
    - 製造業の現場で活用できるPythonの使い方
    - 具体的なコード例を含める（可能な場合）
    - 初心者にも理解しやすい説明
    - データ分析や自動化への応用も含める
    - セキュリティや効率性も考慮する
    - 日本語で丁寧に回答する

    回答:
    """

    if getattr(llm, "is_configured", False):
        return await llm.generate(prompt)
    return "申し訳ございません。現在LLMプロバイダが設定されていないため、Python技術指導を提供できません。API設定を確認してください。"
