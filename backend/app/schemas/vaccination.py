"""Vaccination schemas."""

from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class VaccinationCreate(BaseModel):
    vaccine_name: str
    date_administered: date
    next_due_date: Optional[date] = None


class VaccinationOut(BaseModel):
    id: str
    pet_id: str
    vaccine_name: str
    date_administered: date
    next_due_date: Optional[date] = None
    created_at: datetime

    model_config = {"from_attributes": True}
