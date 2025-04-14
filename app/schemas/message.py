from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class MessageBase(BaseModel):
    content: str = Field(..., description="Content of the message")

class MessageCreate(MessageBase):
    sender_id: str = Field(..., description="ID of the sender")
    receiver_id: str = Field(..., description="ID of the receiver")

class MessageResponse(MessageBase):
    id: str = Field(..., description="Unique ID of the message (timeuuid)")
    sender_id: str = Field(..., description="ID of the sender (uuid)")
    receiver_id: str = Field(..., description="ID of the receiver (uuid)")
    created_at: datetime = Field(..., description="Timestamp when message was created")
    conversation_id: str = Field(..., description="ID of the conversation (uuid)")

class PaginatedMessageRequest(BaseModel):
    limit: int = Field(20, description="Number of items per page")
    before_message_id: Optional[str] = Field(None, description="Get messages before this message_id (timeuuid)")

class PaginatedMessageResponse(BaseModel):
    total: int = Field(..., description="Total number of messages")
    limit: int = Field(..., description="Number of items per page")
    data: List[MessageResponse] = Field(..., description="List of messages")
    next_cursor: Optional[str] = Field(None, description="Cursor for the next page (last message_id)")