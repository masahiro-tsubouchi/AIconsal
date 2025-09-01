"""Chat service for handling conversation logic"""
import time
from typing import List, Optional
from uuid import uuid4
import structlog

from app.models.chat import ChatMessage, ChatHistory, SessionInfo
from app.services.langgraph_service import LangGraphService
from app.services.file_service import FileService
from app.repositories.chat_history import (
    ChatHistoryRepository,
    InMemoryChatHistoryRepository,
)

logger = structlog.get_logger()

# Shared in-memory repository instance to persist across requests
_DEFAULT_REPO = InMemoryChatHistoryRepository()


class ChatService:
    """Service for managing chat conversations"""
    
    def __init__(
        self,
        repository: Optional[ChatHistoryRepository] = None,
        langgraph_service: Optional[LangGraphService] = None,
        file_service: Optional[FileService] = None,
    ):
        self._repo: ChatHistoryRepository = repository or _DEFAULT_REPO
        self._langgraph_service = langgraph_service or LangGraphService()
        self._file_service = file_service or FileService()
    
    async def process_message(
        self, 
        message: str, 
        session_id: str, 
        file_ids: Optional[List[str]] = None
    ) -> str:
        """Process a user message and return AI response"""
        try:
            # Get or create session
            session = await self._repo.create_if_absent(session_id)
            
            # Add user message to history
            user_message = ChatMessage(
                session_id=session_id,
                content=message,
                role="user",
                file_ids=file_ids or []
            )
            await self.add_message_to_history(user_message)
            
            # Prepare context from file contents
            file_context = ""
            if file_ids:
                file_context = await self._get_file_context(file_ids)
            
            # Get conversation history for context
            conversation_history = await self._build_conversation_context(session_id)
            
            # Process with LangGraph
            response = await self._langgraph_service.process_manufacturing_query(
                query=message,
                context=conversation_history,
                file_context=file_context,
                thread_id=session_id,
            )
            
            logger.info(
                "message_processed",
                session_id=session_id,
                user_message_length=len(message),
                response_length=len(response),
                file_count=len(file_ids or [])
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "message_processing_error",
                session_id=session_id,
                error=str(e)
            )
            return "申し訳ございません。処理中にエラーが発生しました。もう一度お試しください。"
    
    async def add_message_to_history(self, message: ChatMessage) -> None:
        """Add a message to session history"""
        await self._repo.add_message(message)
    
    async def get_chat_history(self, session_id: str) -> Optional[ChatHistory]:
        """Get chat history for a session"""
        return await self._repo.get(session_id)
    
    async def _get_or_create_session(self, session_id: str) -> ChatHistory:
        """Get existing session or create new one (compat shim)."""
        return await self._repo.create_if_absent(session_id)
    
    async def _build_conversation_context(self, session_id: str, max_messages: int = 10) -> str:
        """Build conversation context from recent messages"""
        session = await self._repo.get(session_id)
        if not session:
            return ""
        
        # Get recent messages
        recent_messages = session.messages[-max_messages:] if session.messages else []
        
        context_lines = []
        for msg in recent_messages:
            role_prefix = "ユーザー" if msg.role == "user" else "アシスタント"
            context_lines.append(f"{role_prefix}: {msg.content}")
        
        return "\n".join(context_lines)
    
    async def _get_file_context(self, file_ids: List[str]) -> str:
        """Get context from uploaded files"""
        file_contexts = []
        
        for file_id in file_ids:
            file_info = await self._file_service.get_file_info(file_id)
            if file_info and file_info.content:
                file_contexts.append(f"ファイル '{file_info.original_filename}':\n{file_info.content}")
        
        return "\n\n".join(file_contexts)
    
    async def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old sessions via repository."""
        return await self._repo.cleanup(max_age_hours=max_age_hours)
