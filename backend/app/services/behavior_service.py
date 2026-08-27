"""Behavior service — log entries, querying, anomaly detection."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException

from app.models.behavior_log import BehaviorLog, BehaviorCategory
from app.models.pet import Pet
from app.models.user import User
from app.schemas.behavior_log import BehaviorLogCreate, BehaviorLogUpdate
from app.services.pet_service import _get_pet_or_404, _check_ownership


async def create_log(
    pet_id: str, data: BehaviorLogCreate, user: User, db: AsyncSession
) -> BehaviorLog:
    """Create a new behavior log entry for a pet."""
    pet = await _get_pet_or_404(pet_id, db)
    _check_ownership(pet, user)

    # Validate category
    try:
        BehaviorCategory(data.category)
    except ValueError:
        valid = [c.value for c in BehaviorCategory]
        raise ValueError(f"Invalid category. Must be one of: {valid}")

    log = BehaviorLog(
        pet_id=pet_id,
        category=data.category,
        value=data.value,
        notes=data.notes,
        logged_at=data.logged_at or datetime.now(timezone.utc),
        flagged_anomaly=False,
    )

    db.add(log)
    await db.flush()
    return log


async def get_logs(
    pet_id: str,
    user: User,
    db: AsyncSession,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    category: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[BehaviorLog]:
    """Retrieve behavior logs with optional date/category filters."""
    pet = await _get_pet_or_404(pet_id, db)
    _check_ownership(pet, user)

    query = select(BehaviorLog).where(BehaviorLog.pet_id == pet_id)

    if from_date:
        query = query.where(BehaviorLog.logged_at >= from_date)
    if to_date:
        query = query.where(BehaviorLog.logged_at <= to_date)
    if category:
        query = query.where(BehaviorLog.category == category)

    query = query.order_by(BehaviorLog.logged_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    return list(result.scalars().all())


async def update_log(
    log_id: str, pet_id: str, data: BehaviorLogUpdate, user: User, db: AsyncSession
) -> BehaviorLog:
    """Update an existing behavior log entry."""
    pet = await _get_pet_or_404(pet_id, db)
    _check_ownership(pet, user)

    result = await db.execute(
        select(BehaviorLog).where(
            BehaviorLog.id == log_id, BehaviorLog.pet_id == pet_id
        )
    )
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Behavior log entry not found.")

    # Validate category if provided
    if data.category is not None:
        try:
            BehaviorCategory(data.category)
        except ValueError:
            valid = [c.value for c in BehaviorCategory]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Must be one of: {valid}",
            )
        log.category = data.category

    if data.value is not None:
        log.value = data.value
    if data.notes is not None:
        log.notes = data.notes
    if data.logged_at is not None:
        log.logged_at = data.logged_at

    await db.flush()
    return log


async def delete_log(
    log_id: str, pet_id: str, user: User, db: AsyncSession
) -> None:
    """Delete a behavior log entry."""
    pet = await _get_pet_or_404(pet_id, db)
    _check_ownership(pet, user)

    result = await db.execute(
        select(BehaviorLog).where(
            BehaviorLog.id == log_id, BehaviorLog.pet_id == pet_id
        )
    )
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Behavior log entry not found.")

    await db.delete(log)
    await db.flush()

