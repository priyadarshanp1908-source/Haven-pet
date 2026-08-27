"""Recommendation routes — get/generate AI care recommendations for a pet."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.recommendation import RecommendationOut
from app.models.recommendation import Recommendation
from app.models.user import User
from app.services.pet_service import _get_pet_or_404, _check_ownership
from app.agents.recommendation_agent import RecommendationAgent

router = APIRouter()
_recommendation_agent = RecommendationAgent()


@router.get("/pets/{pet_id}/recommendations", response_model=List[RecommendationOut])
async def get_recommendations(
    pet_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get existing recommendations for a pet."""
    pet = await _get_pet_or_404(pet_id, db)
    _check_ownership(pet, current_user)

    result = await db.execute(
        select(Recommendation)
        .where(Recommendation.pet_id == pet_id)
        .order_by(Recommendation.created_at.desc())
        .limit(10)
    )
    return list(result.scalars().all())


@router.post("/pets/{pet_id}/recommendations", response_model=RecommendationOut, status_code=201)
async def generate_recommendation(
    pet_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new AI recommendation for a pet."""
    pet = await _get_pet_or_404(pet_id, db)
    _check_ownership(pet, current_user)

    await _recommendation_agent.run(
        message="Generate personalized recommendations",
        user_id=current_user.id,
        pet_id=pet_id,
        db=db,
    )

    # Return the latest recommendation
    result = await db.execute(
        select(Recommendation)
        .where(Recommendation.pet_id == pet_id)
        .order_by(Recommendation.created_at.desc())
        .limit(1)
    )
    return result.scalar_one()
