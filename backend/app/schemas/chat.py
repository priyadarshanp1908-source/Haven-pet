"""Chat schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ChatRequest(BaseModel):
    pet_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    reply: str
    agent_used: str  # which agent handled the request


class ChatMessageOut(BaseModel):
    id: str
    user_id: str
    pet_id: Optional[str] = None
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
