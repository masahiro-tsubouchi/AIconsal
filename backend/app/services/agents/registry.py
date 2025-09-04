"""Agent registry.

Provides a central mapping from logical agent names to their async `run` callables.
This enables easy addition/replacement of agents without changing callers.
"""
from __future__ import annotations

from typing import Dict, Optional

from .types import AgentFnV2
from . import manufacturing_advisor, python_mentor, general_responder


# V2-only: legacy registry removed. All agents must implement run_v2.


# Optional v2 registry for structured I/O (AgentInput/AgentOutput)
_REGISTRY_V2: Dict[str, AgentFnV2] = {
    # Adopt v2 incrementally starting with general agent
    "general": general_responder.run_v2,
    "python": python_mentor.run_v2,
    "manufacturing": manufacturing_advisor.run_v2,
}


def get_agent_v2(name: str) -> Optional[AgentFnV2]:
    """Return the v2 (structured I/O) agent function by name, if any.

    During staged rollout, not all agents will be present here.
    """
    return _REGISTRY_V2.get(name)


__all__ = ["get_agent_v2"]
