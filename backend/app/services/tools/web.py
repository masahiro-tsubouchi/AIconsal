"""Web search tool placeholder implementation.

Provides `run(arg)` which returns a placeholder message without network calls.
"""
from __future__ import annotations


def run(arg: str) -> str:
    return (
        "[Web Search Tool] まだ有効化されていません。\n"
        "将来的には検索プロバイダ統合＋要約（ソース出典付き）・レート制御・キャッシュを提供予定です。\n"
        f"受領検索語: {arg}"
    )
