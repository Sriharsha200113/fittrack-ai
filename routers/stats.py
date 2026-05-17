from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from backend.db.session import get_db
from backend.services.leaderboard_service import get_daily_leaderboard, get_weekly_leaderboard
from backend.services.streak_service import get_streak
from backend.services.badge_service import get_user_badges

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/leaderboard/daily/{squad_id}")
async def daily_leaderboard(squad_id: str, db: AsyncSession = Depends(get_db)):
    return await get_daily_leaderboard(squad_id, date.today(), db)


@router.get("/leaderboard/weekly/{squad_id}")
async def weekly_leaderboard(squad_id: str, db: AsyncSession = Depends(get_db)):
    return await get_weekly_leaderboard(squad_id, date.today(), db)


@router.get("/streak/{user_id}")
async def user_streak(user_id: str):
    return await get_streak(user_id)


@router.get("/badges/{user_id}")
async def user_badges(user_id: str, db: AsyncSession = Depends(get_db)):
    return await get_user_badges(user_id, db)
