"""Notification service — CRUD for notifications + email stub."""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.notification import Notification, NotificationType
from app.models.user import User

logger = logging.getLogger(__name__)


async def create_notification(
    user_id: str,
    pet_id: Optional[str],
    notif_type: NotificationType,
    message: str,
    db: AsyncSession,
) -> Notification:
    """Create a new notification (in-app + stub email)."""
    notif = Notification(
        user_id=user_id,
        pet_id=pet_id,
        type=notif_type,
        message=message,
    )
    db.add(notif)
    await db.flush()

    # Email stub — logs to console in dev
    _send_email_stub(user_id, message)

    return notif


async def get_notifications(
    user: User, db: AsyncSession, unread_only: bool = False
) -> list[Notification]:
    """Get all notifications for a user, optionally filtered to unread."""
    query = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        query = query.where(Notification.is_read == False)  # noqa: E712
    query = query.order_by(Notification.created_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def mark_as_read(notif_id: str, user: User, db: AsyncSession) -> Notification:
    """Mark a notification as read."""
    result = await db.execute(
        select(Notification).where(Notification.id == notif_id, Notification.user_id == user.id)
    )
    notif = result.scalar_one_or_none()
    if not notif:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notif.is_read = True
    await db.flush()
    return notif


def _send_email_stub(user_id: str, message: str) -> None:
    """
    Email backend stub — logs to console.
    Replace with real SMTP/SendGrid/SES when ready.
    """
    logger.info(f"[EMAIL STUB] To user {user_id}: {message[:100]}...")
