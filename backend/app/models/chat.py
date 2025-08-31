"""Chat data models for Manufacturing AI Assistant"""
from datetime import datetime
from typing import List, Literal, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Individual chat message model"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="メッセージID")
    session_id: str = Field(..., description="セッションID")
    content: str = Field(..., min_length=1, max_length=4000, description="メッセージ内容")
    role: Literal["user", "assistant"] = Field(..., description="送信者ロール")
    timestamp: datetime = Field(default_factory=datetime.now, description="送信時刻")
    file_ids: List[str] = Field(default_factory=list, description="添付ファイルID一覧")
    processing_time: Optional[float] = Field(None, description="処理時間（秒）")


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., min_length=1, max_length=4000, description="送信メッセージ")
    session_id: Optional[str] = Field(None, description="セッションID")
    file_ids: List[str] = Field(default_factory=list, description="添付ファイルID一覧")


class ChatResponse(BaseModel):
    """Chat response model"""
    message: ChatMessage = Field(..., description="応答メッセージ")
    session_id: str = Field(..., description="セッションID")
    processing_time: float = Field(..., description="処理時間（秒）")


class ChatHistory(BaseModel):
    """Chat history model"""
    session_id: str = Field(..., description="セッションID")
    messages: List[ChatMessage] = Field(default_factory=list, description="メッセージ履歴")
    created_at: datetime = Field(default_factory=datetime.now, description="セッション開始時刻")
    last_active: datetime = Field(default_factory=datetime.now, description="最終活動時刻")


class SessionInfo(BaseModel):
    """Session information model"""
    session_id: str = Field(..., description="セッションID")
    user_id: Optional[str] = Field(None, description="ユーザーID")
    created_at: datetime = Field(default_factory=datetime.now, description="セッション開始時刻")
    last_active: datetime = Field(default_factory=datetime.now, description="最終活動時刻")
    message_count: int = Field(0, description="メッセージ数")
