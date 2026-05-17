from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.db_models import DailyPoints, User, Squad
from backend.services.leaderboard_service import add_points, get_user_rank
from backend.services.streak_service import update_streak
from backend.services.badge_service import check_and_award_badges

POINTS = {
    "meal": 20,
    "workout": 25,
    "protein_hit": 15,
    "calorie_hit": 15,
    "weight_logged": 5,
}


async def award_points(
    event: str,
    user: User,
    squad: Squad,
    db: AsyncSession,
) -> dict:
    """
    Award points for a given event.
    Returns dict with: points_awarded, total_points, streak, rank, new_badges, streak_bonus, is_streak_milestone
    event: "meal" | "workout" | "weight_logged" | "protein_hit" | "calorie_hit"
    """
    today = date.today()
    pts = POINTS.get(event, 0)

    result = await db.execute(
        select(DailyPoints).where(
            DailyPoints.user_id == user.id,
            DailyPoints.squad_id == squad.id,
            DailyPoints.date == today,
        )
    )
    dp = result.scalar_one_or_none()
    if not dp:
        dp = DailyPoints(user_id=user.id, squad_id=squad.id, date=today,
                         points=0, meals_logged=0, workouts_logged=0)
        db.add(dp)

    # Ensure columns are never None (guard against missing DB defaults)
    dp.points = dp.points or 0
    dp.meals_logged = dp.meals_logged or 0
    dp.workouts_logged = dp.workouts_logged or 0

    # Guard against double-awarding idempotent events
    if event == "weight_logged" and dp.weight_logged:
        pts = 0
    elif event == "protein_hit" and dp.protein_hit:
        pts = 0
    elif event == "calorie_hit" and dp.calorie_target_hit:
        pts = 0
    else:
        if event == "meal":
            dp.meals_logged += 1
        elif event == "workout":
            dp.workouts_logged += 1
        elif event == "weight_logged":
            dp.weight_logged = True
        elif event == "protein_hit":
            dp.protein_hit = True
        elif event == "calorie_hit":
            dp.calorie_target_hit = True

    dp.points += pts
    await db.commit()
    await db.refresh(dp)

    new_total = await add_points(
        squad_id=str(squad.id),
        user_id=str(user.id),
        user_name=user.name or user.phone,
        points=pts,
        for_date=today,
    )

    # update_streak returns (streak, bonus, milestone); bonus=0 if already updated today
    current_streak, streak_bonus, is_milestone = await update_streak(user, db)

    # Award streak bonus only on the first activity of the day
    if streak_bonus > 0 and dp.meals_logged + dp.workouts_logged == 1:
        dp.points += streak_bonus
        await db.commit()
        new_total = await add_points(
            squad_id=str(squad.id),
            user_id=str(user.id),
            user_name=user.name or user.phone,
            points=streak_bonus,
            for_date=today,
        )
    else:
        streak_bonus = 0

    new_badges = await check_and_award_badges(user, current_streak, db)
    rank = await get_user_rank(str(squad.id), str(user.id), today)

    return {
        "points_awarded": pts,
        "streak_bonus": streak_bonus,
        "total_points": new_total,
        "current_streak": current_streak,
        "rank": rank,
        "new_badges": new_badges,
        "is_streak_milestone": is_milestone,
    }
