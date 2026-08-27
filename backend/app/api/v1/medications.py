"""Medication routes — add and list medication records for a pet."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.medication import MedicationCreate, MedicationOut
from app.models.medication import Medication
from app.models.user import User
from app.services.pet_service import _get_pet_or_404, _check_ownership

router = APIRouter()


@router.post("/pets/{pet_id}/medications", response_model=MedicationOut, status_code=201)
async def add_medication(
    pet_id: str,
    data: MedicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a medication record for a pet."""
    pet = await _get_pet_or_404(pet_id, db)
    _check_ownership(pet, current_user)

    med = Medication(
        pet_id=pet_id,
        name=data.name,
        dosage=data.dosage,
        schedule=data.schedule,
        start_date=data.start_date,
        end_date=data.end_date,
        notes=data.notes,
    )
    db.add(med)
    await db.flush()
    return med


@router.get("/pets/{pet_id}/medications", response_model=List[MedicationOut])
async def list_medications(
    pet_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all medications for a pet."""
    pet = await _get_pet_or_404(pet_id, db)
    _check_ownership(pet, current_user)

    result = await db.execute(
        select(Medication)
        .where(Medication.pet_id == pet_id)
        .order_by(Medication.start_date.desc())
    )
    return list(result.scalars().all())
