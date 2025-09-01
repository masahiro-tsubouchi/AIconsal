"""Agent type definitions and models.

Defines a standard async callable signature for agents and structured
input/output models for future extensibility.
"""
from __future__ import annotations

from typing import Awaitable, Callable, Optional
from pydantic import BaseModel

from app.services.llm.base import LLMProvider

# Async callable signature for agent entrypoints
AgentFn = Callable[[Optional[LLMProvider], str, str, str], Awaitable[str]]


class AgentInput(BaseModel):
    user_query: str
    conversation_history: str = ""
    file_context: str = ""


class AgentOutput(BaseModel):
    content: str
    error: Optional[str] = None


__all__ = [
    "AgentFn",
    "AgentInput",
    "AgentOutput",
]
