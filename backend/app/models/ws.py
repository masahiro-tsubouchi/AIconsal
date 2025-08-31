"""WebSocket message models for typed JSON protocol"""
from __future__ import annotations

from typing import Literal, Union
from pydantic import BaseModel, Field

from app.models.chat import ChatMessage


WSMessageType = Literal["status", "message", "error"]


class WSStatus(BaseModel):
    type: Literal["status"] = Field("status")
    session_id: str
    data: str


class WSError(BaseModel):
    type: Literal["error"] = Field("error")
    session_id: str
    data: str


class WSChatMessage(BaseModel):
    type: Literal["message"] = Field("message")
    session_id: str
    data: ChatMessage


WSMessage = Union[WSStatus, WSError, WSChatMessage]
