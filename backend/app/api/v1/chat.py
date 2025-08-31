"""Chat API endpoints"""
import time
from typing import List
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from uuid import uuid4
import structlog

from app.core.config import get_settings
from app.models.chat import ChatRequest, ChatResponse, ChatMessage, ChatHistory
from app.services.chat_service import ChatService

router = APIRouter()
logger = structlog.get_logger()


@router.post("/", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    chat_service: ChatService = Depends()
) -> ChatResponse:
    """Send a chat message and get AI response"""
    start_time = time.time()
    
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid4())
        
        logger.info(
            "chat_request_received",
            session_id=session_id,
            message_length=len(request.message),
            file_count=len(request.file_ids)
        )
        
        # Process the chat request
        response_content = await chat_service.process_message(
            message=request.message,
            session_id=session_id,
            file_ids=request.file_ids
        )
        
        processing_time = time.time() - start_time
        
        # Create response message
        assistant_message = ChatMessage(
            session_id=session_id,
            content=response_content,
            role="assistant",
            processing_time=processing_time
        )
        
        # Save to history
        await chat_service.add_message_to_history(assistant_message)
        
        logger.info(
            "chat_response_generated",
            session_id=session_id,
            processing_time=processing_time,
            response_length=len(response_content)
        )
        
        return ChatResponse(
            message=assistant_message,
            session_id=session_id,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(
            "chat_processing_error",
            session_id=request.session_id,
            error=str(e),
            processing_time=time.time() - start_time
        )
        raise HTTPException(status_code=500, detail=f"チャット処理エラー: {str(e)}")


@router.get("/history/{session_id}", response_model=ChatHistory)
async def get_chat_history(
    session_id: str,
    chat_service: ChatService = Depends()
) -> ChatHistory:
    """Get chat history for a session"""
    try:
        history = await chat_service.get_chat_history(session_id)
        if not history:
            # 初回アクセスなどセッション未作成の場合は空の履歴を返す
            return ChatHistory(session_id=session_id, messages=[])
        return history
    except HTTPException as he:
        # 既存のHTTP例外はそのまま伝播
        raise he
    except Exception as e:
        logger.error("get_history_error", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"履歴取得エラー: {str(e)}")


@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    logger.info("websocket_connection_attempt", session_id=session_id)
    
    try:
        # Accept WebSocket connection
        await websocket.accept()
        logger.info("websocket_accepted", session_id=session_id)
        
        # Initialize chat service first
        chat_service = ChatService()
        
        # Send connection confirmation
        await websocket.send_text("WebSocket接続が確立されました")
        logger.info("websocket_setup_complete", session_id=session_id)
        
        # Main message loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                logger.info("websocket_message_received", session_id=session_id, message_length=len(data))
                
                # Process message
                response = await chat_service.process_message(
                    message=data,
                    session_id=session_id
                )
                
                # Send response back
                await websocket.send_text(response)
                logger.info("websocket_response_sent", session_id=session_id, response_length=len(response))
                    
            except WebSocketDisconnect:
                logger.info("websocket_client_disconnected", session_id=session_id)
                break
            except Exception as e:
                logger.error(
                    "websocket_message_processing_error",
                    session_id=session_id,
                    error=str(e),
                    error_type=type(e).__name__
                )
                try:
                    await websocket.send_text(f"エラー: {str(e)}")
                except:
                    logger.info("websocket_error_send_failed", session_id=session_id)
                    break
                
    except WebSocketDisconnect:
        logger.info("websocket_disconnected_during_setup", session_id=session_id)
    except Exception as e:
        logger.error(
            "websocket_setup_error", 
            session_id=session_id, 
            error=str(e),
            error_type=type(e).__name__
        )
    finally:
        logger.info("websocket_connection_ended", session_id=session_id)
