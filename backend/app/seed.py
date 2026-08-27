"""Seed script — creates a demo user and pet for testing."""

import asyncio
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.pet import Pet
from app.models.vaccination import Vaccination
from app.models.behavior_log import BehaviorLog, BehaviorCategory
from datetime import date, datetime, timezone, timedelta


async def seed():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if demo user exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == "demo@havenpet.com"))
        if result.scalar_one_or_none():
            print("Demo user already exists — skipping seed.")
            return

        # Create demo user
        user = User(
            name="Demo User",
            email="demo@havenpet.com",
            hashed_password=hash_password("password123"),
        )
        db.add(user)
        await db.flush()

        # Create demo pet
        pet = Pet(
            owner_id=user.id,
            name="Buddy",
            species="dog",
            breed="Golden Retriever",
            dob=date(2021, 3, 15),
            weight=30.5,
            gender="male",
            medical_history="Annual checkups up to date. No known allergies.",
        )
        db.add(pet)
        await db.flush()

        # Add vaccinations
        vax1 = Vaccination(
            pet_id=pet.id,
            vaccine_name="Rabies",
            date_administered=date(2024, 6, 1),
            next_due_date=date.today() + timedelta(days=5),  # Due soon for testing
        )
        vax2 = Vaccination(
            pet_id=pet.id,
            vaccine_name="DHPP",
            date_administered=date(2024, 1, 15),
            next_due_date=date(2025, 1, 15),
        )
        db.add_all([vax1, vax2])

        # Add behavior logs
        now = datetime.now(timezone.utc)
        logs = [
            BehaviorLog(pet_id=pet.id, category=BehaviorCategory.EATING, value="2 cups", notes="Good appetite", logged_at=now - timedelta(hours=2)),
            BehaviorLog(pet_id=pet.id, category=BehaviorCategory.ACTIVITY, value="45 min walk", notes="Energetic", logged_at=now - timedelta(hours=4)),
            BehaviorLog(pet_id=pet.id, category=BehaviorCategory.SLEEP, value="8 hours", notes="Slept through the night", logged_at=now - timedelta(hours=10)),
            BehaviorLog(pet_id=pet.id, category=BehaviorCategory.MOOD, value="Happy", notes="Playful and social", logged_at=now - timedelta(days=1)),
            BehaviorLog(pet_id=pet.id, category=BehaviorCategory.BATHROOM, value="Normal", notes="Regular schedule", logged_at=now - timedelta(days=1, hours=3)),
        ]
        db.add_all(logs)

        await db.commit()
        print("[SUCCESS] Demo data seeded successfully!")
        print(f"   User: demo@havenpet.com / password123")
        print(f"   Pet: {pet.name} (ID: {pet.id})")


if __name__ == "__main__":
    asyncio.run(seed())
