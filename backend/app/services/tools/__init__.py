"""Tools package

Re-exports common entry points so existing imports like
`from app.services.tools import detect_tool_request, execute_tool`
continue to work.
"""
from __future__ import annotations

from .detect import detect_tool_request
from .registry import execute_tool

__all__ = [
    "detect_tool_request",
    "execute_tool",
]
