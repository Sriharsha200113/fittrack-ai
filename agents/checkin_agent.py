from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.models.db_models import MealLog, ExerciseLog, DailyPoints, UserGoals, User, Squad

MORNING_KEYWORDS = {"morning", "gm", "good morning", "rise", "wake", "checking in", "start"}


async def handle_checkin(message: str, user: User, squad: Squad, db: AsyncSession) -> str:
    msg_lower = message.lower()
    is_morning = any(kw in msg_lower for kw in MORNING_KEYWORDS)

    if is_morning:
        return await _morning_checkin(user, db)
    else:
        return await _evening_checkin(user, db)


async def _morning_checkin(user: User, db: AsyncSession) -> str:
    goal_result = await db.execute(select(UserGoals).where(UserGoals.user_id == user.id))
    goals = goal_result.scalar_one_or_none()

    cal_target = goals.daily_calories if goals else 2000
    protein_target = goals.protein_g if goals else 150
    goal_type = goals.goal_type if goals else "maintain"

    goal_emoji = {"fat_loss": "🔥", "muscle_gain": "💪", "recomp": "⚖️", "maintain": "🎯"}
    emoji = goal_emoji.get(goal_type, "🎯")

    return (
        f"Good morning {user.name}! {emoji}\n\n"
        f"Today's targets:\n"
        f"🍽️ Calories: {cal_target} kcal\n"
        f"💪 Protein: {protein_target}g\n\n"
        f"Log your meals and workouts here throughout the day.\n"
        f"Type *stats* anytime to check your progress 📊"
    )


async def _evening_checkin(user: User, db: AsyncSession) -> str:
    today = date.today()

    macro_result = await db.execute(
        select(func.sum(MealLog.calories), func.sum(MealLog.protein_g)).where(
            MealLog.user_id == user.id,
            MealLog.log_date == today,
        )
    )
    cal, protein = macro_result.one()
    cal = round(cal or 0)
    protein = round(protein or 0)

    workout_result = await db.execute(
        select(func.count(ExerciseLog.id)).where(
            ExerciseLog.user_id == user.id,
            ExerciseLog.log_date == today,
        )
    )
    workout_count = workout_result.scalar() or 0

    goal_result = await db.execute(select(UserGoals).where(UserGoals.user_id == user.id))
    goals = goal_result.scalar_one_or_none()
    cal_target = goals.daily_calories if goals else 2000
    protein_target = goals.protein_g if goals else 150

    cal_pct = round((cal / cal_target) * 100) if cal_target else 0
    protein_pct = round((protein / protein_target) * 100) if protein_target else 0

    workout_icon = "✅" if workout_count > 0 else "❌"
    cal_icon = "✅" if 90 <= cal_pct <= 110 else ("⚠️" if cal_pct < 90 else "🔴")
    protein_icon = "✅" if protein_pct >= 90 else "⚠️"

    all_done = cal_icon == "✅" and protein_icon == "✅" and workout_count > 0

    return (
        f"Evening check-in, {user.name}! 🌙\n\n"
        f"{cal_icon} Calories: {cal}/{cal_target} kcal ({cal_pct}%)\n"
        f"{protein_icon} Protein: {protein}/{protein_target}g ({protein_pct}%)\n"
        f"{workout_icon} Workout: {'Done!' if workout_count > 0 else 'Not logged yet'}\n\n"
        f"{'Great work today! 🔥' if all_done else 'Still time to log anything you missed!'}"
    )
