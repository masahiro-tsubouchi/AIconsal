import pytest
from fastapi.testclient import TestClient
from typing import Optional, List

from app.main import app
from app.api.v1 import chat as chat_module
from app.models.chat import ChatHistory, ChatMessage


class FakeChatServiceBase:
    def __init__(self):
        pass

    async def process_message(
        self, message: str, session_id: str, file_ids: Optional[List[str]] = None, debug: Optional[bool] = False
    ) -> str:
        return "ASSISTANT_BODY"

    def get_last_debug_info(self) -> Optional[dict]:
        return None

    async def add_message_to_history(self, message):
        return None

    async def get_chat_history(self, session_id: str):
        return None


def test_send_message_no_debug_no_header(client: TestClient):
    class S(FakeChatServiceBase):
        pass

    app.dependency_overrides[chat_module.get_chat_service] = lambda: S()
    try:
        resp = client.post(
            "/api/v1/chat/",
            json={"message": "hello", "session_id": "sess-1", "debug": False},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("debug") is None
        content = data["message"]["content"]
        assert not content.startswith("[DEBUG]")
    finally:
        app.dependency_overrides.clear()


def test_send_message_debug_attach_fails_does_not_break(client: TestClient):
    class S(FakeChatServiceBase):
        def get_last_debug_info(self) -> Optional[dict]:
            # Missing required field display_header to force pydantic validation error
            return {"selected_agent": "x", "decision_trace": []}

    app.dependency_overrides[chat_module.get_chat_service] = lambda: S()
    try:
        resp = client.post(
            "/api/v1/chat/",
            json={"message": "hello", "session_id": "sess-2", "debug": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        # attach failed -> debug is None and no header prefix
        assert data.get("debug") is None
        assert data["message"]["content"].startswith("ASSISTANT_BODY")
    finally:
        app.dependency_overrides.clear()


def test_send_message_error_returns_500(client: TestClient):
    class S(FakeChatServiceBase):
        async def process_message(self, *args, **kwargs) -> str:
            raise RuntimeError("boom")

    app.dependency_overrides[chat_module.get_chat_service] = lambda: S()
    try:
        resp = client.post(
            "/api/v1/chat/",
            json={"message": "hello", "session_id": "sess-3", "debug": False},
        )
        assert resp.status_code == 500
        assert "チャット処理エラー" in resp.json().get("detail", "")
    finally:
        app.dependency_overrides.clear()


def test_get_history_empty_returns_empty_list(client: TestClient):
    class S(FakeChatServiceBase):
        async def get_chat_history(self, session_id: str):
            return None

    app.dependency_overrides[chat_module.get_chat_service] = lambda: S()
    try:
        resp = client.get("/api/v1/chat/history/sess-4")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "sess-4"
        assert data["messages"] == []
    finally:
        app.dependency_overrides.clear()


def test_get_history_error_returns_500(client: TestClient):
    class S(FakeChatServiceBase):
        async def get_chat_history(self, session_id: str):
            raise ValueError("oops")

    app.dependency_overrides[chat_module.get_chat_service] = lambda: S()
    try:
        resp = client.get("/api/v1/chat/history/sess-5")
        assert resp.status_code == 500
        assert "履歴取得エラー" in resp.json().get("detail", "")
    finally:
        app.dependency_overrides.clear()


def test_websocket_status_and_message(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    class WSService(FakeChatServiceBase):
        async def process_message(self, message: str, session_id: str, **kwargs) -> str:
            return "WS_RESPONSE"

    # Monkeypatch ChatService constructor used inside ws route
    monkeypatch.setattr(chat_module, "ChatService", WSService)

    with client.websocket_connect("/api/v1/chat/ws/ws-sess-1") as ws:
        # First status message
        msg = ws.receive_json()
        assert msg["type"] == "status"
        assert msg["session_id"] == "ws-sess-1"
        assert msg["data"] == "connected"

        # Send a message and expect a response message
        ws.send_text("hello")
        msg2 = ws.receive_json()
        assert msg2["type"] == "message"
        assert msg2["session_id"] == "ws-sess-1"
        assert msg2["data"]["content"] == "WS_RESPONSE"
        assert msg2["data"]["role"] == "assistant"

def test_auto_session_id_generated_when_missing(client: TestClient):
    class S(FakeChatServiceBase):
        pass

    # Override dependency to avoid real LangGraph execution
    app.dependency_overrides[chat_module.get_chat_service] = lambda: S()
    try:
        resp = client.post(
            "/api/v1/chat/",
            json={"message": "hello", "debug": False},  # no session_id provided
        )
        assert resp.status_code == 200
        data = resp.json()

        # session_id should be auto-generated and echoed on message
        sid = data.get("session_id")
        assert isinstance(sid, str) and len(sid) > 0
        assert data["message"]["session_id"] == sid
        assert data["message"]["role"] == "assistant"
        # Content should come from our fake service
        assert data["message"]["content"].startswith("ASSISTANT_BODY")
    finally:
        app.dependency_overrides.clear()


def test_websocket_error_message_on_exception(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    class WSServiceErr(FakeChatServiceBase):
        async def process_message(self, message: str, session_id: str, **kwargs) -> str:
            raise RuntimeError("ws-boom")

    monkeypatch.setattr(chat_module, "ChatService", WSServiceErr)

    with client.websocket_connect("/api/v1/chat/ws/ws-sess-2") as ws:
        # status
        _ = ws.receive_json()
        # provoke error
        ws.send_text("hello")
        err = ws.receive_json()
        assert err["type"] == "error"
        assert err["session_id"] == "ws-sess-2"
        assert "エラー:" in err["data"]


def test_get_history_with_limit_returns_last_n(client: TestClient):
    class S(FakeChatServiceBase):
        async def get_chat_history(self, session_id: str):
            msgs = [
                ChatMessage(id="m1", session_id=session_id, content="1", role="user"),
                ChatMessage(id="m2", session_id=session_id, content="2", role="assistant"),
                ChatMessage(id="m3", session_id=session_id, content="3", role="user"),
            ]
            return ChatHistory(session_id=session_id, messages=msgs)

    app.dependency_overrides[chat_module.get_chat_service] = lambda: S()
    try:
        sid = "sess-limit-1"
        resp = client.get(f"/api/v1/chat/history/{sid}?limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == sid
        assert len(data["messages"]) == 2
        # Should be last two messages m2, m3 in order
        assert [m["id"] for m in data["messages"]] == ["m2", "m3"]
    finally:
        app.dependency_overrides.clear()


def test_get_history_with_invalid_limit_returns_422(client: TestClient):
    class S(FakeChatServiceBase):
        async def get_chat_history(self, session_id: str):
            return ChatHistory(session_id=session_id, messages=[])

    app.dependency_overrides[chat_module.get_chat_service] = lambda: S()
    try:
        sid = "sess-limit-2"
        resp = client.get(f"/api/v1/chat/history/{sid}?limit=0")
        assert resp.status_code == 422  # FastAPI validation error for ge=1
    finally:
        app.dependency_overrides.clear()
