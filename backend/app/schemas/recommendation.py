"""Recommendation schemas."""

from pydantic import BaseModel
from datetime import datetime


class RecommendationOut(BaseModel):
    id: str
    pet_id: str
    agent_source: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
