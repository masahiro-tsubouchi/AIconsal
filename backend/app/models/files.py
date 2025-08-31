"""File processing data models"""
from datetime import datetime
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class UploadedFile(BaseModel):
    """Uploaded file model"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="ファイルID")
    filename: str = Field(..., description="ファイル名")
    original_filename: str = Field(..., description="元のファイル名")
    file_type: str = Field(..., description="ファイル形式")
    file_size: int = Field(..., description="ファイルサイズ（バイト）")
    content: Optional[str] = Field(None, description="抽出されたテキスト内容")
    upload_time: datetime = Field(default_factory=datetime.now, description="アップロード時刻")
    session_id: str = Field(..., description="関連セッションID")


class FileUploadRequest(BaseModel):
    """File upload request model"""
    session_id: Optional[str] = Field(None, description="セッションID")


class FileUploadResponse(BaseModel):
    """File upload response model"""
    file: UploadedFile = Field(..., description="アップロードされたファイル情報")
    message: str = Field(..., description="処理結果メッセージ")


class FileProcessingResult(BaseModel):
    """File processing result model"""
    file_id: str = Field(..., description="ファイルID")
    success: bool = Field(..., description="処理成功フラグ")
    extracted_text: Optional[str] = Field(None, description="抽出されたテキスト")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")
    processing_time: float = Field(..., description="処理時間（秒）")
