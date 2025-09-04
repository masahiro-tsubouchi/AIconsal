"""Agent type definitions and models.

Defines a standard async callable signature for agents and structured
input/output models for future extensibility.
"""
from __future__ import annotations

from typing import Awaitable, Callable, Optional
from pydantic import BaseModel

from app.services.llm.base import LLMProvider

# Async callable signature for agent entrypoints (legacy)
AgentFn = Callable[[Optional[LLMProvider], str, str, str], Awaitable[str]]


class AgentInput(BaseModel):
    user_query: str
    conversation_history: str = ""
    file_context: str = ""


class AgentOutput(BaseModel):
    content: str
    error: Optional[str] = None


# New callable signature for agent entrypoints using structured I/O
# Using string annotations to avoid forward-reference issues at runtime
AgentFnV2 = Callable[[Optional[LLMProvider], "AgentInput"], Awaitable["AgentOutput"]]


__all__ = [
    "AgentFn",
    "AgentInput",
    "AgentOutput",
    "AgentFnV2",
]
