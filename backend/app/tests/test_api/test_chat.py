"""Tests for chat API endpoints"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


class TestChatAPI:
    """Test cases for chat API endpoints"""
    
    @pytest.mark.unit
    def test_send_message_success(self, client: TestClient, sample_chat_request):
        """Test successful chat message sending"""
        # Act
        response = client.post("/api/v1/chat/", json=sample_chat_request)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "session_id" in data
        assert "processing_time" in data
        assert data["session_id"] == sample_chat_request["session_id"]
    
    @pytest.mark.unit
    def test_send_message_without_session_id(self, client: TestClient):
        """Test sending message without session_id generates new session"""
        # Arrange
        request_data = {"message": "こんにちは"}
        
        # Act
        response = client.post("/api/v1/chat/", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] is not None
        assert len(data["session_id"]) > 0
    
    @pytest.mark.unit
    def test_send_empty_message_fails(self, client: TestClient):
        """Test sending empty message returns validation error"""
        # Arrange
        request_data = {"message": "", "session_id": "test-session"}
        
        # Act
        response = client.post("/api/v1/chat/", json=request_data)
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.unit
    def test_send_message_too_long_fails(self, client: TestClient):
        """Test sending overly long message returns validation error"""
        # Arrange
        long_message = "a" * 5000  # Exceeds 4000 char limit
        request_data = {"message": long_message, "session_id": "test-session"}
        
        # Act
        response = client.post("/api/v1/chat/", json=request_data)
        
        # Assert
        assert response.status_code == 422
    
    @pytest.mark.unit
    def test_send_message_with_files(self, client: TestClient):
        """Test sending message with file IDs"""
        # Arrange
        request_data = {
            "message": "このファイルについて教えてください",
            "session_id": "test-session",
            "file_ids": ["file-123", "file-456"]
        }
        
        # Act
        response = client.post("/api/v1/chat/", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    @pytest.mark.integration
    def test_get_chat_history_success(self, client: TestClient, test_session_id):
        """Test retrieving chat history for existing session"""
        # Arrange - First send a message to create history
        request_data = {"message": "テストメッセージ", "session_id": test_session_id}
        client.post("/api/v1/chat/", json=request_data)
        
        # Act
        response = client.get(f"/api/v1/chat/history/{test_session_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "messages" in data
        assert data["session_id"] == test_session_id
        assert len(data["messages"]) >= 1
    
    @pytest.mark.unit
    def test_get_chat_history_nonexistent_session(self, client: TestClient):
        """Test retrieving history for non-existent session returns 404"""
        # Act
        response = client.get("/api/v1/chat/history/nonexistent-session")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.integration
    async def test_websocket_chat_connection(self, async_client: AsyncClient):
        """Test WebSocket chat connection"""
        # This test would require WebSocket testing setup
        # For now, we'll mark it as a placeholder
        pass
    
    @pytest.mark.unit
    def test_chat_message_structure(self, client: TestClient, sample_chat_request):
        """Test chat message response structure"""
        # Act
        response = client.post("/api/v1/chat/", json=sample_chat_request)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Verify message structure
        message = data["message"]
        assert "id" in message
        assert "session_id" in message
        assert "content" in message
        assert "role" in message
        assert "timestamp" in message
        assert message["role"] == "assistant"
        assert len(message["content"]) > 0
    
    @pytest.mark.integration
    def test_manufacturing_query_processing(self, client: TestClient, sample_manufacturing_query):
        """Test manufacturing-specific query processing"""
        # Arrange
        request_data = {
            "message": sample_manufacturing_query,
            "session_id": "manufacturing-test-session"
        }
        
        # Act
        response = client.post("/api/v1/chat/", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Response should contain manufacturing-related content
        response_content = data["message"]["content"].lower()
        assert any(keyword in response_content for keyword in ["製造", "改善", "効率", "生産"])
    
    @pytest.mark.integration
    def test_python_query_processing(self, client: TestClient, sample_python_query):
        """Test Python-specific query processing"""
        # Arrange
        request_data = {
            "message": sample_python_query,
            "session_id": "python-test-session"
        }
        
        # Act
        response = client.post("/api/v1/chat/", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Response should contain Python-related content
        response_content = data["message"]["content"].lower()
        assert any(keyword in response_content for keyword in ["python", "データ", "分析", "コード"])
