import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from backend.models.db_models import UserGoals, User

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

SYSTEM_PROMPT = """You are parsing a goal-setting message for a fitness app.
Extract any fitness goals or targets mentioned.

Respond ONLY in this exact JSON format:
{
  "action": "set|view",
  "daily_calories": null,
  "protein_g": null,
  "carbs_g": null,
  "fat_g": null,
  "goal_type": null,
  "target_weight_kg": null,
  "activity_level": null
}

Rules:
- action is "set" if user wants to change goals, "view" if they want to see current goals
- goal_type must be one of: fat_loss, muscle_gain, recomp, maintain (or null if not mentioned)
- activity_level: sedentary, light, moderate, active, very_active (or null)
- Set fields to null if not mentioned
- Keywords: "lose fat/weight" → fat_loss, "build muscle/bulk" → muscle_gain,
  "recomp/body recomp" → recomp, "maintain" → maintain"""


async def handle_goal(message: str, user: User, db: AsyncSession) -> str:
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
            return "❓ Couldn't parse your goal. Try: 'set calorie goal 2000' or 'protein target 150g'"

    result = await db.execute(select(UserGoals).where(UserGoals.user_id == user.id))
    goals = result.scalar_one_or_none()

    if not goals:
        goals = UserGoals(user_id=user.id)
        db.add(goals)

    if data.get("action") == "set":
        if data.get("daily_calories"):
            goals.daily_calories = int(data["daily_calories"])
        if data.get("protein_g"):
            goals.protein_g = int(data["protein_g"])
        if data.get("carbs_g"):
            goals.carbs_g = int(data["carbs_g"])
        if data.get("fat_g"):
            goals.fat_g = int(data["fat_g"])
        if data.get("goal_type"):
            goals.goal_type = data["goal_type"]
        if data.get("target_weight_kg"):
            goals.target_weight_kg = float(data["target_weight_kg"])
        if data.get("activity_level"):
            goals.activity_level = data["activity_level"]

        await db.commit()
        await db.refresh(goals)

    return _format_goals(user.name, goals)


def _format_goals(name: str, goals: UserGoals) -> str:
    goal_emoji = {
        "fat_loss": "🔥 Fat Loss",
        "muscle_gain": "💪 Muscle Gain",
        "recomp": "⚖️ Recomposition",
        "maintain": "🎯 Maintain",
    }
    goal_label = goal_emoji.get(goals.goal_type, "🎯 General Fitness")

    lines = [
        f"🎯 *{name}'s Goals*\n",
        f"Goal: {goal_label}",
        f"Daily calories: {goals.daily_calories} kcal",
        f"Protein target: {goals.protein_g}g",
    ]
    if goals.carbs_g:
        lines.append(f"Carbs target: {goals.carbs_g}g")
    if goals.fat_g:
        lines.append(f"Fat target: {goals.fat_g}g")
    if goals.target_weight_kg:
        lines.append(f"Target weight: {goals.target_weight_kg} kg")
    lines.append(f"Activity level: {goals.activity_level}")
    lines.append(f"\nTo update: 'set calorie goal 2200' or 'protein target 160g'")

    return "\n".join(lines)
