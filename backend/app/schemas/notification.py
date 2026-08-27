"""Notification schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NotificationOut(BaseModel):
    id: str
    user_id: str
    pet_id: Optional[str] = None
    type: str
    message: str
    is_read: bool
    created_at: datetime
    scheduled_for: Optional[datetime] = None

    model_config = {"from_attributes": True}
