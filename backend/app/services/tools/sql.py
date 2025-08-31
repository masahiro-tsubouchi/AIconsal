"""SQL tool placeholder implementation.

Provides `run(arg)` which returns a non-network, non-DB placeholder message.
"""
from __future__ import annotations


def run(arg: str) -> str:
    return (
        "[SQL Tool] まだ有効化されていません。\n"
        "将来的には安全な読み取り専用クエリ実行（パラメータ化・監査ログ・タイムアウト）を提供予定です。\n"
        f"受領クエリ候補: {arg}"
    )
