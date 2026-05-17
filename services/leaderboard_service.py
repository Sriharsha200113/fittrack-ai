from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.services.redis_service import get_redis
from backend.models.db_models import User, DailyPoints

LEADERBOARD_TTL = 48 * 3600
WEEKLY_TTL = 8 * 24 * 3600


def _daily_key(squad_id: str, for_date: date) -> str:
    return f"leaderboard:{squad_id}:{for_date.isoformat()}"


def _weekly_key(squad_id: str, for_date: date) -> str:
    year, week, _ = for_date.isocalendar()
    return f"leaderboard_weekly:{squad_id}:{year}-{week:02d}"


def _name_key(user_id: str) -> str:
    return f"user_name:{user_id}"


async def add_points(
    squad_id: str,
    user_id: str,
    user_name: str,
    points: int,
    for_date: date,
) -> int:
    """Add points to Redis leaderboard. Returns new total score."""
    r = await get_redis()
    daily_key = _daily_key(squad_id, for_date)
    weekly_key = _weekly_key(squad_id, for_date)

    new_score = await r.zincrby(daily_key, points, user_id)
    await r.zincrby(weekly_key, points, user_id)

    await r.expire(daily_key, LEADERBOARD_TTL)
    await r.expire(weekly_key, WEEKLY_TTL)

    await r.set(_name_key(user_id), user_name, ex=86400)

    return int(new_score)


async def get_daily_leaderboard(
    squad_id: str,
    for_date: date,
    db: AsyncSession,
) -> list[dict]:
    """Returns sorted leaderboard for today. Falls back to DB if Redis miss."""
    r = await get_redis()
    key = _daily_key(squad_id, for_date)

    entries = await r.zrevrange(key, 0, -1, withscores=True)

    if not entries:
        return await _load_from_db_daily(squad_id, for_date, db)

    result = []
    for user_id, score in entries:
        name = await r.get(_name_key(user_id)) or user_id
        result.append({"user_id": user_id, "user_name": name, "points": int(score)})

    return result


async def get_weekly_leaderboard(
    squad_id: str,
    for_date: date,
    db: AsyncSession,
) -> list[dict]:
    """Returns sorted weekly leaderboard."""
    r = await get_redis()
    key = _weekly_key(squad_id, for_date)
    entries = await r.zrevrange(key, 0, -1, withscores=True)

    result = []
    for user_id, score in entries:
        name = await r.get(_name_key(user_id)) or user_id
        result.append({"user_id": user_id, "user_name": name, "points": int(score)})

    return result


async def get_user_rank(squad_id: str, user_id: str, for_date: date) -> int:
    """Returns 1-based rank of user in daily leaderboard."""
    r = await get_redis()
    key = _daily_key(squad_id, for_date)
    rank = await r.zrevrank(key, user_id)
    return (rank + 1) if rank is not None else 999


async def _load_from_db_daily(squad_id: str, for_date: date, db: AsyncSession) -> list[dict]:
    """Load daily points from DB into Redis (cache warm-up)."""
    result = await db.execute(
        select(DailyPoints, User)
        .join(User, DailyPoints.user_id == User.id)
        .where(DailyPoints.squad_id == squad_id, DailyPoints.date == for_date)
        .order_by(DailyPoints.points.desc())
    )
    rows = result.all()

    r = await get_redis()
    key = _daily_key(squad_id, for_date)

    leaderboard = []
    for dp, user in rows:
        await r.zadd(key, {str(user.id): dp.points})
        await r.set(_name_key(str(user.id)), user.name or user.phone, ex=86400)
        leaderboard.append({
            "user_id": str(user.id),
            "user_name": user.name or user.phone,
            "points": dp.points,
        })

    if leaderboard:
        await r.expire(key, LEADERBOARD_TTL)

    return leaderboard
