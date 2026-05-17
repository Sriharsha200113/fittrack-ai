from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.db_models import UserStreak, User
from backend.services.redis_service import get_redis

STREAK_BONUS_PER_DAY = 2
STREAK_BONUS_CAP = 50


async def update_streak(user: User, db: AsyncSession) -> tuple[int, int, bool]:
    """
    Updates streak for user based on today's activity.
    Returns (current_streak, bonus_points, is_new_milestone).
    Call once per day after any activity (meal or workout logged).
    """
    today = date.today()

    result = await db.execute(select(UserStreak).where(UserStreak.user_id == user.id))
    streak_row = result.scalar_one_or_none()

    if not streak_row:
        streak_row = UserStreak(user_id=user.id, current_streak=0, longest_streak=0)
        db.add(streak_row)

    # Guard against NULL columns from missing DB defaults
    streak_row.current_streak = streak_row.current_streak or 0
    streak_row.longest_streak = streak_row.longest_streak or 0

    last_active = streak_row.last_active_date

    if last_active == today:
        return streak_row.current_streak, 0, False

    if last_active == today - timedelta(days=1):
        streak_row.current_streak += 1
    else:
        streak_row.current_streak = 1

    streak_row.last_active_date = today

    if streak_row.current_streak > streak_row.longest_streak:
        streak_row.longest_streak = streak_row.current_streak

    await db.commit()
    await db.refresh(streak_row)

    r = await get_redis()
    await r.hset(f"streak:{user.id}", mapping={
        "current_streak": streak_row.current_streak,
        "longest_streak": streak_row.longest_streak,
        "last_active_date": today.isoformat(),
    })

    bonus = min(streak_row.current_streak * STREAK_BONUS_PER_DAY, STREAK_BONUS_CAP)
    is_milestone = streak_row.current_streak in (3, 7, 14, 30, 60, 100)

    return streak_row.current_streak, bonus, is_milestone


async def get_streak(user_id: str) -> dict:
    """Get streak data from Redis (fast path)."""
    r = await get_redis()
    data = await r.hgetall(f"streak:{user_id}")
    return {
        "current_streak": int(data.get("current_streak", 0)),
        "longest_streak": int(data.get("longest_streak", 0)),
        "last_active_date": data.get("last_active_date"),
    }
