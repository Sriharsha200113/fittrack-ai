import json
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from backend.models.db_models import MealLog, UserGoals, User, Squad
from backend.services.points_service import award_points
from backend.services.redis_service import get_redis

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

SYSTEM_PROMPT = """You are a nutrition expert parsing a meal log message for a fitness tracking app.
Extract the food items and estimate macros accurately.

Use standard Indian food nutritional values where applicable.
If quantity is unclear, assume a standard single serving.

Respond ONLY in this exact JSON format with no additional text:
{
  "meal_type": "breakfast|lunch|dinner|snack",
  "food_items": [
    {"name": "string", "quantity": "string", "calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
  ],
  "total_calories": 0,
  "total_protein_g": 0,
  "total_carbs_g": 0,
  "total_fat_g": 0
}"""

VISION_PROMPT = """You are a nutrition expert analyzing a food photo for a fitness tracking app.
Identify all visible food items and estimate macros accurately.

Use standard Indian food nutritional values where applicable.
Assume a standard single serving if quantity is unclear.

Respond ONLY in this exact JSON format with no additional text:
{
  "meal_type": "breakfast|lunch|dinner|snack",
  "food_items": [
    {"name": "string", "quantity": "string", "calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
  ],
  "total_calories": 0,
  "total_protein_g": 0,
  "total_carbs_g": 0,
  "total_fat_g": 0
}"""

PENDING_TTL = 300  # 5 minutes to confirm


def _progress_bar(pct: int) -> str:
    filled = min(10, pct // 10)
    return "█" * filled + "░" * (10 - filled)


def _parse_llm_json(content: str) -> dict | None:
    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        start = content.find('{')
        end = content.rfind('}') + 1
        if start >= 0 and end > start:
            try:
                return json.loads(content[start:end])
            except json.JSONDecodeError:
                return None
    return None


async def handle_diet(message: str, user: User, squad: Squad, db: AsyncSession, image_data: str | None = None, image_mimetype: str | None = None) -> str:
    if image_data:
        messages = [
            SystemMessage(content=VISION_PROMPT),
            HumanMessage(content=[
                {"type": "image_url", "image_url": {"url": f"data:{image_mimetype or 'image/jpeg'};base64,{image_data}"}},
                {"type": "text", "text": "Identify all food items in this photo and estimate their macros."},
            ]),
        ]
        raw_text = message or "food photo"
    else:
        messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=message)]
        raw_text = message

    response = await llm.ainvoke(messages)
    data = _parse_llm_json(response.content)

    if not data:
        return "Sorry, I couldn't identify the food. Please describe your meal in text (e.g. '2 chapati with dal')."

    # For photo meals, build raw_text from detected food names
    if image_data:
        items = data.get("food_items", [])
        raw_text = ", ".join(item["name"] for item in items) if items else (message or "food photo")

    # Store pending meal in Redis for confirmation
    r = await get_redis()
    pending = json.dumps({**data, "raw_text": raw_text})
    await r.set(f"pending_meal:{user.phone}", pending, ex=PENDING_TTL)

    items = data.get("food_items", [])
    cal = round(data.get("total_calories", 0))
    p = round(data.get("total_protein_g", 0))
    c = round(data.get("total_carbs_g", 0))
    f = round(data.get("total_fat_g", 0))
    meal_type = data.get("meal_type", "meal").capitalize()

    lines = [f"🍽️ *{meal_type} detected:*\n"]
    for item in items:
        lines.append(f"• {item['name']} ({item['quantity']}) — {round(item['calories'])} kcal | P:{round(item['protein_g'])}g C:{round(item['carbs_g'])}g F:{round(item['fat_g'])}g")

    lines += [
        f"\n*Total:* {cal} kcal | Protein: {p}g | Carbs: {c}g | Fat: {f}g",
        f"\n✅ Reply *YES* to log this meal",
        f"❌ Reply *NO* to cancel",
    ]
    return "\n".join(lines)


async def confirm_meal(user: User, squad: Squad, db: AsyncSession) -> str:
    r = await get_redis()
    raw = await r.get(f"pending_meal:{user.phone}")
    if not raw:
        return "No pending meal to confirm. Log your meal first."

    data = json.loads(raw)
    await r.delete(f"pending_meal:{user.phone}")

    meal_log = MealLog(
        user_id=user.id,
        raw_text=data.get("raw_text", ""),
        meal_type=data.get("meal_type", "snack"),
        food_items=data.get("food_items", []),
        calories=data.get("total_calories", 0),
        protein_g=data.get("total_protein_g", 0),
        carbs_g=data.get("total_carbs_g", 0),
        fat_g=data.get("total_fat_g", 0),
        log_date=date.today(),
    )
    db.add(meal_log)

    result = await award_points("meal", user, squad, db)

    today = date.today()
    daily_result = await db.execute(
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
    daily_cal, daily_p, daily_c, daily_f = daily_result.one()
    daily_cal = round(daily_cal or 0)
    daily_p = round(daily_p or 0)

    goal_result = await db.execute(select(UserGoals).where(UserGoals.user_id == user.id))
    goals = goal_result.scalar_one_or_none()

    cal_target = goals.daily_calories if goals else 2000
    protein_target = goals.protein_g if goals else 150

    cal_pct = round((daily_cal / cal_target) * 100) if cal_target else 0
    protein_pct = round((daily_p / protein_target) * 100) if protein_target else 0

    nutrition_bonus = 0
    nutrition_msg = ""
    if goals:
        if protein_pct >= 90:
            protein_result = await award_points("protein_hit", user, squad, db)
            if protein_result["points_awarded"] > 0:
                nutrition_bonus += protein_result["points_awarded"]
                nutrition_msg += " +15 protein bonus! 🎯"
        if 90 <= cal_pct <= 110:
            cal_result = await award_points("calorie_hit", user, squad, db)
            if cal_result["points_awarded"] > 0:
                nutrition_bonus += cal_result["points_awarded"]
                nutrition_msg += " +15 calorie target hit! 🎯"

    streak = result["current_streak"]
    rank = result["rank"]
    new_badges = result["new_badges"]
    streak_bonus = result["streak_bonus"]

    badge_line = ""
    if new_badges:
        badge_str = "  ".join([f"{b['emoji']} {b['label']}" for b in new_badges])
        badge_line = f"\n🏅 New badge: {badge_str}"

    streak_line = f"🔥 Streak: {streak} days" if streak > 1 else ""
    bonus_line = ""
    if streak_bonus:
        bonus_line += f" +{streak_bonus} streak bonus!"
    if nutrition_msg:
        bonus_line += nutrition_msg

    meal_type = data.get("meal_type", "meal").capitalize()
    cal = round(data.get("total_calories", 0))
    p = round(data.get("total_protein_g", 0))
    items = data.get("food_items", [])
    food_summary = ", ".join([item.get("name", "") for item in items[:3]])
    if len(items) > 3:
        food_summary += f" +{len(items)-3} more"

    return (
        f"✅ Logged {user.name}!\n"
        f"🍽️ {meal_type}: {food_summary}\n"
        f"Calories: {cal} kcal | P: {p}g\n\n"
        f"📊 Daily Progress:\n"
        f"Calories: {_progress_bar(cal_pct)} {daily_cal}/{cal_target} ({cal_pct}%)\n"
        f"Protein:  {_progress_bar(protein_pct)} {daily_p}/{protein_target}g ({protein_pct}%)\n"
        f"+{result['points_awarded']} pts{bonus_line} | Squad: #{rank}{badge_line}\n"
        + (f"{streak_line}" if streak_line else "")
    )
