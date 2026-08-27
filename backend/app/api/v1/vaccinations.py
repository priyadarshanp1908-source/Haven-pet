"""Vaccination routes — add and list vaccination records for a pet."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.vaccination import VaccinationCreate, VaccinationOut
from app.models.vaccination import Vaccination
from app.models.user import User
from app.services.pet_service import _get_pet_or_404, _check_ownership

router = APIRouter()


@router.post("/pets/{pet_id}/vaccinations", response_model=VaccinationOut, status_code=201)
async def add_vaccination(
    pet_id: str,
    data: VaccinationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a vaccination record for a pet."""
    pet = await _get_pet_or_404(pet_id, db)
    _check_ownership(pet, current_user)

    vax = Vaccination(
        pet_id=pet_id,
        vaccine_name=data.vaccine_name,
        date_administered=data.date_administered,
        next_due_date=data.next_due_date,
    )
    db.add(vax)
    await db.flush()
    return vax


@router.get("/pets/{pet_id}/vaccinations", response_model=List[VaccinationOut])
async def list_vaccinations(
    pet_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all vaccinations for a pet."""
    pet = await _get_pet_or_404(pet_id, db)
    _check_ownership(pet, current_user)

    result = await db.execute(
        select(Vaccination)
        .where(Vaccination.pet_id == pet_id)
        .order_by(Vaccination.date_administered.desc())
    )
    return list(result.scalars().all())
