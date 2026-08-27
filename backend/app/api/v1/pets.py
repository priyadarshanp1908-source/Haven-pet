"""Pet routes — CRUD for pet profiles with photo upload."""

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.pet import PetCreate, PetUpdate, PetOut
from app.services import pet_service
from app.models.user import User

router = APIRouter()


@router.get("/pets", response_model=List[PetOut])
async def list_pets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all pets belonging to the current user."""
    return await pet_service.list_pets(current_user, db)


@router.post("/pets", response_model=PetOut, status_code=201)
async def create_pet(
    data: PetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new pet profile."""
    return await pet_service.create_pet(data, current_user, db)


@router.get("/pets/{pet_id}", response_model=PetOut)
async def get_pet(
    pet_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a pet's full profile."""
    return await pet_service.get_pet(pet_id, current_user, db)


@router.put("/pets/{pet_id}", response_model=PetOut)
async def update_pet(
    pet_id: str,
    data: PetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a pet's profile."""
    return await pet_service.update_pet(pet_id, data, current_user, db)


@router.delete("/pets/{pet_id}", status_code=204)
async def delete_pet(
    pet_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a pet profile."""
    await pet_service.delete_pet(pet_id, current_user, db)


@router.post("/pets/{pet_id}/photo", response_model=PetOut)
async def upload_photo(
    pet_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a pet photo."""
    return await pet_service.upload_photo(pet_id, file, current_user, db)
