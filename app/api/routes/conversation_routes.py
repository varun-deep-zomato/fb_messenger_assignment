from fastapi import APIRouter, Depends, Query, Path
from typing import Optional

from app.controllers.conversation_controller import ConversationController
from app.schemas.conversation import (
    ConversationResponse,
    PaginatedConversationResponse
)

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])

@router.get("/user/{user_id}", response_model=PaginatedConversationResponse)
async def get_user_conversations(
    user_id: str = Path(..., description="ID of the user (uuid)"),
    limit: int = Query(20, description="Number of conversations per page"),
    before_conversation_id: Optional[str] = Query(None, description="Get conversations before this conversation_id (uuid)"),
    conversation_controller: ConversationController = Depends()
) -> PaginatedConversationResponse:
    """
    Get all conversations for a user with cursor-based pagination
    """
    return await conversation_controller.get_user_conversations(
        user_id=user_id,
        limit=limit,
        before_conversation_id=before_conversation_id
    )

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str = Path(..., description="ID of the conversation (uuid)"),
    enrich_users: bool = Query(False, description="If true, enrich with user IDs from messages"),
    conversation_controller: ConversationController = Depends()
) -> ConversationResponse:
    """
    Get a specific conversation by ID, optionally enriching with user IDs from messages.
    """
    return await conversation_controller.get_conversation(conversation_id, enrich_users=enrich_users)