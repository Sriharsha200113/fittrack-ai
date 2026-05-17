from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.models.db_models import (
    User, MealLog, ExerciseLog, DailyPoints,
    UserGoals, BodyMetrics, WeeklySnapshot, UserBadge,
)
from backend.services.streak_service import get_streak
from backend.services.badge_service import BADGES


async def get_weekly_report_data(user: User, db: AsyncSession) -> dict:
    """Compile all data needed for a weekly report."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)

    pts_result = await db.execute(
        select(DailyPoints).where(
            DailyPoints.user_id == user.id,
            DailyPoints.date >= week_start,
            DailyPoints.date <= today,
        )
    )
    daily_pts = pts_result.scalars().all()

    total_points = sum(dp.points for dp in daily_pts)
    active_days = len([dp for dp in daily_pts if dp.meals_logged > 0 or dp.workouts_logged > 0])
    workout_days = len([dp for dp in daily_pts if dp.workouts_logged > 0])
    protein_hit_days = len([dp for dp in daily_pts if dp.protein_hit])
    calorie_hit_days = len([dp for dp in daily_pts if dp.calorie_target_hit])

    # Sum macros per day, then average those daily totals
    daily_macro_sq = (
        select(
            func.sum(MealLog.calories).label("day_cal"),
            func.sum(MealLog.protein_g).label("day_p"),
            func.sum(MealLog.carbs_g).label("day_c"),
            func.sum(MealLog.fat_g).label("day_f"),
            func.count(MealLog.id).label("day_meals"),
        ).where(
            MealLog.user_id == user.id,
            MealLog.log_date >= week_start,
            MealLog.log_date <= today,
        ).group_by(MealLog.log_date)
        .subquery()
    )
    macro_result = await db.execute(
        select(
            func.avg(daily_macro_sq.c.day_cal),
            func.avg(daily_macro_sq.c.day_p),
            func.avg(daily_macro_sq.c.day_c),
            func.avg(daily_macro_sq.c.day_f),
            func.sum(daily_macro_sq.c.day_meals),
        )
    )
    avg_cal, avg_p, avg_c, avg_f, meal_count = macro_result.one()

    # Fetch individual meal logs for the week
    meal_logs_result = await db.execute(
        select(MealLog).where(
            MealLog.user_id == user.id,
            MealLog.log_date >= week_start,
            MealLog.log_date <= today,
        ).order_by(MealLog.log_date, MealLog.logged_at)
    )
    meal_logs = meal_logs_result.scalars().all()

    # Fetch individual exercise logs for the week
    exercise_logs_result = await db.execute(
        select(ExerciseLog).where(
            ExerciseLog.user_id == user.id,
            ExerciseLog.log_date >= week_start,
            ExerciseLog.log_date <= today,
        ).order_by(ExerciseLog.log_date, ExerciseLog.logged_at)
    )
    exercise_logs = exercise_logs_result.scalars().all()

    weight_result = await db.execute(
        select(BodyMetrics.weight_kg, BodyMetrics.log_date).where(
            BodyMetrics.user_id == user.id,
            BodyMetrics.log_date >= week_start,
            BodyMetrics.log_date <= today,
            BodyMetrics.weight_kg.isnot(None),
        ).order_by(BodyMetrics.log_date)
    )
    weight_logs = weight_result.all()

    goal_result = await db.execute(select(UserGoals).where(UserGoals.user_id == user.id))
    goals = goal_result.scalar_one_or_none()

    streak = await get_streak(str(user.id))

    badge_result = await db.execute(
        select(UserBadge).where(
            UserBadge.user_id == user.id,
            UserBadge.earned_at >= week_start,
        )
    )
    new_badges = badge_result.scalars().all()

    # Group meals by date
    meals_by_date: dict = {}
    for m in meal_logs:
        key = str(m.log_date)
        if key not in meals_by_date:
            meals_by_date[key] = []
        label = m.meal_type.capitalize() if m.meal_type else "Meal"
        meals_by_date[key].append({
            "label": label,
            "name": m.raw_text[:60],
            "calories": round(m.calories or 0),
            "protein": round(m.protein_g or 0),
        })

    # Group exercises by date
    exercises_by_date: dict = {}
    for e in exercise_logs:
        key = str(e.log_date)
        if key not in exercises_by_date:
            exercises_by_date[key] = []
        parts = [e.workout_type.capitalize() if e.workout_type else "Workout"]
        if e.duration_min:
            parts.append(f"{e.duration_min} min")
        if e.calories_burned:
            parts.append(f"~{round(e.calories_burned)} kcal burned")
        exercises_by_date[key].append(" · ".join(parts))

    return {
        "user_name": user.name,
        "week_start": week_start,
        "week_end": week_end,
        "total_points": total_points,
        "active_days": active_days,
        "workout_days": workout_days,
        "protein_hit_days": protein_hit_days,
        "calorie_hit_days": calorie_hit_days,
        "avg_calories": round(avg_cal or 0),
        "avg_protein": round(avg_p or 0),
        "avg_carbs": round(avg_c or 0),
        "avg_fat": round(avg_f or 0),
        "meal_count": meal_count or 0,
        "meals_by_date": meals_by_date,
        "exercises_by_date": exercises_by_date,
        "weight_logs": [{"date": str(w.log_date), "weight": w.weight_kg} for w in weight_logs],
        "goals": {
            "daily_calories": goals.daily_calories if goals else 2000,
            "protein_g": goals.protein_g if goals else 150,
            "goal_type": goals.goal_type if goals else "maintain",
        },
        "current_streak": streak["current_streak"],
        "longest_streak": streak["longest_streak"],
        "new_badges": [
            {**BADGES[b.badge_slug], "slug": b.badge_slug}
            for b in new_badges if b.badge_slug in BADGES
        ],
    }


async def get_monthly_report_data(user: User, db: AsyncSession) -> dict:
    """Compile all data needed for a monthly report."""
    today = date.today()
    month_start = today.replace(day=1)

    pts_result = await db.execute(
        select(DailyPoints).where(
            DailyPoints.user_id == user.id,
            DailyPoints.date >= month_start,
            DailyPoints.date <= today,
        ).order_by(DailyPoints.date)
    )
    daily_pts = pts_result.scalars().all()

    total_points = sum(dp.points for dp in daily_pts)
    active_days = len([dp for dp in daily_pts if dp.meals_logged > 0 or dp.workouts_logged > 0])
    total_workout_days = sum(1 for dp in daily_pts if dp.workouts_logged > 0)
    best_day_pts = max((dp.points for dp in daily_pts), default=0)

    macro_result = await db.execute(
        select(
            func.avg(MealLog.calories),
            func.avg(MealLog.protein_g),
            func.avg(MealLog.carbs_g),
            func.avg(MealLog.fat_g),
            func.count(MealLog.id),
        ).where(
            MealLog.user_id == user.id,
            MealLog.log_date >= month_start,
            MealLog.log_date <= today,
        )
    )
    avg_cal, avg_p, avg_c, avg_f, total_meals = macro_result.one()

    weight_result = await db.execute(
        select(BodyMetrics.weight_kg, BodyMetrics.log_date).where(
            BodyMetrics.user_id == user.id,
            BodyMetrics.log_date >= month_start,
            BodyMetrics.log_date <= today,
            BodyMetrics.weight_kg.isnot(None),
        ).order_by(BodyMetrics.log_date)
    )
    weight_logs = weight_result.all()

    first_weight = weight_logs[0].weight_kg if weight_logs else None
    last_weight = weight_logs[-1].weight_kg if weight_logs else None
    weight_change = round(last_weight - first_weight, 1) if first_weight and last_weight else None

    snapshot_result = await db.execute(
        select(WeeklySnapshot).where(WeeklySnapshot.week_start >= month_start)
    )
    weekly_snapshots = snapshot_result.scalars().all()

    goal_result = await db.execute(select(UserGoals).where(UserGoals.user_id == user.id))
    goals = goal_result.scalar_one_or_none()

    streak = await get_streak(str(user.id))

    badge_result = await db.execute(
        select(UserBadge).where(UserBadge.user_id == user.id)
    )
    all_badges = badge_result.scalars().all()

    return {
        "user_name": user.name,
        "month": today.strftime("%B %Y"),
        "month_start": month_start,
        "today": today,
        "total_points": total_points,
        "active_days": active_days,
        "total_days": (today - month_start).days + 1,
        "total_workout_days": total_workout_days,
        "best_day_pts": best_day_pts,
        "avg_calories": round(avg_cal or 0),
        "avg_protein": round(avg_p or 0),
        "avg_carbs": round(avg_c or 0),
        "avg_fat": round(avg_f or 0),
        "total_meals": total_meals or 0,
        "weight_logs": [{"date": str(w.log_date), "weight": w.weight_kg} for w in weight_logs],
        "first_weight": first_weight,
        "last_weight": last_weight,
        "weight_change": weight_change,
        "weekly_snapshots": [
            {
                "week_start": str(s.week_start),
                "week_end": str(s.week_end),
                "rankings": s.rankings,
            }
            for s in weekly_snapshots
        ],
        "goals": {
            "daily_calories": goals.daily_calories if goals else 2000,
            "protein_g": goals.protein_g if goals else 150,
            "goal_type": goals.goal_type if goals else "maintain",
            "target_weight_kg": goals.target_weight_kg if goals else None,
        },
        "current_streak": streak["current_streak"],
        "longest_streak": streak["longest_streak"],
        "all_badges": [
            {**BADGES[b.badge_slug], "slug": b.badge_slug}
            for b in all_badges if b.badge_slug in BADGES
        ],
    }


def format_weekly_report_text(data: dict) -> str:
    """Format weekly report as WhatsApp-friendly text."""
    from datetime import date as date_type
    goal_emoji = {
        "fat_loss": "🔥", "muscle_gain": "💪",
        "recomp": "⚖️", "maintain": "🎯",
        "lose": "🔥", "gain": "💪", "strength": "🏋️",
        "endurance": "🚴", "health": "❤️",
    }
    g = data["goals"]
    emoji = goal_emoji.get(g["goal_type"], "🎯")
    week_start = data["week_start"]
    week_end = data["week_end"]
    week_label = f"{week_start.strftime('%b %d')} – {week_end.strftime('%b %d')}"

    # Aggregate all exercises across the week for the summary
    all_exercises = []
    total_cal_burned = 0
    for ex_list in data.get("exercises_by_date", {}).values():
        for ex in ex_list:
            all_exercises.append(ex)
    # Re-derive total calories burned from exercises_by_date raw data isn't available,
    # so we'll just list unique workout types done this week
    exercise_summary_lines = [f"  • {ex}" for ex in all_exercises]

    lines = [
        f"📊 *{data['user_name']}'s Weekly Report*",
        f"📅 {week_label} {emoji}\n",
        f"*Activity*",
        f"✅ Active days: {data['active_days']}/7",
        f"🏋️ Workout days: {data['workout_days']}",
    ]
    lines.extend(exercise_summary_lines)
    lines += [
        f"⭐ Total points: {data['total_points']}\n",
        f"*Nutrition (daily averages)*",
        f"🍽️ Calories: {data['avg_calories']} / {g['daily_calories']} kcal",
        f"💪 Protein: {data['avg_protein']}g / {g['protein_g']}g",
        f"🎯 Protein target hit: {data['protein_hit_days']}/7 days",
        f"🎯 Calorie target hit: {data['calorie_hit_days']}/7 days\n",
    ]

    # Per-day meals and workouts
    today = date_type.today()
    day = week_start
    day_lines = []
    while day <= min(week_end, today):
        key = str(day)
        day_meals = data.get("meals_by_date", {}).get(key, [])
        day_exercises = data.get("exercises_by_date", {}).get(key, [])
        if day_meals or day_exercises:
            day_lines.append(f"*{day.strftime('%a %b %d')}*")
            for m in day_meals:
                day_lines.append(f"  🍽️ {m['label']}: {m['name']} ({m['calories']} kcal, {m['protein']}g protein)")
            for ex in day_exercises:
                day_lines.append(f"  🏋️ {ex}")
        day = day + timedelta(days=1)

    if day_lines:
        lines.append("*Daily Log*")
        lines.extend(day_lines)
        lines.append("")

    if data["weight_logs"]:
        weights = [w["weight"] for w in data["weight_logs"]]
        lines.append("*Weight*")
        lines.append(f"⚖️ {min(weights)} – {max(weights)} kg this week")
        lines.append("")

    lines.append(f"🔥 Current streak: {data['current_streak']} days")
    lines.append(f"🏆 Longest streak: {data['longest_streak']} days\n")

    if data["new_badges"]:
        badge_str = "  ".join([f"{b['emoji']} {b['label']}" for b in data["new_badges"]])
        lines.append(f"🏅 New badges: {badge_str}\n")

    lines.append("Keep pushing! 🚀")
    lines.append("\n📱 View full dashboard: https://web-eight-sepia-22.vercel.app")
    return "\n".join(lines)
