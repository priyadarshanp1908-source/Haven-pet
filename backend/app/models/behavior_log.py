"""BehaviorLog model — daily routine and behavior entries for pets."""

import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class BehaviorCategory(str, enum.Enum):
    EATING = "eating"
    SLEEP = "sleep"
    ACTIVITY = "activity"
    MOOD = "mood"
    BATHROOM = "bathroom"
    OTHER = "other"


class BehaviorLog(Base):
    __tablename__ = "behavior_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    pet_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    category: Mapped[str] = mapped_column(
        SAEnum(BehaviorCategory), nullable=False
    )
    value: Mapped[str | None] = mapped_column(String(200), nullable=True)  # e.g. "good", "3 cups", "30 min"
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    flagged_anomaly: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    pet = relationship("Pet", back_populates="behavior_logs")
