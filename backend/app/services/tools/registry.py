"""Tool registry and dispatcher.

Provides a single `execute_tool(tool, arg)` entry point.
"""
from __future__ import annotations

from typing import Callable, Optional

from . import sql, web

# Map canonical tool names to their handlers
TOOL_RUNNERS: dict[str, Callable[[str], str]] = {
    "sql": sql.run,
    "web": web.run,
}


def execute_tool(tool: Optional[str], arg: str) -> str:
    """Execute the specified tool in a safe, placeholder manner.

    This is a stub that does NOT hit databases or the network.
    It returns an instructional message suitable for early scaffolding.
    """
    if not tool:
        return "不明なツールが指定されました。サポートされている例: sql:, web: / search:"

    runner = TOOL_RUNNERS.get(tool.lower())
    if runner:
        return runner(arg)

    return f"[Tool:{tool}] まだ有効化されていません。入力: {arg}"
