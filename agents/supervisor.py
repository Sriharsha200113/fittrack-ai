from sqlalchemy.ext.asyncio import AsyncSession
from backend.agents.intent_classifier import classify_intent
from backend.agents.diet_agent import handle_diet, confirm_meal
from backend.agents.exercise_agent import handle_exercise
from backend.agents.general_agent import handle_general
from backend.agents.body_metrics_agent import handle_body_metrics
from backend.agents.goal_agent import handle_goal
from backend.agents.checkin_agent import handle_checkin
from backend.agents.advice_agent import handle_advice
from backend.models.db_models import User, Squad
from backend.services.redis_service import get_redis

_YES = {"yes", "y", "ok", "okay", "confirm", "sure", "yep", "yup", "log it", "save"}
_NO = {"no", "n", "cancel", "discard", "nope", "delete"}


async def process(user: User, squad: Squad, message: str, db: AsyncSession,
                  image_data: str | None = None, image_mimetype: str | None = None) -> str:
    msg = message.strip().lower()

    # Handle pending meal confirmation
    r = await get_redis()
    has_pending = await r.exists(f"pending_meal:{user.phone}")

    if has_pending:
        if msg in _YES:
            return await confirm_meal(user, squad, db)
        if msg in _NO:
            await r.delete(f"pending_meal:{user.phone}")
            return "❌ Meal cancelled. Nothing was logged."
        if not image_data:
            return "Please reply *YES* to log the meal or *NO* to cancel."

    # Image always goes to diet agent
    if image_data:
        return await handle_diet(message, user, squad, db, image_data, image_mimetype)

    intent = await classify_intent(message)

    if intent == "diet":
        return await handle_diet(message, user, squad, db)
    elif intent == "exercise":
        return await handle_exercise(message, user, squad, db)
    elif intent == "body_metrics":
        return await handle_body_metrics(message, user, squad, db)
    elif intent == "goal_setting":
        return await handle_goal(message, user, db)
    elif intent == "check_in":
        return await handle_checkin(message, user, squad, db)
    elif intent == "advice":
        return await handle_advice(message, user, db)
    else:
        return await handle_general(intent, message, user, squad, db)
