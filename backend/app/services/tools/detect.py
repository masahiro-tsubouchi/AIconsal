"""Tool detection utilities.

Parses explicit user prefixes to route to tools safely.
"""
from __future__ import annotations

from typing import Optional, Tuple

# Supported tool prefixes -> canonical tool name
_PREFIX_MAP = {
    "sql": "sql",
    "web": "web",
    "search": "web",  # alias for web search
    "tool": None,  # generic prefix; requires explicit tool name after it
}


def detect_tool_request(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Detect explicit tool prefix in the user's text.

    Formats supported:
    - "sql: SELECT * FROM table"
    - "web: query terms"
    - "search: query terms" (alias of web)
    - "tool:sql: <arg>" (generic form)

    Returns (tool_name, argument) or (None, None) if not detected.
    """
    if not text:
        return (None, None)

    raw = text.strip()

    # Generic form: tool:<name>:<arg>
    if raw.lower().startswith("tool:"):
        rest = raw[5:].strip()
        # Expect something like "sql: ..." or "web: ..."
        for prefix in ("sql:", "web:", "search:"):
            if rest.lower().startswith(prefix):
                tool = _PREFIX_MAP[prefix[:-1]]  # remove trailing ':'
                arg = rest[len(prefix):].strip()
                return (tool, arg)
        # If just "tool:" with no known subtool, treat as unknown
        return (None, None)

    # Direct prefixes
    for p in ("sql:", "web:", "search:"):
        if raw.lower().startswith(p):
            tool = _PREFIX_MAP[p[:-1]]
            arg = raw[len(p):].strip()
            return (tool, arg)

    return (None, None)
