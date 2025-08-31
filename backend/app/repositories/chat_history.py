"""Chat history repository abstractions and in-memory implementation"""
from __future__ import annotations

from typing import Dict, Optional, Protocol
from datetime import datetime, timedelta
import structlog

from app.models.chat import ChatMessage, ChatHistory


logger = structlog.get_logger()


class ChatHistoryRepository(Protocol):
    async def get(self, session_id: str) -> Optional[ChatHistory]:
        ...

    async def create_if_absent(self, session_id: str) -> ChatHistory:
        ...

    async def add_message(self, message: ChatMessage) -> None:
        ...

    async def save(self, history: ChatHistory) -> None:
        ...

    async def cleanup(self, max_age_hours: int = 24) -> int:
        ...


class InMemoryChatHistoryRepository(ChatHistoryRepository):
    """Simple in-memory repository for chat histories."""

    def __init__(self) -> None:
        self._store: Dict[str, ChatHistory] = {}

    async def get(self, session_id: str) -> Optional[ChatHistory]:
        return self._store.get(session_id)

    async def create_if_absent(self, session_id: str) -> ChatHistory:
        history = self._store.get(session_id)
        if not history:
            history = ChatHistory(session_id=session_id, messages=[])
            self._store[session_id] = history
            logger.info("repo_new_session_created", session_id=session_id)
        return history

    async def add_message(self, message: ChatMessage) -> None:
        history = await self.create_if_absent(message.session_id)
        history.messages.append(message)
        history.last_active = message.timestamp

    async def save(self, history: ChatHistory) -> None:
        self._store[history.session_id] = history

    async def cleanup(self, max_age_hours: int = 24) -> int:
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = [sid for sid, h in self._store.items() if h.last_active < cutoff]
        for sid in to_remove:
            del self._store[sid]
        if to_remove:
            logger.info(
                "repo_sessions_cleaned_up",
                cleaned_count=len(to_remove),
                remaining_count=len(self._store),
            )
        return len(to_remove)
