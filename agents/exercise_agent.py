import json
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from backend.models.db_models import ExerciseLog, User, Squad
from backend.services.points_service import award_points

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

SYSTEM_PROMPT = """You are a fitness expert parsing a workout log message.
Extract workout details from what the user explicitly stated.

Rules:
- Only set duration_min if the user explicitly mentions time (e.g. "60 min", "1 hour"). Otherwise null.
- Only set estimated_calories_burned if duration_min is known. Otherwise null.
- Extract exercises, sets, and reps only if mentioned.

Respond ONLY in this exact JSON format with no additional text:
{
  "workout_type": "chest|back|legs|shoulders|arms|cardio|full_body|other",
  "duration_min": null,
  "exercises": [
    {"name": "string", "sets": null, "reps": null}
  ],
  "estimated_calories_burned": null,
  "summary": "brief one-line summary e.g. Chest day — bench press 4 sets"
}"""


async def handle_exercise(message: str, user: User, squad: Squad, db: AsyncSession) -> str:
    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=message)]
    response = await llm.ainvoke(messages)

    try:
        data = json.loads(response.content.strip())
    except json.JSONDecodeError:
        content = response.content
        start = content.find('{')
        end = content.rfind('}') + 1
        if start >= 0 and end > start:
            data = json.loads(content[start:end])
        else:
            return f"🏋️ Workout logged, {user.name}! Keep it up!"

    exercise_log = ExerciseLog(
        user_id=user.id,
        raw_text=message,
        workout_type=data.get("workout_type", "other"),
        duration_min=data.get("duration_min"),
        sets_reps=data.get("exercises", []),
        calories_burned=data.get("estimated_calories_burned"),
        log_date=date.today(),
    )
    db.add(exercise_log)

    # award_points commits the session (including the unsaved exercise_log above)
    result = await award_points("workout", user, squad, db)

    streak = result["current_streak"]
    rank = result["rank"]
    new_badges = result["new_badges"]
    streak_bonus = result["streak_bonus"]

    badge_line = ""
    if new_badges:
        badge_str = "  ".join([f"{b['emoji']} {b['label']}" for b in new_badges])
        badge_line = f"\n🏅 New badge: {badge_str}"

    bonus_line = f" +{streak_bonus} streak bonus!" if streak_bonus else ""

    duration = data.get("duration_min")
    cal_burned = data.get("estimated_calories_burned")
    summary = data.get("summary", "Workout completed")

    stats_parts = []
    if duration:
        stats_parts.append(f"⏱️ {duration} min")
    if cal_burned:
        stats_parts.append(f"🔥 ~{round(cal_burned)} kcal burned")
    stats_line = (" | ".join(stats_parts) + "\n") if stats_parts else ""

    return (
        f"🏋️ Logged {user.name}! {summary}\n"
        f"{stats_line}"
        f"+{result['points_awarded']} pts{bonus_line} | Squad: #{rank} 🏆\n"
        f"🔥 Streak: {streak} days"
        + badge_line
    )
