"""Tool types and result models."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    tool: str = Field(..., description="Tool name")
    input: str = Field(..., description="Input argument")
    output: str = Field(..., description="Rendered tool output (human-readable)")
    took_ms: Optional[int] = Field(None, description="Elapsed time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if failed")


__all__ = ["ToolResult"]
