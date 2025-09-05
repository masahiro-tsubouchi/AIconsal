"""Chat API endpoints"""
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.encoders import jsonable_encoder
from uuid import uuid4
import structlog

from app.core.config import get_settings
from app.models.chat import ChatRequest, ChatResponse, ChatMessage, ChatHistory, DebugInfo
from app.models.ws import WSStatus, WSError, WSChatMessage
from app.services.chat_service import ChatService

router = APIRouter()
logger = structlog.get_logger()

def get_chat_service() -> ChatService:
    """Dependency factory to create ChatService without FastAPI inspecting its __init__ signature."""
    return ChatService()


@router.post("/", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
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
            file_ids=request.file_ids,
            debug=bool(request.debug),
        )
        
        processing_time = time.time() - start_time
        
        # Create response message
        assistant_message = ChatMessage(
            session_id=session_id,
            content=response_content,
            role="assistant",
            processing_time=processing_time
        )

        # Attach debug header and payload if requested
        debug_payload = None
        if bool(request.debug):
            last_debug = chat_service.get_last_debug_info()
            if last_debug:
                try:
                    debug_payload = DebugInfo(**last_debug)
                    # Prepend display header to assistant content (UIでも使えるように）
                    assistant_message.content = f"[DEBUG] {debug_payload.display_header}\n\n" + assistant_message.content
                except Exception as e:  # noqa: BLE001
                    logger.warning("attach_debug_info_failed", session_id=session_id, error=str(e))
        
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
            processing_time=processing_time,
            debug=debug_payload,
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
    limit: Optional[int] = Query(None, ge=1, description="返却する最新メッセージ数の上限"),
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatHistory:
    """Get chat history for a session

    Optional query parameter `limit` allows returning only the last N messages.
    """
    try:
        history = await chat_service.get_chat_history(session_id)
        if not history:
            # 初回アクセスなどセッション未作成の場合は空の履歴を返す
            return ChatHistory(session_id=session_id, messages=[])

        # Apply limit if provided
        if limit is not None and history.messages:
            messages = history.messages[-limit:]
            return ChatHistory(
                session_id=history.session_id,
                messages=messages,
                created_at=history.created_at,
                last_active=history.last_active,
            )

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
        
        # Send connection confirmation (typed JSON)
        status = WSStatus(session_id=session_id, data="connected")
        await websocket.send_json(jsonable_encoder(status))
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
                
                # Create assistant message and persist to history
                assistant_message = ChatMessage(
                    session_id=session_id,
                    content=response,
                    role="assistant",
                )
                await chat_service.add_message_to_history(assistant_message)

                # Send typed message back as JSON
                ws_msg = WSChatMessage(session_id=session_id, data=assistant_message)
                await websocket.send_json(jsonable_encoder(ws_msg))
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
                    error_msg = WSError(session_id=session_id, data=f"エラー: {str(e)}")
                    await websocket.send_json(jsonable_encoder(error_msg))
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
