"""Chat service for handling conversation logic"""
import time
from typing import Dict, List, Optional
from uuid import uuid4
import structlog

from app.models.chat import ChatMessage, ChatHistory, SessionInfo
from app.services.langgraph_service import LangGraphService
from app.services.file_service import FileService

logger = structlog.get_logger()


class ChatService:
    """Service for managing chat conversations"""
    
    def __init__(self):
        self._sessions: Dict[str, ChatHistory] = {}
        self._langgraph_service = LangGraphService()
        self._file_service = FileService()
    
    async def process_message(
        self, 
        message: str, 
        session_id: str, 
        file_ids: Optional[List[str]] = None
    ) -> str:
        """Process a user message and return AI response"""
        try:
            # Get or create session
            session = await self._get_or_create_session(session_id)
            
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
                file_context=file_context
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
        session = await self._get_or_create_session(message.session_id)
        session.messages.append(message)
        session.last_active = message.timestamp
    
    async def get_chat_history(self, session_id: str) -> Optional[ChatHistory]:
        """Get chat history for a session"""
        return self._sessions.get(session_id)
    
    async def _get_or_create_session(self, session_id: str) -> ChatHistory:
        """Get existing session or create new one"""
        if session_id not in self._sessions:
            self._sessions[session_id] = ChatHistory(
                session_id=session_id,
                messages=[],
            )
            logger.info("new_session_created", session_id=session_id)
        
        return self._sessions[session_id]
    
    async def _build_conversation_context(self, session_id: str, max_messages: int = 10) -> str:
        """Build conversation context from recent messages"""
        session = self._sessions.get(session_id)
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
        """Clean up old sessions"""
        import datetime
        
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=max_age_hours)
        sessions_to_remove = []
        
        for session_id, session in self._sessions.items():
            if session.last_active < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self._sessions[session_id]
        
        if sessions_to_remove:
            logger.info(
                "sessions_cleaned_up",
                cleaned_count=len(sessions_to_remove),
                remaining_count=len(self._sessions)
            )
        
        return len(sessions_to_remove)
