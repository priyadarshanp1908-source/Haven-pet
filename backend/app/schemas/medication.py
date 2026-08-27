"""Medication schemas."""

from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class MedicationCreate(BaseModel):
    name: str
    dosage: str
    schedule: str
    start_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = None


class MedicationOut(BaseModel):
    id: str
    pet_id: str
    name: str
    dosage: str
    schedule: str
    start_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
