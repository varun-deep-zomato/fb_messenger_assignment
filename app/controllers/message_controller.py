from typing import Optional
from datetime import datetime
from fastapi import HTTPException, status
import logging

from app.schemas.message import MessageCreate, MessageResponse, PaginatedMessageResponse
from app.models.cassandra_models import MessageModel, ConversationModel
from app.util.util import generate_conversation_id

logger = logging.getLogger(__name__)

class MessageController:
    """
    Controller for handling message operations
    """
    
    def parse_messages(self, messages):
        return [
            MessageResponse(
                id=m['id'],
                sender_id=m['sender_id'],
                receiver_id=m['receiver_id'],
                content=m['content'],
                created_at=m['created_at'],
                conversation_id=m['conversation_id']
            )
            for m in messages
        ]

    async def send_message(self, message_data: MessageCreate) -> MessageResponse:
        """
        Send a message from one user to another
        """
        try:
            # Use deterministic conversation id
            conversation_id = generate_conversation_id(str(message_data.sender_id), str(message_data.receiver_id))
            result = await MessageModel.create_message(
                conversation_id=conversation_id,
                sender_id=str(message_data.sender_id),
                receiver_id=str(message_data.receiver_id),
                content=message_data.content
            )
            return MessageResponse(
                id=str(result['id']),
                sender_id=str(result['sender_id']),
                receiver_id=str(result['receiver_id']),
                content=result['content'],
                created_at=result['created_at'],
                conversation_id=str(result['conversation_id'])
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 20,
        last_message_id: Optional[str] = None
    ) -> PaginatedMessageResponse:
        """
        Get all messages in a conversation with stateless pagination (using last_message_id as token)
        """
        logger.info(f"[Controller] Fetching messages for conversation_id={conversation_id}, limit={limit}, last_message_id={last_message_id}")
        try:
            messages = await MessageModel.get_conversation_messages(
                conversation_id=conversation_id,
                limit=limit,
                last_message_id=last_message_id
            )
            logger.info(f"[Controller] Retrieved {len(messages)} messages from model")
            data = self.parse_messages(messages)
            next_cursor = messages[-1]['id'] if messages else None
            logger.info(f"[Controller] Returning {len(data)} parsed messages, next_cursor={next_cursor}")
            return PaginatedMessageResponse(
                total=len(data),
                limit=limit,
                data=data,
                next_cursor=next_cursor
            )
        except Exception as e:
            logger.error(f"[Controller] Exception: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_messages_before_timestamp(
        self,
        conversation_id: str,
        before_message_id: str,
        limit: int = 20
    ) -> PaginatedMessageResponse:
        """
        Get messages in a conversation before a specific message_id (for pagination)
        """
        try:
            messages = await MessageModel.get_conversation_messages(
                conversation_id=conversation_id,
                limit=limit,
                last_message_id=before_message_id
            )
            data = self.parse_messages(messages)
            next_cursor = messages[-1]['id'] if messages else None
            return PaginatedMessageResponse(
                total=len(data),
                limit=limit,
                data=data,
                next_cursor=next_cursor
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))