from fastapi import HTTPException, status
from typing import Optional

from app.schemas.conversation import ConversationResponse, PaginatedConversationResponse

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
        from app.models.cassandra_models import ConversationModel
        conversations = await ConversationModel.get_user_conversations(
            user_id=user_id,
            limit=limit,
            before_conversation_id=before_conversation_id
        )
        data = [
            ConversationResponse(
                id=conv['conversation_id'],
                user1_id=conv['user_id'],
                user2_id=conv['other_user_id'],
                last_message_at=conv['last_updated'],
                last_message_content=conv['last_message']
            ) for conv in conversations
        ]
        next_cursor = data[-1].id if data else None
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
        from app.models.cassandra_models import ConversationModel, MessageModel
        conversation = await ConversationModel.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        user1_id = None
        user2_id = None
        if enrich_users:
            # Try to fetch the first message in the conversation to infer user IDs
            messages = await MessageModel.get_conversation_messages(conversation_id, limit=1)
            if messages:
                user1_id = messages[0]['sender_id']
                user2_id = messages[0]['receiver_id']
        return ConversationResponse(
            id=conversation['conversation_id'],
            user1_id=user1_id,
            user2_id=user2_id,
            last_message_at=conversation['created_at'],
            last_message_content=None
        )