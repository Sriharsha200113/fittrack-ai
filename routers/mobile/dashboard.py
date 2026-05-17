from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.db.session import get_db
from backend.core.deps import get_current_user
from backend.models.db_models import User, DailyPoints, MealLog, ExerciseLog
from backend.services.streak_service import get_streak

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/today")
async def get_today(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    today = date.today()

    dp_result = await db.execute(
        select(DailyPoints).where(DailyPoints.user_id == current_user.id, DailyPoints.date == today)
    )
    dp = dp_result.scalar_one_or_none()

    meals_result = await db.execute(
        select(MealLog).where(MealLog.user_id == current_user.id, MealLog.log_date == today)
    )
    meals = meals_result.scalars().all()

    workouts_result = await db.execute(
        select(ExerciseLog).where(ExerciseLog.user_id == current_user.id, ExerciseLog.log_date == today)
    )
    workouts = workouts_result.scalars().all()

    streak = await get_streak(str(current_user.id))

    return {
        "date": today.isoformat(),
        "points": dp.points if dp else 0,
        "meals_logged": dp.meals_logged if dp else 0,
        "workouts_logged": dp.workouts_logged if dp else 0,
        "protein_hit": dp.protein_hit if dp else False,
        "calorie_target_hit": dp.calorie_target_hit if dp else False,
        "weight_logged": dp.weight_logged if dp else False,
        "streak": streak.get("current_streak", 0),
        "recent_meals": [{"food": m.raw_text, "calories": m.calories, "protein_g": m.protein_g} for m in meals],
        "recent_workouts": [{"activity": w.raw_text, "duration_min": w.duration_min} for w in workouts],
    }


@router.get("/weekly-chart")
async def get_weekly_chart(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    today = date.today()
    week_start = today - timedelta(days=6)

    result = await db.execute(
        select(DailyPoints).where(
            DailyPoints.user_id == current_user.id,
            DailyPoints.date >= week_start,
            DailyPoints.date <= today,
        )
    )
    rows = {dp.date: dp for dp in result.scalars().all()}

    chart = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        dp = rows.get(d)
        chart.append({
            "date": d.isoformat(),
            "points": dp.points if dp else 0,
            "meals": dp.meals_logged if dp else 0,
            "workouts": dp.workouts_logged if dp else 0,
        })

    return {"chart": chart}
