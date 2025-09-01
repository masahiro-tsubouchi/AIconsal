"""Agent registry.

Provides a central mapping from logical agent names to their async `run` callables.
This enables easy addition/replacement of agents without changing callers.
"""
from __future__ import annotations

from typing import Dict, Optional

from .types import AgentFn
from . import manufacturing_advisor, python_mentor, general_responder


_REGISTRY: Dict[str, AgentFn] = {
    # Logical names align with routing keys used in LangGraphService
    "manufacturing": manufacturing_advisor.run,
    "python": python_mentor.run,
    "general": general_responder.run,
}


def get_agent(name: str) -> Optional[AgentFn]:
    """Return the registered agent function by name, if any."""
    return _REGISTRY.get(name)


__all__ = ["get_agent"]
