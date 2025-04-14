from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.message import MessageResponse

class ConversationResponse(BaseModel):
    id: str = Field(..., description="Unique ID of the conversation (uuid)")
    user1_id: str = Field(..., description="ID of the first user (uuid)")
    user2_id: str = Field(..., description="ID of the second user (uuid)")
    last_message_at: datetime = Field(..., description="Timestamp of the last message")
    last_message_content: Optional[str] = Field(None, description="Content of the last message")

class ConversationDetail(ConversationResponse):
    messages: List[MessageResponse] = Field(..., description="List of messages in conversation")

class PaginatedConversationRequest(BaseModel):
    limit: int = Field(20, description="Number of items per page")
    before_conversation_id: Optional[str] = Field(None, description="Get conversations before this conversation_id (uuid)")

class PaginatedConversationResponse(BaseModel):
    total: int = Field(..., description="Total number of conversations")
    limit: int = Field(..., description="Number of items per page")
    data: List[ConversationResponse] = Field(..., description="List of conversations")
    next_cursor: Optional[str] = Field(None, description="Cursor for the next page (last conversation_id)")