"""Tool registry and dispatcher.

Provides a single `execute_tool(tool, arg)` entry point.
"""
from __future__ import annotations

from typing import Callable, Optional
import asyncio
import inspect
import time

from .types import ToolResult

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


async def async_execute_tool(tool: Optional[str], arg: str, timeout_s: float = 5.0) -> ToolResult:
    """Async tool execution with timeout and structured result.

    - Preserves behavior of `execute_tool` but returns `ToolResult`.
    - Wraps sync runners using `asyncio.to_thread`.
    - Enforces `timeout_s` via `asyncio.wait_for`.
    """
    start = time.perf_counter()
    name = (tool or "").lower()

    if not name:
        msg = "不明なツールが指定されました。サポートされている例: sql:, web: / search:"
        took = int((time.perf_counter() - start) * 1000)
        return ToolResult(tool="", input=arg, output=msg, error="unknown_tool", took_ms=took)

    runner = TOOL_RUNNERS.get(name)
    if not runner:
        msg = f"[Tool:{tool}] まだ有効化されていません。入力: {arg}"
        took = int((time.perf_counter() - start) * 1000)
        return ToolResult(tool=name, input=arg, output=msg, error="unsupported_tool", took_ms=took)

    try:
        if inspect.iscoroutinefunction(runner):
            coro = runner(arg)  # type: ignore[arg-type]
        else:
            coro = asyncio.to_thread(runner, arg)

        output: str = await asyncio.wait_for(coro, timeout=timeout_s)
        took = int((time.perf_counter() - start) * 1000)
        return ToolResult(tool=name, input=arg, output=output, took_ms=took)
    except asyncio.TimeoutError:
        took = int((time.perf_counter() - start) * 1000)
        return ToolResult(tool=name, input=arg, output="", error=f"timeout after {timeout_s}s", took_ms=took)
    except Exception as e:  # noqa: BLE001
        took = int((time.perf_counter() - start) * 1000)
        return ToolResult(tool=name, input=arg, output="", error=str(e), took_ms=took)
