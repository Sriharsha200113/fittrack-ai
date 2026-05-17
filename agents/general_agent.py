from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from backend.models.db_models import MealLog, ExerciseLog, UserGoals, User, Squad
from backend.services.leaderboard_service import get_daily_leaderboard
from backend.services.streak_service import get_streak

_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

MEDALS = ["🥇", "🥈", "🥉"]


async def handle_general(intent: str, message: str, user: User, squad: Squad, db: AsyncSession) -> str:
    msg_lower = message.lower()

    if any(kw in msg_lower for kw in ["my report", "weekly report", "my stats report", "report"]):
        return await _on_demand_weekly_report(user, db)
    elif any(kw in msg_lower for kw in ["monthly report", "my monthly"]):
        return await _on_demand_monthly_report(user, squad, db)

    if intent == "leaderboard":
        return await _leaderboard(squad, db)
    elif intent == "stats":
        return await _personal_stats(user, squad, db)
    else:
        return await _conversational(message, user)


async def _leaderboard(squad: Squad, db: AsyncSession) -> str:
    today = date.today()
    entries = await get_daily_leaderboard(str(squad.id), today, db)

    if not entries:
        return f"🏆 {squad.name} — No activity logged yet today! 💪"

    lines = [f"🏆 *{squad.name}* — {today.strftime('%b %d')}\n"]

    for i, entry in enumerate(entries):
        medal = MEDALS[i] if i < 3 else "  "
        streak_data = await get_streak(entry["user_id"])
        streak = streak_data["current_streak"]
        streak_str = f" 🔥{streak}" if streak > 1 else ""
        lines.append(f"{medal} {entry['user_name']} — {entry['points']} pts{streak_str}")

    return "\n".join(lines)


async def _personal_stats(user: User, squad: Squad, db: AsyncSession) -> str:
    today = date.today()

    from backend.models.db_models import DailyPoints
    pts_result = await db.execute(
        select(DailyPoints).where(
            DailyPoints.user_id == user.id,
            DailyPoints.squad_id == squad.id,
            DailyPoints.date == today,
        )
    )
    dp = pts_result.scalar_one_or_none()
    total_pts = dp.points if dp else 0
    meals_logged = dp.meals_logged if dp else 0
    workouts_logged = dp.workouts_logged if dp else 0

    macro_result = await db.execute(
        select(
            func.sum(MealLog.calories),
            func.sum(MealLog.protein_g),
            func.sum(MealLog.carbs_g),
            func.sum(MealLog.fat_g),
        ).where(
            MealLog.user_id == user.id,
            MealLog.log_date == today,
        )
    )
    cal, p, c, f = macro_result.one()
    cal = round(cal or 0)
    p = round(p or 0)
    c = round(c or 0)
    f = round(f or 0)

    goal_result = await db.execute(select(UserGoals).where(UserGoals.user_id == user.id))
    goals = goal_result.scalar_one_or_none()

    cal_target = goals.daily_calories if goals else 2000
    protein_target = goals.protein_g if goals else 150

    cal_pct = round((cal / cal_target) * 100) if cal_target else 0
    protein_pct = round((p / protein_target) * 100) if protein_target else 0

    cal_icon = "✅" if 90 <= cal_pct <= 110 else ("⚠️" if cal_pct < 90 else "🔴")
    protein_icon = "✅" if protein_pct >= 90 else "⚠️"

    # Fetch today's workouts
    workouts_result = await db.execute(
        select(ExerciseLog).where(
            ExerciseLog.user_id == user.id,
            ExerciseLog.log_date == today,
        ).order_by(ExerciseLog.logged_at)
    )
    workouts = workouts_result.scalars().all()

    streak_data = await get_streak(str(user.id))
    streak = streak_data["current_streak"]
    streak_line = f"🔥 Streak: {streak} days\n" if streak > 1 else ""

    # Build workout lines
    workout_section = f"🏋️ *Workouts logged: {workouts_logged}*"
    if workouts:
        workout_items = []
        for w in workouts:
            label = w.workout_type or "Workout"
            parts = [label.capitalize()]
            if w.duration_min:
                parts.append(f"{w.duration_min} min")
            if w.calories_burned:
                parts.append(f"~{round(w.calories_burned)} kcal burned")
            workout_items.append("  • " + " · ".join(parts))
        workout_section += "\n" + "\n".join(workout_items)

    # Remaining calories
    remaining = cal_target - cal
    remaining_str = f"🍴 Remaining: {remaining} kcal\n" if remaining > 0 else ""

    return (
        f"📊 *{user.name}'s Stats — {today.strftime('%b %d')}*\n\n"
        f"🍽️ *Meals logged: {meals_logged}*\n"
        f"{cal_icon} Calories: {cal}/{cal_target} kcal ({cal_pct}%)\n"
        f"{remaining_str}"
        f"{protein_icon} Protein: {p}/{protein_target}g ({protein_pct}%)\n"
        f"Carbs: {c}g | Fat: {f}g\n\n"
        f"{workout_section}\n\n"
        f"{streak_line}"
        f"⭐ Today's points: {total_pts}"
    )


async def _on_demand_weekly_report(user: User, db: AsyncSession) -> str:
    from backend.services.report_service import get_weekly_report_data, format_weekly_report_text
    data = await get_weekly_report_data(user, db)
    return format_weekly_report_text(data)


async def _on_demand_monthly_report(user: User, squad: Squad, db: AsyncSession) -> str:
    from backend.services.report_service import get_monthly_report_data
    from backend.services.pdf_service import generate_monthly_pdf
    from backend.services.whatsapp_service import send_pdf
    data = await get_monthly_report_data(user, db)
    pdf_bytes = generate_monthly_pdf(data)
    filename = f"fitsquad_{user.name}_{date.today().strftime('%Y_%m')}"
    caption = f"📊 {user.name}'s Monthly Report — {data['month']}"
    await send_pdf(squad.wa_group_id, pdf_bytes, filename, caption)
    return f"📊 Your monthly report PDF is on the way, {user.name}!"


async def _conversational(message: str, user: User) -> str:
    response = await _llm.ainvoke([
        SystemMessage(content=(
            f"You are FitBot, a friendly AI fitness coach on WhatsApp. "
            f"The user's name is {user.name}. "
            f"Answer their question helpfully and concisely in 2-3 sentences. "
            f"If they seem to need help with commands, mention they can tag @FitBot with their meal or workout."
        )),
        HumanMessage(content=message),
    ])
    return response.content.strip()


def _help_message(user: User) -> str:
    return (
        f"Hey {user.name}! 👋 Here's what I can do:\n\n"
        f"🍽️ *Log meals* — just tell me what you ate\n"
        f"   'had chicken rice for lunch'\n\n"
        f"🏋️ *Log workouts* — tell me what you did\n"
        f"   'chest day done, bench 4 sets'\n\n"
        f"⚖️ *Log weight* — 'my weight is 74.5kg'\n\n"
        f"🎯 *Set goals* — 'set calorie goal 2200'\n"
        f"   'protein target 160g'\n"
        f"   'I want to lose fat'\n\n"
        f"💡 *Ask anything* — 'what should I eat for fat loss'\n"
        f"   'best exercises for chest'\n\n"
        f"📊 *stats* — your daily summary\n"
        f"🏆 *leaderboard* — squad rankings\n"
        f"📋 *my report* — weekly report\n"
        f"📋 *monthly report* — PDF report"
    )
