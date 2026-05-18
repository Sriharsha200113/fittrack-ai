from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.models.db_models import UserBadge, User, DailyPoints, ExerciseLog
from backend.services.redis_service import get_redis

BADGES = {
    "streak_3": {"emoji": "🔥", "label": "On Fire", "description": "3-day streak"},
    "streak_7": {"emoji": "⚡", "label": "Week Warrior", "description": "7-day streak"},
    "streak_30": {"emoji": "💎", "label": "Diamond Streak", "description": "30-day streak"},
    "diet_champion": {"emoji": "🥗", "label": "Diet Champion", "description": "Protein target 7 days straight"},
    "workout_beast": {"emoji": "💪", "label": "Workout Beast", "description": "5 workouts in a week"},
    "weekly_winner": {"emoji": "🏆", "label": "Weekly Champion", "description": "Top of squad for a week"},
}


async def check_and_award_badges(
    user: User,
    current_streak: int,
    db: AsyncSession,
) -> list[dict]:
    """Check all badge conditions and award any newly earned badges. Returns list of new badges."""
    new_badges = []

    for slug in ("streak_3", "streak_7", "streak_30"):
        threshold = int(slug.split("_")[1])
        if current_streak >= threshold:
            awarded = await _award_badge_if_new(user.id, slug, db)
            if awarded:
                new_badges.append({**BADGES[slug], "slug": slug})

    protein_streak = await _count_protein_streak(user.id, db)
    if protein_streak >= 7:
        awarded = await _award_badge_if_new(user.id, "diet_champion", db)
        if awarded:
            new_badges.append({**BADGES["diet_champion"], "slug": "diet_champion"})

    workouts_this_week = await _count_workouts_this_week(user.id, db)
    if workouts_this_week >= 5:
        awarded = await _award_badge_if_new(user.id, "workout_beast", db)
        if awarded:
            new_badges.append({**BADGES["workout_beast"], "slug": "workout_beast"})

    if new_badges:
        r = await get_redis()
        for badge in new_badges:
            await r.sadd(f"badges:{user.id}", badge["slug"])

    return new_badges


async def get_user_badges(user_id: str, db: AsyncSession) -> list[dict]:
    """Get all badges for a user."""
    result = await db.execute(
        select(UserBadge).where(UserBadge.user_id == user_id)
    )
    rows = result.scalars().all()
    return [
        {**BADGES[row.badge_slug], "slug": row.badge_slug, "earned_at": row.earned_at}
        for row in rows
        if row.badge_slug in BADGES
    ]


async def _award_badge_if_new(user_id, slug: str, db: AsyncSession) -> bool:
    result = await db.execute(
        select(UserBadge).where(UserBadge.user_id == user_id, UserBadge.badge_slug == slug)
    )
    if not result.scalar_one_or_none():
        db.add(UserBadge(user_id=user_id, badge_slug=slug))
        await db.commit()
        return True
    return False


async def _count_protein_streak(user_id, db: AsyncSession) -> int:
    """Count consecutive days where protein_hit = True in daily_points."""
    today = date.today()
    streak = 0
    check_date = today
    while True:
        result = await db.execute(
            select(DailyPoints).where(
                DailyPoints.user_id == user_id,
                DailyPoints.date == check_date,
                DailyPoints.protein_hit == True,
            )
        )
        if not result.scalars().first():
            break
        streak += 1
        check_date -= timedelta(days=1)
    return streak


async def _count_workouts_this_week(user_id, db: AsyncSession) -> int:
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    result = await db.execute(
        select(func.count(ExerciseLog.id)).where(
            ExerciseLog.user_id == user_id,
            ExerciseLog.log_date >= week_start,
            ExerciseLog.log_date <= today,
        )
    )
    return result.scalar() or 0
