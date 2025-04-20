from fastapi import HTTPException, status
from typing import Optional
import uuid

from app.schemas.conversation import ConversationResponse, PaginatedConversationResponse
from app.models.cassandra_models import ConversationModel, MessageModel
class ConversationController:
    """
    Controller for handling conversation operations
    This is a stub that students will implement
    """
    
    async def get_user_conversations(
        self, 
        user_id: str, 
        limit: int = 20, 
        before_conversation_id: Optional[str] = None
    ) -> PaginatedConversationResponse:
        """
        Get all conversations for a user with stateless pagination (using before_conversation_id as token)
        """

        conversations = await ConversationModel.get_user_conversations(
            user_id=user_id,
            limit=limit,
            before_conversation_id=before_conversation_id
        )
        data = [
            ConversationResponse(
                conversation_id=conv['conversation_id'],
                user1_id=conv['user_id'],
                user2_id=conv['other_user_id'],
                last_message_at=conv['last_updated'],
                last_message_content=conv['last_message']
            ) for conv in conversations
        ]
        next_cursor = data[-1].conversation_id if data else None
        return PaginatedConversationResponse(
            total=len(data),
            limit=limit,
            data=data,
            next_cursor=next_cursor
        )
    
    async def get_conversation(self, conversation_id: str, enrich_users: bool = False) -> ConversationResponse:
        """
        Get a specific conversation by ID
        Args:
            conversation_id: ID of the conversation
            enrich_users: If True, attempt to fetch user1_id and user2_id from messages or another source
        """

        conversation = await ConversationModel.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        user1_id = ""
        user2_id = ""
        if enrich_users:
            # Try to fetch the first message in the conversation to infer user IDs
            messages = await MessageModel.get_conversation_messages(conversation_id, limit=1)
            if messages:
                user1_id = str(messages[0]['sender_id'])
                user2_id = str(messages[0]['receiver_id'])
        return ConversationResponse(
            conversation_id=conversation['conversation_id'],
            user1_id=user1_id,
            user2_id=user2_id,
            last_message_at=conversation['created_at'],
            last_message_content=None
        )