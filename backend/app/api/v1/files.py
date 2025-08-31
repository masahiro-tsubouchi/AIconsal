"""File upload and processing API endpoints"""
import os
import time
from typing import List
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
import structlog

from app.core.config import get_settings
from app.models.files import FileUploadResponse, UploadedFile
from app.services.file_service import FileService

router = APIRouter()
logger = structlog.get_logger()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(None),
    file_service: FileService = Depends()
) -> FileUploadResponse:
    """Upload and process a file"""
    start_time = time.time()
    settings = get_settings()
    
    try:
        # Validate file size
        if file.size > settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"ファイルサイズが上限を超えています（最大: {settings.max_file_size / 1024 / 1024:.1f}MB）"
            )
        
        # Validate file type
        file_extension = os.path.splitext(file.filename or "")[1].lower()
        if file_extension not in settings.supported_file_types:
            raise HTTPException(
                status_code=400,
                detail=f"サポートされていないファイル形式です。対応形式: {', '.join(settings.supported_file_types)}"
            )
        
        logger.info(
            "file_upload_started",
            filename=file.filename,
            file_size=file.size,
            file_type=file_extension,
            session_id=session_id
        )
        
        # Process the uploaded file
        uploaded_file = await file_service.process_uploaded_file(
            file=file,
            session_id=session_id or "default"
        )
        
        processing_time = time.time() - start_time
        
        logger.info(
            "file_upload_completed",
            file_id=uploaded_file.id,
            filename=uploaded_file.filename,
            processing_time=processing_time,
            content_length=len(uploaded_file.content or "")
        )
        
        return FileUploadResponse(
            file=uploaded_file,
            message=f"ファイル '{uploaded_file.original_filename}' が正常にアップロードされました"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(
            "file_upload_error",
            filename=file.filename,
            error=str(e),
            processing_time=processing_time
        )
        raise HTTPException(status_code=500, detail=f"ファイル処理エラー: {str(e)}")


@router.get("/{file_id}")
async def get_file_info(
    file_id: str,
    file_service: FileService = Depends()
) -> UploadedFile:
    """Get information about an uploaded file"""
    try:
        file_info = await file_service.get_file_info(file_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="ファイルが見つかりません")
        return file_info
    except Exception as e:
        logger.error("get_file_info_error", file_id=file_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"ファイル情報取得エラー: {str(e)}")


@router.get("/session/{session_id}")
async def get_session_files(
    session_id: str,
    file_service: FileService = Depends()
) -> List[UploadedFile]:
    """Get all files for a session"""
    try:
        files = await file_service.get_session_files(session_id)
        return files
    except Exception as e:
        logger.error("get_session_files_error", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"セッションファイル取得エラー: {str(e)}")


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    file_service: FileService = Depends()
) -> dict:
    """Delete an uploaded file"""
    try:
        success = await file_service.delete_file(file_id)
        if not success:
            raise HTTPException(status_code=404, detail="ファイルが見つかりません")
        
        logger.info("file_deleted", file_id=file_id)
        return {"message": "ファイルが削除されました", "file_id": file_id}
    except Exception as e:
        logger.error("delete_file_error", file_id=file_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"ファイル削除エラー: {str(e)}")
