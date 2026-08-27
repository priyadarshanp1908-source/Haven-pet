"""Pet service — CRUD operations for pet profiles."""

import os
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status, UploadFile

from app.models.pet import Pet
from app.models.user import User
from app.schemas.pet import PetCreate, PetUpdate
from app.core.config import settings


async def list_pets(user: User, db: AsyncSession) -> list[Pet]:
    """List all pets belonging to the current user."""
    result = await db.execute(
        select(Pet).where(Pet.owner_id == user.id).order_by(Pet.created_at.desc())
    )
    return list(result.scalars().all())


async def get_pet(pet_id: str, user: User, db: AsyncSession) -> Pet:
    """Get a single pet by ID, ensuring ownership."""
    pet = await _get_pet_or_404(pet_id, db)
    _check_ownership(pet, user)
    return pet


async def create_pet(data: PetCreate, user: User, db: AsyncSession) -> Pet:
    """Create a new pet for the current user."""
    pet = Pet(
        owner_id=user.id,
        name=data.name,
        species=data.species,
        breed=data.breed,
        dob=data.dob,
        weight=data.weight,
        gender=data.gender,
        medical_history=data.medical_history,
    )
    db.add(pet)
    await db.flush()
    return pet


async def update_pet(pet_id: str, data: PetUpdate, user: User, db: AsyncSession) -> Pet:
    """Update a pet's profile fields."""
    pet = await _get_pet_or_404(pet_id, db)
    _check_ownership(pet, user)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pet, field, value)

    await db.flush()
    return pet


async def delete_pet(pet_id: str, user: User, db: AsyncSession) -> None:
    """Delete a pet."""
    pet = await _get_pet_or_404(pet_id, db)
    _check_ownership(pet, user)
    await db.delete(pet)
    await db.flush()


async def upload_photo(pet_id: str, file: UploadFile, user: User, db: AsyncSession) -> Pet:
    """Upload and save a pet photo."""
    pet = await _get_pet_or_404(pet_id, db)
    _check_ownership(pet, user)

    # Generate unique filename
    ext = os.path.splitext(file.filename or "photo.jpg")[1] or ".jpg"
    filename = f"{pet_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    pet.photo_url = f"/uploads/{filename}"
    await db.flush()
    return pet


async def _get_pet_or_404(pet_id: str, db: AsyncSession) -> Pet:
    """Fetch pet by ID or raise 404."""
    result = await db.execute(select(Pet).where(Pet.id == pet_id))
    pet = result.scalar_one_or_none()
    if not pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found")
    return pet


def _check_ownership(pet: Pet, user: User) -> None:
    """Ensure the user owns this pet."""
    if pet.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your pet")
