"""Tests for ChatService"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.services.chat_service import ChatService
from app.models.chat import ChatMessage


class TestChatService:
    """Test cases for ChatService"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_message_success(self, chat_service: ChatService, test_session_id):
        """Test successful message processing"""
        # Arrange
        message = "製造業の改善活動について教えてください"
        
        with patch.object(chat_service._langgraph_service, 'process_manufacturing_query', 
                         return_value="改善活動についてご説明します...") as mock_process:
            
            # Act
            response = await chat_service.process_message(message, test_session_id)
            
            # Assert
            assert isinstance(response, str)
            assert len(response) > 0
            mock_process.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_message_with_files(self, chat_service: ChatService, test_session_id):
        """Test message processing with file context"""
        # Arrange
        message = "このファイルについて分析してください"
        file_ids = ["file-123"]
        
        with patch.object(chat_service._file_service, 'get_file_info', 
                         return_value=Mock(original_filename="test.txt", content="テストファイル内容")) as mock_file:
            with patch.object(chat_service._langgraph_service, 'process_manufacturing_query', 
                             return_value="ファイル分析結果です") as mock_process:
                
                # Act
                response = await chat_service.process_message(message, test_session_id, file_ids)
                
                # Assert
                assert isinstance(response, str)
                mock_file.assert_called_once_with("file-123")
                mock_process.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_message_to_history(self, chat_service: ChatService):
        """Test adding message to session history"""
        # Arrange
        session_id = "test-session"
        message = ChatMessage(
            session_id=session_id,
            content="テストメッセージ",
            role="user"
        )
        
        # Act
        await chat_service.add_message_to_history(message)
        
        # Assert
        history = await chat_service.get_chat_history(session_id)
        assert history is not None
        assert len(history.messages) == 1
        assert history.messages[0].content == "テストメッセージ"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_chat_history_existing_session(self, chat_service: ChatService, test_session_id):
        """Test getting history for existing session"""
        # Arrange - Add some messages
        message1 = ChatMessage(session_id=test_session_id, content="メッセージ1", role="user")
        message2 = ChatMessage(session_id=test_session_id, content="メッセージ2", role="assistant")
        
        await chat_service.add_message_to_history(message1)
        await chat_service.add_message_to_history(message2)
        
        # Act
        history = await chat_service.get_chat_history(test_session_id)
        
        # Assert
        assert history is not None
        assert history.session_id == test_session_id
        assert len(history.messages) == 2
        assert history.messages[0].content == "メッセージ1"
        assert history.messages[1].content == "メッセージ2"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_chat_history_nonexistent_session(self, chat_service: ChatService):
        """Test getting history for non-existent session"""
        # Act
        history = await chat_service.get_chat_history("nonexistent-session")
        
        # Assert
        assert history is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_build_conversation_context(self, chat_service: ChatService, test_session_id):
        """Test building conversation context from history"""
        # Arrange - Add messages to create history
        messages = [
            ChatMessage(session_id=test_session_id, content="こんにちは", role="user"),
            ChatMessage(session_id=test_session_id, content="こんにちは！", role="assistant"),
            ChatMessage(session_id=test_session_id, content="製造業について", role="user"),
        ]
        
        for msg in messages:
            await chat_service.add_message_to_history(msg)
        
        # Act
        context = await chat_service._build_conversation_context(test_session_id)
        
        # Assert
        assert "ユーザー: こんにちは" in context
        assert "アシスタント: こんにちは！" in context
        assert "ユーザー: 製造業について" in context
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_file_context(self, chat_service: ChatService):
        """Test getting context from files"""
        # Arrange
        file_ids = ["file-123", "file-456"]
        
        mock_file1 = Mock(original_filename="doc1.txt", content="ファイル1の内容")
        mock_file2 = Mock(original_filename="doc2.txt", content="ファイル2の内容")
        
        with patch.object(chat_service._file_service, 'get_file_info', 
                         side_effect=[mock_file1, mock_file2]) as mock_get_file:
            
            # Act
            context = await chat_service._get_file_context(file_ids)
            
            # Assert
            assert "ファイル 'doc1.txt'" in context
            assert "ファイル1の内容" in context
            assert "ファイル 'doc2.txt'" in context
            assert "ファイル2の内容" in context
            assert mock_get_file.call_count == 2
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cleanup_old_sessions(self, chat_service: ChatService):
        """Test cleaning up old sessions"""
        # Arrange - Create sessions with different ages
        import datetime
        from unittest.mock import patch
        
        old_time = datetime.datetime.now() - datetime.timedelta(hours=25)
        recent_time = datetime.datetime.now() - datetime.timedelta(hours=1)
        
        # Create test sessions
        await chat_service._get_or_create_session("old-session")
        await chat_service._get_or_create_session("recent-session")
        
        # Manually set timestamps
        chat_service._sessions["old-session"].last_active = old_time
        chat_service._sessions["recent-session"].last_active = recent_time
        
        # Act
        cleaned_count = await chat_service.cleanup_old_sessions(max_age_hours=24)
        
        # Assert
        assert cleaned_count == 1
        assert "old-session" not in chat_service._sessions
        assert "recent-session" in chat_service._sessions
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_process_message_error_handling(self, chat_service: ChatService, test_session_id):
        """Test error handling during message processing"""
        # Arrange
        message = "テストメッセージ"
        
        with patch.object(chat_service._langgraph_service, 'process_manufacturing_query', 
                         side_effect=Exception("テストエラー")):
            
            # Act
            response = await chat_service.process_message(message, test_session_id)
            
            # Assert
            assert "申し訳ございません" in response
            assert "エラーが発生しました" in response
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_session_creation_on_first_message(self, chat_service: ChatService):
        """Test session creation when processing first message"""
        # Arrange
        new_session_id = "brand-new-session"
        message = "初回メッセージ"
        
        with patch.object(chat_service._langgraph_service, 'process_manufacturing_query', 
                         return_value="応答メッセージ"):
            
            # Act
            response = await chat_service.process_message(message, new_session_id)
            
            # Assert
            assert isinstance(response, str)
            history = await chat_service.get_chat_history(new_session_id)
            assert history is not None
            assert history.session_id == new_session_id
