import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.main import app
from app.api.v1 import chat as chat_module
from app.services.chat_service import ChatService
from app.repositories.chat_history import InMemoryChatHistoryRepository
from app.models.chat import ChatHistory, ChatMessage
from app.services.file_service import FileService


@pytest.mark.asyncio
async def test_chat_service_fallback_on_langgraph_error():
    class LGErr:
        async def process_query(self, *args, **kwargs):
            raise RuntimeError("lg-fail")

        def get_last_debug_info(self):
            return None

    svc = ChatService(
        repository=InMemoryChatHistoryRepository(),
        langgraph_service=LGErr(),
        file_service=FileService(),
    )
    # When LG raises, ChatService should return fallback apology message
    msg = await svc.process_message("hello", session_id="sess-fallback")
    assert "エラーが発生" in msg or "もう一度お試しください" in msg


def test_chat_api_debug_success_attaches_header_and_payload(client: TestClient):
    class S:
        async def process_message(self, *args, **kwargs):
            return "ASSIST"

        def get_last_debug_info(self):
            return {
                "display_header": "Trace ok",
                "selected_agent": "general_responder",
                "decision_trace": [],
                "thread_id": "t-1",
            }

        async def add_message_to_history(self, message):
            return None

    app.dependency_overrides[chat_module.get_chat_service] = lambda: S()
    try:
        resp = client.post(
            "/api/v1/chat/",
            json={"message": "hi", "session_id": "sess-dbg", "debug": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["debug"]["display_header"] == "Trace ok"
        assert data["message"]["content"].startswith("[DEBUG] Trace ok\n\nASSIST")
    finally:
        app.dependency_overrides.clear()


def test_chat_api_get_history_returns_existing_history(client: TestClient):
    class S:
        async def get_chat_history(self, session_id: str):
            return ChatHistory(
                session_id=session_id,
                messages=[
                    ChatMessage(session_id=session_id, content="hi", role="user")
                ],
            )

    app.dependency_overrides[chat_module.get_chat_service] = lambda: S()
    try:
        resp = client.get("/api/v1/chat/history/sess-have")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "sess-have"
        assert len(data["messages"]) == 1
    finally:
        app.dependency_overrides.clear()


def test_chat_api_get_history_http_exception_passthrough(client: TestClient):
    class S:
        async def get_chat_history(self, session_id: str):
            raise HTTPException(status_code=404, detail="nope")

    app.dependency_overrides[chat_module.get_chat_service] = lambda: S()
    try:
        resp = client.get("/api/v1/chat/history/sess-404")
        assert resp.status_code == 404
        assert resp.json().get("detail") == "nope"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_chat_repository_save_and_cleanup_removes_old_sessions():
    repo = InMemoryChatHistoryRepository()
    # Old session
    old = ChatHistory(session_id="old", messages=[])
    old.last_active = datetime.now() - timedelta(hours=5)
    # New session
    new = ChatHistory(session_id="new", messages=[])

    # Save both
    await repo.save(old)
    await repo.save(new)

    removed = await repo.cleanup(max_age_hours=1)
    assert removed >= 1
    still_old = await repo.get("old")
    still_new = await repo.get("new")
    assert still_old is None
    assert still_new is not None


@pytest.mark.asyncio
async def test_file_service_extract_text_unsupported_type_returns_message(tmp_path):
    from app.services.file_service import FileService

    svc = FileService()
    bogus = tmp_path / "a.xyz"
    bogus.write_text("x", encoding="utf-8")
    text = await svc._extract_text_from_file(str(bogus), ".xyz")
    assert "読み取れません" in text or "Unsupported file type" in text
