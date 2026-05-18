from typing import TypedDict, Any, Literal

from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from backend.models.db_models import User, Squad, UserGoals
from backend.agents.diet_agent import handle_diet, confirm_meal, correct_meal
from backend.agents.exercise_agent import handle_exercise
from backend.agents.general_agent import handle_general
from backend.agents.body_metrics_agent import handle_body_metrics
from backend.agents.goal_agent import handle_goal
from backend.agents.checkin_agent import handle_checkin
from backend.agents.advice_agent import handle_advice
from backend.services.redis_service import get_redis

_YES = {"yes", "y", "ok", "okay", "confirm", "sure", "yep", "yup", "log it", "save"}
_NO = {"no", "n", "cancel", "discard", "nope", "delete"}


class RouteDecision(BaseModel):
    next: Literal["diet", "exercise", "body_metrics", "goal", "checkin", "advice", "general", "FINISH"]
    direct_response: str = ""


class FitState(TypedDict):
    message: str
    user: Any
    squad: Any
    db: Any
    image_data: Any
    image_mimetype: Any
    intent: str
    response: str


_supervisor_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(RouteDecision)

_SUPERVISOR_SYSTEM = """\
You are FitBot, a fitness tracking assistant for WhatsApp groups. \
You are the central coordinator — all messages come through you first.

Route to the right specialist, or answer directly.

Routing options:
- diet        : logging meals, food, nutrition, calories (e.g. "had chicken rice", "ate 2 eggs")
- exercise    : logging workouts, gym, runs, steps (e.g. "chest day done", "ran 5km")
- body_metrics: logging weight or body measurements (e.g. "my weight is 74kg")
- goal        : setting or updating fitness goals/targets (e.g. "set protein goal 160g")
- checkin     : morning/evening check-ins (e.g. "gm", "good morning", "done for the day")
- advice      : fitness/nutrition questions needing expert guidance \
(e.g. "what should I eat for fat loss", "best chest exercises")
- general     : stats, leaderboard, reports (e.g. "stats", "leaderboard", "my report")
- FINISH      : answer directly — greetings, help, casual chat, anything else

For FINISH: write a warm, concise WhatsApp-style reply in direct_response.
Mention they can tag @FitBot with meals or workouts if helpful.

User: {user_name} | Goals: {goals_context}"""


async def _goals_context(user: User, db: AsyncSession) -> str:
    result = await db.execute(select(UserGoals).where(UserGoals.user_id == user.id))
    goals = result.scalar_one_or_none()
    if goals:
        return f"{goals.daily_calories} kcal, {goals.protein_g}g protein, goal={goals.goal_type}"
    return "not set"


# ── nodes ──────────────────────────────────────────────────────────────────────

async def _check_pending(state: FitState) -> dict:
    msg = state["message"].strip().lower()
    r = await get_redis()
    has_pending = await r.exists(f"pending_meal:{state['user'].phone}")

    if has_pending:
        if msg in _YES:
            response = await confirm_meal(state["user"], state["squad"], state["db"])
            return {"response": response, "intent": "__done__"}
        if msg in _NO:
            await r.delete(f"pending_meal:{state['user'].phone}")
            return {"response": "❌ Meal cancelled. Nothing was logged.", "intent": "__done__"}
        if not state["image_data"]:
            response = await correct_meal(state["message"], state["user"])
            return {"response": response, "intent": "__done__"}

    return {"intent": ""}


async def _supervisor(state: FitState) -> dict:
    # Photos always route to diet — no need to ask the LLM
    if state.get("image_data"):
        return {"intent": "diet"}

    ctx = await _goals_context(state["user"], state["db"])
    system = _SUPERVISOR_SYSTEM.format(
        user_name=state["user"].name or "User",
        goals_context=ctx,
    )
    raw = await _supervisor_llm.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=state["message"]),
    ])

    # with_structured_output may return a dict or a pydantic model depending on version
    if isinstance(raw, dict):
        next_val = raw.get("next", "general")
        direct = raw.get("direct_response", "")
    else:
        next_val = raw.next
        direct = raw.direct_response

    if next_val == "FINISH":
        return {"response": direct, "intent": "__done__"}

    return {"intent": next_val}


async def _diet(state: FitState) -> dict:
    response = await handle_diet(
        state["message"], state["user"], state["squad"], state["db"],
        state.get("image_data"), state.get("image_mimetype"),
    )
    return {"response": response}


async def _exercise(state: FitState) -> dict:
    return {"response": await handle_exercise(state["message"], state["user"], state["squad"], state["db"])}


async def _body_metrics(state: FitState) -> dict:
    return {"response": await handle_body_metrics(state["message"], state["user"], state["squad"], state["db"])}


async def _goal(state: FitState) -> dict:
    return {"response": await handle_goal(state["message"], state["user"], state["db"])}


async def _checkin(state: FitState) -> dict:
    return {"response": await handle_checkin(state["message"], state["user"], state["squad"], state["db"])}


async def _advice(state: FitState) -> dict:
    return {"response": await handle_advice(state["message"], state["user"], state["db"])}


async def _general(state: FitState) -> dict:
    return {"response": await handle_general(state["intent"], state["message"], state["user"], state["squad"], state["db"])}


# ── routing ────────────────────────────────────────────────────────────────────

def _route_pending(state: FitState) -> str:
    if state.get("intent") == "__done__":
        return END
    return "supervisor"


def _route_supervisor(state: FitState) -> str:
    if state.get("intent") == "__done__":
        return END
    return state.get("intent", "general")


# ── graph ──────────────────────────────────────────────────────────────────────

def _build_graph():
    g = StateGraph(FitState)

    g.add_node("check_pending", _check_pending)
    g.add_node("supervisor", _supervisor)
    g.add_node("diet", _diet)
    g.add_node("exercise", _exercise)
    g.add_node("body_metrics", _body_metrics)
    g.add_node("goal", _goal)
    g.add_node("checkin", _checkin)
    g.add_node("advice", _advice)
    g.add_node("general", _general)

    g.set_entry_point("check_pending")
    g.add_conditional_edges("check_pending", _route_pending)
    g.add_conditional_edges("supervisor", _route_supervisor)

    for node in ("diet", "exercise", "body_metrics", "goal", "checkin", "advice", "general"):
        g.add_edge(node, END)

    return g.compile()


_graph = _build_graph()


# ── public API ─────────────────────────────────────────────────────────────────

async def process(user: User, squad: Squad, message: str, db: AsyncSession,
                  image_data: str | None = None, image_mimetype: str | None = None) -> str:
    result = await _graph.ainvoke({
        "message": message,
        "user": user,
        "squad": squad,
        "db": db,
        "image_data": image_data,
        "image_mimetype": image_mimetype,
        "intent": "",
        "response": "",
    })
    return result["response"]
