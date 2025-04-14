from fastapi import APIRouter, Depends, Query, Path, Body
from typing import Optional
from datetime import datetime

from app.controllers.message_controller import MessageController
from app.schemas.message import (
    MessageCreate, 
    MessageResponse, 
    PaginatedMessageResponse
)

router = APIRouter(prefix="/api/messages", tags=["Messages"])

@router.post("/", response_model=MessageResponse, status_code=201)
async def send_message(
    message: MessageCreate = Body(...),
    message_controller: MessageController = Depends()
) -> MessageResponse:
    """
    Send a message from one user to another
    """
    return await message_controller.send_message(message)

@router.get("/conversation/{conversation_id}", response_model=PaginatedMessageResponse)
async def get_conversation_messages(
    conversation_id: str = Path(..., description="ID of the conversation (uuid)"),
    limit: int = Query(20, description="Number of messages per page"),
    before_message_id: Optional[str] = Query(None, description="Get messages before this message_id (timeuuid)"),
    message_controller: MessageController = Depends()
) -> PaginatedMessageResponse:
    """
    Get all messages in a conversation with cursor-based pagination
    """
    return await message_controller.get_conversation_messages(
        conversation_id=conversation_id,
        limit=limit,
        last_message_id=before_message_id
    )

@router.get("/conversation/{conversation_id}/before", response_model=PaginatedMessageResponse)
async def get_messages_before_timestamp(
    conversation_id: str = Path(..., description="ID of the conversation (uuid)"),
    before_message_id: Optional[str] = Query(None, description="Get messages before this message_id (timeuuid)"),
    limit: int = Query(20, description="Number of messages per page"),
    message_controller: MessageController = Depends()
) -> PaginatedMessageResponse:
    """
    Get messages in a conversation before a specific message_id with cursor-based pagination
    """
    return await message_controller.get_messages_before_timestamp(
        conversation_id=conversation_id,
        before_message_id=before_message_id,
        limit=limit
    )