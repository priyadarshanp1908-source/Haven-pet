"""
Proactive Health Reminder Agent — scheduled job that scans for upcoming
vaccinations and medication doses, creating notifications automatically.
Runs via APScheduler on a daily schedule.
"""

import logging
from datetime import date, timedelta, datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.vaccination import Vaccination
from app.models.medication import Medication
from app.models.pet import Pet
from app.models.notification import Notification, NotificationType

logger = logging.getLogger(__name__)

# Module-level scheduler instance
_scheduler: BackgroundScheduler | None = None


def start_scheduler():
    """Start the APScheduler background scheduler."""
    global _scheduler
    _scheduler = BackgroundScheduler()
    # Run daily at 8:00 AM
    _scheduler.add_job(
        _run_reminder_check,
        "cron",
        hour=8,
        minute=0,
        id="proactive_health_reminder",
        replace_existing=True,
    )
    # Also run once on startup (after a short delay)
    _scheduler.add_job(
        _run_reminder_check,
        "date",
        run_date=datetime.now(timezone.utc) + timedelta(seconds=10),
        id="startup_reminder_check",
    )
    _scheduler.start()
    logger.info("✅ APScheduler started — proactive reminder agent active")


def stop_scheduler():
    """Shut down the scheduler gracefully."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")


def _run_reminder_check():
    """Synchronous wrapper that runs the async check."""
    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_check_and_create_reminders())
        loop.close()
    except Exception as e:
        logger.error(f"Reminder check failed: {e}")


async def _check_and_create_reminders():
    """
    Scan all pets for:
    1. Vaccinations due within 7 days
    2. Active medications (as dose reminders)
    Creates notifications for the pet's owner.
    """
    async with AsyncSessionLocal() as db:
        today = date.today()
        window = today + timedelta(days=7)

        # 1. Check upcoming vaccinations
        result = await db.execute(
            select(Vaccination, Pet)
            .join(Pet, Vaccination.pet_id == Pet.id)
            .where(Vaccination.next_due_date.between(today, window))
        )
        for vax, pet in result.all():
            days_until = (vax.next_due_date - today).days
            message = (
                f"💉 Vaccination reminder: {pet.name}'s {vax.vaccine_name} "
                f"is due {'today' if days_until == 0 else f'in {days_until} day(s)'} "
                f"(due: {vax.next_due_date.isoformat()})."
            )

            # Avoid duplicate notifications (check if one already exists for this vaccination)
            existing = await db.execute(
                select(Notification).where(
                    Notification.user_id == pet.owner_id,
                    Notification.pet_id == pet.id,
                    Notification.type == NotificationType.VACCINATION_DUE,
                    Notification.message.contains(vax.vaccine_name),
                    Notification.created_at >= datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc),
                )
            )
            if not existing.scalar_one_or_none():
                notif = Notification(
                    user_id=pet.owner_id,
                    pet_id=pet.id,
                    type=NotificationType.VACCINATION_DUE,
                    message=message,
                )
                db.add(notif)
                logger.info(f"Created vaccination reminder for {pet.name}: {vax.vaccine_name}")

        # 2. Check active medications
        result = await db.execute(
            select(Medication, Pet)
            .join(Pet, Medication.pet_id == Pet.id)
            .where(
                Medication.start_date <= today,
                (Medication.end_date >= today) | (Medication.end_date.is_(None)),
            )
        )
        for med, pet in result.all():
            message = (
                f"💊 Medication reminder: Give {pet.name} their {med.name} "
                f"({med.dosage}, {med.schedule})."
            )

            existing = await db.execute(
                select(Notification).where(
                    Notification.user_id == pet.owner_id,
                    Notification.pet_id == pet.id,
                    Notification.type == NotificationType.MEDICATION_REMINDER,
                    Notification.message.contains(med.name),
                    Notification.created_at >= datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc),
                )
            )
            if not existing.scalar_one_or_none():
                notif = Notification(
                    user_id=pet.owner_id,
                    pet_id=pet.id,
                    type=NotificationType.MEDICATION_REMINDER,
                    message=message,
                )
                db.add(notif)
                logger.info(f"Created medication reminder for {pet.name}: {med.name}")

        await db.commit()
        logger.info("✅ Proactive reminder check completed")
