"""Notification routes — list and mark-as-read for user notifications."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.notification import NotificationOut
from app.services import notification_service
from app.models.user import User

router = APIRouter()


@router.get("/notifications", response_model=List[NotificationOut])
async def list_notifications(
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all notifications for the current user."""
    return await notification_service.get_notifications(current_user, db, unread_only=unread_only)


@router.patch("/notifications/{notif_id}/read", response_model=NotificationOut)
async def mark_read(
    notif_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a notification as read."""
    return await notification_service.mark_as_read(notif_id, current_user, db)
