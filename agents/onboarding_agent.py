import re
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from backend.models.db_models import User, UserGoals
from backend.services.redis_service import get_redis

ACTIVITY_LABELS = {
    "sedentary": "Sedentary 🪑", "light": "Light 🚶",
    "moderate": "Moderate 🏃", "active": "Active 💪", "very_active": "Very Active 🏆",
}
GOAL_LABELS = {
    "lose": "Lose weight 🔥",
    "gain": "Build muscle 💪",
    "maintain": "Maintain weight ⚖️",
    "recomp": "Body recomposition 🔄",
    "endurance": "Improve endurance 🏃",
    "strength": "Get stronger 🏋️",
    "health": "General health & wellness 🩺",
}

GOAL_MENU = (
    "*What's your fitness goal?*\n\n"
    "1️⃣ 🔥 Lose weight\n"
    "2️⃣ 💪 Build muscle\n"
    "3️⃣ ⚖️ Maintain weight\n"
    "4️⃣ 🔄 Body recomposition _(build muscle + lose fat)_\n"
    "5️⃣ 🏃 Improve endurance / fitness\n"
    "6️⃣ 🏋️ Get stronger\n"
    "7️⃣ 🩺 General health & wellness\n"
    "8️⃣ 💬 Custom _(type your own goal)_\n\n"
    "_Reply with 1–8 or describe your goal_"
)

_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Goals that don't need a target weight question
_NO_TARGET_GOALS = {"maintain", "endurance", "health"}


async def _calculate_targets(age, height_cm, weight_kg, gender, activity, goal_type, target_weight):
    prompt = (
        f"Calculate personalized daily nutrition targets for this person:\n"
        f"- Age: {age} years\n"
        f"- Height: {height_cm} cm\n"
        f"- Current weight: {weight_kg} kg\n"
        f"- Gender: {gender}\n"
        f"- Activity level: {activity}\n"
        f"- Goal: {goal_type}\n"
        f"- Target weight: {target_weight} kg\n\n"
        f"Use your nutritional expertise (consider TDEE, goal-specific adjustments, Indian diet context).\n"
        f"For time_est: estimate realistic weeks to reach target weight, or null if no weight change goal.\n\n"
        f"Respond ONLY in this exact JSON format:\n"
        f'{{"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "time_est": "~X weeks or null"}}'
    )
    resp = await _llm.ainvoke([
        SystemMessage(content="You are a certified nutritionist. Respond only with the requested JSON."),
        HumanMessage(content=prompt),
    ])
    try:
        content = resp.content.strip()
        start = content.find('{')
        end = content.rfind('}') + 1
        data = json.loads(content[start:end])
        return {
            "calories": max(int(data.get("calories", 2000)), 1200),
            "protein": int(data.get("protein", 150)),
            "carbs": int(data.get("carbs", 200)),
            "fat": int(data.get("fat", 65)),
            "time_est": data.get("time_est") if data.get("time_est") not in (None, "null") else None,
        }
    except Exception:
        # Fallback to safe defaults if LLM response unparseable
        return {"calories": 2000, "protein": 150, "carbs": 200, "fat": 65, "time_est": None}


async def _classify_custom_goal(text: str) -> tuple[str, str]:
    """Returns (goal_type, display_label) for free-text goal."""
    resp = await _llm.ainvoke([
        SystemMessage(content=(
            "Classify this fitness goal into one of: lose, gain, recomp, endurance, strength, health, maintain. "
            "Also produce a short friendly label (max 5 words) for the goal. "
            'Respond ONLY as JSON: {"type": "...", "label": "..."}'
        )),
        HumanMessage(content=text),
    ])
    try:
        data = json.loads(resp.content.strip())
        goal_type = data.get("type", "maintain")
        if goal_type not in GOAL_LABELS:
            goal_type = "maintain"
        label = data.get("label", text[:40])
        return goal_type, label
    except Exception:
        return "maintain", text[:40]


def _parse_height(text):
    cm = re.search(r'(\d+\.?\d*)\s*cm', text, re.IGNORECASE)
    if cm:
        return float(cm.group(1))
    ft = re.search(r"(\d+)['\s](\d+)", text)
    if ft:
        return round(int(ft.group(1)) * 30.48 + int(ft.group(2)) * 2.54, 1)
    nums = re.findall(r'\d+\.?\d*', text)
    if nums:
        h = float(nums[0])
        return h if h > 100 else round(h * 30.48, 1)
    return None


_ACTIVITY_QUESTION = (
    "*How active are you?*\n\n"
    "1️⃣ 🪑 Sedentary _(desk job, no exercise)_\n"
    "2️⃣ 🚶 Light _(1–3 days/week)_\n"
    "3️⃣ 🏃 Moderate _(3–5 days/week)_\n"
    "4️⃣ 💪 Active _(6–7 days/week)_\n"
    "5️⃣ 🏆 Very Active _(athlete / physical job)_\n\n"
    "_Reply with 1–5_"
)


async def handle_onboarding(message: str, user: User, db: AsyncSession) -> str:
    r = await get_redis()
    key = f"onboarding:{user.phone}"
    state = await r.hgetall(key) or {}
    step = state.get("step", "")
    msg = message.strip().lower()

    async def save(mapping: dict):
        await r.hset(key, mapping=mapping)
        await r.expire(key, 86400)

    # ── BACK navigation ───────────────────────────────────────────────────────
    if step and any(t in msg for t in ("back", "previous", "prev", "undo")):
        current_weight = state.get("weight", "70")
        goal_type = state.get("goal_type", "maintain")
        prev = {
            "gender": ("name", "What's your *name?*"),
            "age": ("gender", "What's your *gender?*\n\n1️⃣ Male\n2️⃣ Female\n3️⃣ Other\n\n_Reply with 1, 2 or 3_"),
            "height": ("age", "How old are you?\n\n_Enter your age in years (e.g. 25)_"),
            "weight": ("height", "What's your *height*?\n\n_E.g. 175 cm or 5'9\"_"),
            "goal_type": ("weight", "What's your *current weight*?\n\n_E.g. 80 kg_"),
            "target_weight": ("goal_type", GOAL_MENU),
            "activity": ("goal_type" if goal_type in _NO_TARGET_GOALS else "target_weight",
                         GOAL_MENU if goal_type in _NO_TARGET_GOALS
                         else f"What's your *goal weight*? _(Currently {float(current_weight):.0f} kg)_\n\n_E.g. 70 kg_"),
            "confirm": ("activity", _ACTIVITY_QUESTION),
        }
        if step in prev:
            new_step, question = prev[step]
            await save({"step": new_step})
            return f"↩️ Going back!\n\n{question}"
        return "You're at the first step already!"

    # ── STEP 0: first contact ──────────────────────────────────────────────────
    if not step:
        await save({"step": "name"})
        return (
            "👋 *Welcome to FitSquad!*\n\n"
            "I'm FitBot — your AI fitness coach. "
            "Let me set up your personal profile so I can calculate your exact calorie and nutrition targets.\n\n"
            "*What's your name?*"
        )

    # ── STEP 1: name ──────────────────────────────────────────────────────────
    if step == "name":
        name = message.strip().title()
        if len(name) < 2:
            return "Please enter your name (at least 2 characters)."
        user.name = name
        await db.commit()
        await save({"step": "gender", "name": name})
        return (
            f"Nice to meet you, *{name}!* 👋\n\n"
            "*What's your gender?*\n\n"
            "1️⃣ Male\n2️⃣ Female\n3️⃣ Other\n\n"
            "_Reply with 1, 2 or 3_"
        )

    # ── STEP 2: gender ────────────────────────────────────────────────────────
    if step == "gender":
        gender = "female" if msg in ("2", "female", "f") else "male"
        await save({"step": "age", "gender": gender})
        return "How old are you?\n\n_Enter your age in years (e.g. 25)_"

    # ── STEP 3: age ───────────────────────────────────────────────────────────
    if step == "age":
        nums = re.findall(r'\d+', message)
        if not nums or not (10 <= int(nums[0]) <= 100):
            return "Please enter a valid age (e.g. 25)."
        await save({"step": "height", "age": nums[0]})
        return "What's your *height*?\n\n_E.g. 175 cm or 5'9\"_"

    # ── STEP 4: height ────────────────────────────────────────────────────────
    if step == "height":
        h = _parse_height(message)
        if not h or not (100 <= h <= 250):
            return "Please enter a valid height (e.g. 175 cm or 5'10\")."
        await save({"step": "weight", "height_cm": str(h)})
        return "What's your *current weight*?\n\n_E.g. 80 kg_"

    # ── STEP 5: weight ────────────────────────────────────────────────────────
    if step == "weight":
        nums = re.findall(r'\d+\.?\d*', message)
        if not nums or not (30 <= float(nums[0]) <= 300):
            return "Please enter a valid weight (e.g. 80 kg)."
        await save({"step": "goal_type", "weight": nums[0]})
        return GOAL_MENU

    # ── STEP 6: goal type ─────────────────────────────────────────────────────
    if step == "goal_type":
        number_map = {
            "1": "lose", "2": "gain", "3": "maintain",
            "4": "recomp", "5": "endurance", "6": "strength", "7": "health",
        }
        keyword_map = [
            ("recomp", ("recomp", "recomposition", "build muscle and lose", "muscle and fat", "toned", "tone")),
            ("lose",   ("lose", "loss", "fat loss", "slim", "cut", "cutting", "shred", "weight loss")),
            ("gain",   ("gain", "build muscle", "bulk", "bulking", "mass", "hypertrophy", "muscle")),
            ("endurance", ("endur", "cardio", "run", "marathon", "stamina", "fitness", "aerobic")),
            ("strength",  ("strong", "strength", "powerlifting", "powerl", "1rm", "max")),
            ("health",    ("health", "wellness", "healthy", "lifestyle", "general")),
            ("maintain",  ("maintain", "maintenance", "same weight")),
        ]

        current_weight = state.get("weight", "70")
        goal = number_map.get(msg)
        custom_label = None

        if not goal:
            # Check keywords
            for g, kws in keyword_map:
                if any(kw in msg for kw in kws):
                    goal = g
                    break

        if msg == "8" or (not goal):
            # Custom goal via LLM
            if msg == "8":
                await save({"step": "custom_goal"})
                return "Tell me your fitness goal in your own words 💬\n\n_E.g. 'I want to run a 5K' or 'I want to lose belly fat and feel more energetic'_"
            else:
                goal, custom_label = await _classify_custom_goal(message)

        # Detect contradictory state: said "gain" but will set a lower target → recomp
        # We'll check this again at target_weight step

        await save({"step": "activity" if goal in _NO_TARGET_GOALS else "target_weight",
                    "goal_type": goal,
                    "goal_label": custom_label or GOAL_LABELS.get(goal, goal),
                    "target_weight": current_weight})

        if goal in _NO_TARGET_GOALS:
            return _ACTIVITY_QUESTION

        direction = "target" if goal == "lose" else "goal"
        return f"What's your *{direction} weight*? _(Currently {float(current_weight):.0f} kg)_\n\n_E.g. 70 kg_"

    # ── STEP 6b: custom goal text ─────────────────────────────────────────────
    if step == "custom_goal":
        goal, custom_label = await _classify_custom_goal(message)
        current_weight = state.get("weight", "70")
        await save({"step": "activity" if goal in _NO_TARGET_GOALS else "target_weight",
                    "goal_type": goal,
                    "goal_label": custom_label,
                    "target_weight": current_weight})
        if goal in _NO_TARGET_GOALS:
            return _ACTIVITY_QUESTION
        direction = "target" if goal == "lose" else "goal"
        return f"Got it — _{custom_label}_!\n\nWhat's your *{direction} weight*? _(Currently {float(current_weight):.0f} kg)_\n\n_E.g. 70 kg_"

    # ── STEP 7: target weight ─────────────────────────────────────────────────
    if step == "target_weight":
        nums = re.findall(r'\d+\.?\d*', message)
        if not nums or not (30 <= float(nums[0]) <= 300):
            return "Please enter a valid target weight (e.g. 70 kg)."
        target = float(nums[0])
        current = float(state.get("weight", 70))
        goal_type = state.get("goal_type", "maintain")

        # Auto-correct contradictory goal/target combos → recomp
        if goal_type == "gain" and target < current:
            goal_type = "recomp"
            await save({"goal_type": "recomp", "goal_label": GOAL_LABELS["recomp"]})
        elif goal_type == "lose" and target > current:
            goal_type = "gain"
            await save({"goal_type": "gain", "goal_label": GOAL_LABELS["gain"]})

        await save({"step": "activity", "target_weight": nums[0]})
        return _ACTIVITY_QUESTION

    # ── STEP 8: activity level → calculate & show targets ─────────────────────
    if step == "activity":
        activity_map = {
            "1": "sedentary", "2": "light", "3": "moderate", "4": "active", "5": "very_active",
            "sedentary": "sedentary", "light": "light", "moderate": "moderate",
            "active": "active", "very active": "very_active", "very_active": "very_active",
        }
        activity = activity_map.get(msg)
        if not activity:
            return (
                "Please reply with a number 1–5:\n\n"
                "1️⃣ 🪑 Sedentary\n2️⃣ 🚶 Light\n3️⃣ 🏃 Moderate\n4️⃣ 💪 Active\n5️⃣ 🏆 Very Active"
            )

        state = await r.hgetall(key) or {}
        age = int(state.get("age", 25))
        height_cm = float(state.get("height_cm", 170))
        weight = float(state.get("weight", 70))
        gender = state.get("gender", "male")
        goal_type = state.get("goal_type", "maintain")
        target_weight = float(state.get("target_weight", weight))
        goal_label = state.get("goal_label", GOAL_LABELS.get(goal_type, goal_type))

        t = await _calculate_targets(age, height_cm, weight, gender, activity, goal_type, target_weight)

        await save({
            "step": "confirm",
            "activity": activity,
            "calc_calories": str(t["calories"]),
            "calc_protein": str(t["protein"]),
            "calc_carbs": str(t["carbs"]),
            "calc_fat": str(t["fat"]),
        })

        weight_line = f"👤 {age}y | {height_cm:.0f}cm | {weight:.0f}kg"
        if goal_type not in _NO_TARGET_GOALS and abs(target_weight - weight) > 0.5:
            weight_line += f" → {target_weight:.0f}kg"

        lines = [
            f"📊 *Your Personalized Targets*\n",
            weight_line,
            f"🎯 Goal: {goal_label}",
            f"⚡ Activity: {ACTIVITY_LABELS[activity]}\n",
            f"*Daily Nutrition Targets:*",
            f"🔥 Calories: *{t['calories']} kcal*",
            f"🥩 Protein:  *{t['protein']}g*",
            f"🌾 Carbs:    *{t['carbs']}g*",
            f"🥑 Fat:      *{t['fat']}g*",
        ]
        if t["time_est"]:
            lines.append(f"\n⏱ {t['time_est']}")
        lines += [
            f"\n✅ Reply *YES* to confirm and start tracking!",
            f"✏️ Reply *EDIT* to change your goals",
            f"🔢 Type a number _(e.g. 2500)_ to set custom calories, or _protein 160g_ for custom protein",
            f"↩️ Reply *BACK* to change activity level",
        ]
        return "\n".join(lines)

    # ── STEP 9: confirm ───────────────────────────────────────────────────────
    if step == "confirm":
        if msg in ("restart", "redo"):
            await r.delete(key)
            await save({"step": "name"})
            return "No problem! Let's start over.\n\n*What's your name?*"

        if msg in ("edit", "change", "no"):
            kept = {k: state[k] for k in ("name", "gender", "age", "height_cm", "weight") if k in state}
            await r.delete(key)
            await save({**kept, "step": "goal_type"})
            return f"No problem! Let's redo your goals.\n\n{GOAL_MENU}"

        # Custom protein override — user types "protein 160g" or "160g protein" or "protein 160"
        protein_match = re.search(r'(?:protein\s*(\d{2,3})\s*g?|(\d{2,3})\s*g?\s*protein)', message, re.IGNORECASE)
        if protein_match:
            custom_protein = int(protein_match.group(1) or protein_match.group(2))
            if 30 <= custom_protein <= 400:
                cur_cal = int(state.get("calc_calories", 2000))
                cur_fat = int(state.get("calc_fat", 65))
                carbs = max(int((cur_cal - custom_protein * 4 - cur_fat * 9) / 4), 0)
                await save({
                    "calc_protein": str(custom_protein),
                    "calc_carbs": str(carbs),
                })
                goal_label = state.get("goal_label", GOAL_LABELS.get(state.get("goal_type", "maintain"), ""))
                activity = state.get("activity", "moderate")
                return (
                    f"✏️ *Updated targets:*\n\n"
                    f"🎯 Goal: {goal_label}\n"
                    f"⚡ Activity: {ACTIVITY_LABELS.get(activity, activity)}\n\n"
                    f"🔥 Calories: *{cur_cal} kcal*\n"
                    f"🥩 Protein:  *{custom_protein}g* _(custom)_\n"
                    f"🌾 Carbs:    *{carbs}g*\n"
                    f"🥑 Fat:      *{cur_fat}g*\n\n"
                    f"✅ Reply *YES* to confirm or adjust further"
                )

        # Custom calorie override — user types a number like "2500" or "set 2200 calories"
        cal_nums = re.findall(r'\b(\d{3,4})\b', message)
        custom_cal = next((int(n) for n in cal_nums if 1000 <= int(n) <= 6000), None)
        if custom_cal:
            orig_cal = int(state.get("calc_calories", 2000))
            orig_protein = int(state.get("calc_protein", 150))
            orig_carbs = int(state.get("calc_carbs", 200))
            orig_fat = int(state.get("calc_fat", 65))
            # Scale all macros proportionally
            ratio = custom_cal / orig_cal if orig_cal else 1
            protein = max(int(orig_protein * ratio), 50)
            fat = max(int(orig_fat * ratio), 20)
            carbs = max(int((custom_cal - protein * 4 - fat * 9) / 4), 0)
            await save({
                "calc_calories": str(custom_cal),
                "calc_protein": str(protein),
                "calc_carbs": str(carbs),
                "calc_fat": str(fat),
            })
            goal_label = state.get("goal_label", GOAL_LABELS.get(state.get("goal_type", "maintain"), ""))
            activity = state.get("activity", "moderate")
            return (
                f"✏️ *Updated targets:*\n\n"
                f"🎯 Goal: {goal_label}\n"
                f"⚡ Activity: {ACTIVITY_LABELS.get(activity, activity)}\n\n"
                f"🔥 Calories: *{custom_cal} kcal* _(custom)_\n"
                f"🥩 Protein:  *{protein}g*\n"
                f"🌾 Carbs:    *{carbs}g*\n"
                f"🥑 Fat:      *{fat}g*\n\n"
                f"✅ Reply *YES* to confirm or type another number to adjust"
            )

        if msg not in ("yes", "y", "ok", "okay", "confirm", "sure", "looks good", "perfect", "great", "yep", "yup"):
            return "Please reply *YES* to confirm your targets, *EDIT* to change goals, enter a calorie number _(e.g. 2500)_, or set protein _(e.g. protein 160g)_."

        state = await r.hgetall(key) or {}
        name = state.get("name", user.name or "")
        goals_result = await db.execute(select(UserGoals).where(UserGoals.user_id == user.id))
        goals = goals_result.scalar_one_or_none()
        if not goals:
            goals = UserGoals(user_id=user.id)
            db.add(goals)

        goals.daily_calories = int(state.get("calc_calories", 2000))
        goals.protein_g = int(state.get("calc_protein", 150))
        goals.carbs_g = int(state.get("calc_carbs", 200))
        goals.fat_g = int(state.get("calc_fat", 65))
        goals.goal_type = state.get("goal_type", "maintain")
        goals.target_weight_kg = float(state.get("target_weight", state.get("weight", 70)))
        goals.activity_level = state.get("activity", "moderate")
        goals.age = int(state.get("age", 25))
        goals.height_cm = float(state.get("height_cm", 170))
        goals.current_weight_kg = float(state.get("weight", 70))

        user.is_onboarded = True
        await db.commit()
        await r.delete(key)

        return (
            f"🎉 *You're all set, {name}!*\n\n"
            f"Your targets are saved. Time to get to work! 💪\n\n"
            f"*Start logging in the group:*\n"
            f"🍽 @FitBot had chicken rice for lunch\n"
            f"🏋 @FitBot 45 min gym session\n"
            f"⚖ @FitBot weight: 79kg\n\n"
            f"*Commands:*\n"
            f"📊 @FitBot stats\n"
            f"🏆 @FitBot leaderboard\n"
            f"💡 @FitBot advice\n"
            f"📋 @FitBot my report\n\n"
            f"Let's crush those goals! 🚀"
        )

    return "Something went wrong. Send any message to restart."
