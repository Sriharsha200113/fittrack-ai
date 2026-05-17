import json
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from backend.models.db_models import BodyMetrics, UserGoals, User, Squad
from backend.services.points_service import award_points

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

SYSTEM_PROMPT = """You are parsing a body metrics log message from a fitness app user.
Extract any body metrics mentioned.

Respond ONLY in this exact JSON format:
{
  "weight_kg": null,
  "body_fat_pct": null,
  "waist_cm": null,
  "chest_cm": null,
  "arms_cm": null,
  "notes": null
}

Rules:
- If weight is mentioned in lbs, convert to kg (1 lb = 0.453592 kg)
- If only a number is given with no unit, assume kg
- Set fields to null if not mentioned
- Round weight to 1 decimal place"""


async def handle_body_metrics(message: str, user: User, squad: Squad, db: AsyncSession) -> str:
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
            return f"⚖️ Weight logged, {user.name}!"

    metrics = BodyMetrics(
        user_id=user.id,
        weight_kg=data.get("weight_kg"),
        body_fat_pct=data.get("body_fat_pct"),
        waist_cm=data.get("waist_cm"),
        chest_cm=data.get("chest_cm"),
        arms_cm=data.get("arms_cm"),
        notes=data.get("notes"),
        log_date=date.today(),
    )
    db.add(metrics)

    # award_points commits the session (including the unsaved metrics above)
    result = await award_points("weight_logged", user, squad, db)

    goal_result = await db.execute(select(UserGoals).where(UserGoals.user_id == user.id))
    goals = goal_result.scalar_one_or_none()

    weight = data.get("weight_kg")
    if not weight:
        return f"📊 Metrics logged, {user.name}! Keep tracking consistently 💪"

    reply_lines = [f"⚖️ Logged {user.name}! Weight: *{weight} kg*"]

    if goals and goals.target_weight_kg:
        diff = round(weight - goals.target_weight_kg, 1)
        if diff > 0:
            reply_lines.append(f"🎯 Goal: {goals.target_weight_kg} kg | {diff} kg to go")
        elif diff < 0:
            reply_lines.append(f"🎯 Goal: {goals.target_weight_kg} kg | You're {abs(diff)} kg past target! 🎉")
        else:
            reply_lines.append(f"🎯 Goal reached! You're at target weight! 🏆")

    if result["points_awarded"] > 0:
        reply_lines.append(f"+{result['points_awarded']} pts for logging weight!")

    return "\n".join(reply_lines)
