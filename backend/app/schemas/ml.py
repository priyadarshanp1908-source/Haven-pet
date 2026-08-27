"""ML recognition schemas."""

from pydantic import BaseModel
from typing import List, Optional


class RecognitionTag(BaseModel):
    label: str
    confidence: float


class RecognitionResult(BaseModel):
    species: Optional[str] = None
    breed: Optional[str] = None
    confidence: float
    health_tags: List[RecognitionTag] = []
    message: str
