from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.session import get_db
from backend.core.deps import get_current_user
from backend.models.db_models import User, UserGoals, UserBadge
from backend.services.streak_service import get_streak
from backend.services.badge_service import BADGES

router = APIRouter(prefix="/profile", tags=["profile"])


class GoalsUpdate(BaseModel):
    daily_calories: Optional[int] = None
    protein_g: Optional[int] = None
    carbs_g: Optional[int] = None
    fat_g: Optional[int] = None
    goal_type: Optional[str] = None
    target_weight_kg: Optional[float] = None
    activity_level: Optional[str] = None


class NameUpdate(BaseModel):
    name: str


@router.get("/")
async def get_profile(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    goals_result = await db.execute(select(UserGoals).where(UserGoals.user_id == current_user.id))
    goals = goals_result.scalar_one_or_none()

    badges_result = await db.execute(select(UserBadge).where(UserBadge.user_id == current_user.id))
    user_badges = badges_result.scalars().all()

    streak = await get_streak(str(current_user.id))

    return {
        "id": str(current_user.id),
        "name": current_user.name,
        "phone": current_user.phone,
        "created_at": current_user.created_at.isoformat(),
        "streak": streak.get("current_streak", 0),
        "longest_streak": streak.get("longest_streak", 0),
        "goals": {
            "daily_calories": goals.daily_calories if goals else 2000,
            "protein_g": goals.protein_g if goals else 150,
            "carbs_g": goals.carbs_g if goals else None,
            "fat_g": goals.fat_g if goals else None,
            "goal_type": goals.goal_type if goals else "maintain",
            "target_weight_kg": goals.target_weight_kg if goals else None,
            "activity_level": goals.activity_level if goals else "moderate",
        } if goals else None,
        "badges": [
            {
                "slug": b.badge_slug,
                "emoji": BADGES.get(b.badge_slug, {}).get("emoji", ""),
                "label": BADGES.get(b.badge_slug, {}).get("label", b.badge_slug),
                "earned_at": b.earned_at.isoformat(),
            }
            for b in user_badges
        ],
    }


@router.patch("/goals")
async def update_goals(body: GoalsUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    goals_result = await db.execute(select(UserGoals).where(UserGoals.user_id == current_user.id))
    goals = goals_result.scalar_one_or_none()
    if not goals:
        goals = UserGoals(user_id=current_user.id)
        db.add(goals)

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(goals, field, value)

    await db.commit()
    return {"message": "Goals updated"}


@router.patch("/name")
async def update_name(body: NameUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    current_user.name = body.name
    await db.commit()
    return {"id": str(current_user.id), "name": current_user.name}
