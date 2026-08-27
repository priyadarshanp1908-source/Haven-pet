"""Behavior log schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BehaviorLogCreate(BaseModel):
    category: str  # eating, sleep, activity, mood, bathroom, other
    value: Optional[str] = None
    notes: Optional[str] = None
    logged_at: Optional[datetime] = None  # defaults to now on the server


class BehaviorLogUpdate(BaseModel):
    category: Optional[str] = None
    value: Optional[str] = None
    notes: Optional[str] = None
    logged_at: Optional[datetime] = None


class BehaviorLogOut(BaseModel):
    id: str
    pet_id: str
    logged_at: datetime
    category: str
    value: Optional[str] = None
    notes: Optional[str] = None
    flagged_anomaly: bool
    created_at: datetime

    model_config = {"from_attributes": True}

