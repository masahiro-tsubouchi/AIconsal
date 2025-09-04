"""
統合テスト - Debug/Traceモード
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app


class TestAPIDebugMode:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_chat_endpoint_returns_debug_payload_and_header(self, client):
        # Arrange
        session_id = "test-debug-session"
        chat_request = {
            "message": "python: print(\"Hello\") を教えて",
            "session_id": session_id,
            "debug": True,
        }

        fake_debug = {
            "display_header": "Agent: python_mentor / Tool: none / 根拠: キーワード検出",
            "selected_agent": "python_mentor",
            "selected_tool": None,
            "decision_trace": [
                {"type": "agent_selected", "name": "python_mentor", "reason": "キーワード検出", "ts": 1},
            ],
            "thread_id": session_id,
        }

        with patch(
            "app.services.langgraph_service.LangGraphService.process_manufacturing_query",
        ) as mock_process, patch(
            "app.services.chat_service.ChatService.get_last_debug_info",
        ) as mock_get_debug:
            mock_process.return_value = "OK"
            mock_get_debug.return_value = fake_debug

            # Act
            resp = client.post("/api/v1/chat/", json=chat_request)

        # Assert
        assert resp.status_code == 200
        data = resp.json()
        assert "debug" in data
        assert data["debug"]["display_header"].startswith("Agent: ")
        assert data["message"]["content"].startswith("[DEBUG] ")
