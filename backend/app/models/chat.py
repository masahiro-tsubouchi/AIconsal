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
    # Debug/Trace toggle (optional)
    debug: Optional[bool] = Field(False, description="デバッグ/トレース情報を返すかどうか")


class DebugTraceEvent(BaseModel):
    """Single decision/trace event for observability."""
    type: str = Field(..., description="イベント種別 (agent_selected, tool_invoked など)")
    name: Optional[str] = Field(None, description="エージェント/ツール名")
    reason: Optional[str] = Field(None, description="判断理由/根拠")
    ts: Optional[int] = Field(None, description="イベント時刻 (epoch ms)")
    tool_input: Optional[str] = Field(None, description="ツール入力（必要に応じて短縮）")
    took_ms: Optional[int] = Field(None, description="処理時間 (ms)")
    error: Optional[str] = Field(None, description="エラー情報（あれば）")


class DebugInfo(BaseModel):
    """Debug/Trace information returned when debug=true."""
    display_header: str = Field(..., description="UI先頭に表示する要約ヘッダ")
    selected_agent: Optional[str] = Field(None, description="選択されたエージェント")
    selected_tool: Optional[str] = Field(None, description="選択/実行されたツール")
    decision_trace: List[DebugTraceEvent] = Field(default_factory=list, description="判断トレース")
    thread_id: Optional[str] = Field(None, description="相関ID（スレッドID）")


class ChatResponse(BaseModel):
    """Chat response model"""
    message: ChatMessage = Field(..., description="応答メッセージ")
    session_id: str = Field(..., description="セッションID")
    processing_time: float = Field(..., description="処理時間（秒）")
    # Optional debug/trace payload
    debug: Optional[DebugInfo] = Field(None, description="デバッグ/トレース情報")


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
