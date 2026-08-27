"""Pet schemas — CRUD operations for pet profiles."""

from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional


class PetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    species: str = Field(..., min_length=1, max_length=50)
    breed: Optional[str] = None
    dob: Optional[date] = None
    weight: Optional[float] = Field(None, gt=0)
    gender: Optional[str] = None
    medical_history: Optional[str] = None


class PetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    species: Optional[str] = None
    breed: Optional[str] = None
    dob: Optional[date] = None
    weight: Optional[float] = Field(None, gt=0)
    gender: Optional[str] = None
    medical_history: Optional[str] = None


class PetOut(BaseModel):
    id: str
    owner_id: str
    name: str
    species: str
    breed: Optional[str] = None
    dob: Optional[date] = None
    weight: Optional[float] = None
    gender: Optional[str] = None
    photo_url: Optional[str] = None
    medical_history: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
