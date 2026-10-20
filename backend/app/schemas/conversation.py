
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreateResponse(BaseModel):
    conversation_id: int
    status: str


class MessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime


class ConversationResponse(BaseModel):
    conversation_id: int
    status: str
    current_requirements: dict
    messages: list[MessageResponse]
