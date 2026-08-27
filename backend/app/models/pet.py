"""Pet model — pet profiles owned by users."""

import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, DateTime, Date, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    species: Mapped[str] = mapped_column(String(50), nullable=False)  # dog, cat, bird, etc.
    breed: Mapped[str] = mapped_column(String(100), nullable=True)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    medical_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    owner = relationship("User", back_populates="pets")
    vaccinations = relationship("Vaccination", back_populates="pet", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="pet", cascade="all, delete-orphan")
    behavior_logs = relationship("BehaviorLog", back_populates="pet", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="pet", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="pet", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="pet", cascade="all, delete-orphan")
