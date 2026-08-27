"""Behavior log routes — create and query behavior entries for a pet."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.behavior_log import BehaviorLogCreate, BehaviorLogUpdate, BehaviorLogOut
from app.services import behavior_service
from app.models.user import User

router = APIRouter()


@router.post("/pets/{pet_id}/behavior-logs", response_model=BehaviorLogOut, status_code=201)
async def create_behavior_log(
    pet_id: str,
    data: BehaviorLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Log a behavior/routine entry for a pet."""
    return await behavior_service.create_log(pet_id, data, current_user, db)


@router.get("/pets/{pet_id}/behavior-logs", response_model=List[BehaviorLogOut])
async def list_behavior_logs(
    pet_id: str,
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    category: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query behavior logs with optional date range and category filters."""
    return await behavior_service.get_logs(
        pet_id, current_user, db,
        from_date=from_date, to_date=to_date,
        category=category, limit=limit, offset=offset,
    )


@router.put("/pets/{pet_id}/behavior-logs/{log_id}", response_model=BehaviorLogOut)
async def update_behavior_log(
    pet_id: str,
    log_id: str,
    data: BehaviorLogUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a behavior log entry for a pet."""
    return await behavior_service.update_log(log_id, pet_id, data, current_user, db)


@router.delete("/pets/{pet_id}/behavior-logs/{log_id}", status_code=204)
async def delete_behavior_log(
    pet_id: str,
    log_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a behavior log entry for a pet."""
    await behavior_service.delete_log(log_id, pet_id, current_user, db)
    return None

