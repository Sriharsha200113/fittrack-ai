from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.session import get_db
from backend.core.deps import get_current_user
from backend.models.db_models import User, MealLog, ExerciseLog, BodyMetrics

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/meals")
async def get_meals(
    days: int = Query(default=7, le=30),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    since = date.today() - timedelta(days=days - 1)
    result = await db.execute(
        select(MealLog)
        .where(MealLog.user_id == current_user.id, MealLog.log_date >= since)
        .order_by(MealLog.logged_at.desc())
    )
    meals = result.scalars().all()
    return {
        "meals": [
            {
                "id": str(m.id),
                "date": m.log_date.isoformat(),
                "meal_type": m.meal_type,
                "food": m.raw_text,
                "calories": m.calories,
                "protein_g": m.protein_g,
                "carbs_g": m.carbs_g,
                "fat_g": m.fat_g,
            }
            for m in meals
        ]
    }


@router.get("/workouts")
async def get_workouts(
    days: int = Query(default=7, le=30),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    since = date.today() - timedelta(days=days - 1)
    result = await db.execute(
        select(ExerciseLog)
        .where(ExerciseLog.user_id == current_user.id, ExerciseLog.log_date >= since)
        .order_by(ExerciseLog.logged_at.desc())
    )
    workouts = result.scalars().all()
    return {
        "workouts": [
            {
                "id": str(w.id),
                "date": w.log_date.isoformat(),
                "workout_type": w.workout_type,
                "description": w.raw_text,
                "duration_min": w.duration_min,
                "calories_burned": w.calories_burned,
            }
            for w in workouts
        ]
    }


@router.get("/body-metrics")
async def get_body_metrics(
    days: int = Query(default=30, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    since = date.today() - timedelta(days=days - 1)
    result = await db.execute(
        select(BodyMetrics)
        .where(BodyMetrics.user_id == current_user.id, BodyMetrics.log_date >= since)
        .order_by(BodyMetrics.log_date.desc())
    )
    metrics = result.scalars().all()
    return {
        "body_metrics": [
            {
                "id": str(m.id),
                "date": m.log_date.isoformat(),
                "weight_kg": m.weight_kg,
                "body_fat_pct": m.body_fat_pct,
                "muscle_mass_kg": m.muscle_mass_kg,
                "waist_cm": m.waist_cm,
            }
            for m in metrics
        ]
    }
