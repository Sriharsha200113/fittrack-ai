from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

SYSTEM_PROMPT = """You are an intent classifier for a fitness tracking WhatsApp bot.
Classify the user message into exactly one of these intents:
- diet: user is logging food, meals, what they ate or drank (e.g. "had chicken rice", "ate 2 eggs for breakfast")
- exercise: user is logging a workout, gym session, run, steps, or any physical activity
- body_metrics: user is logging their body weight, body fat percentage, or measurements
- goal_setting: user wants to set or view their fitness goals or targets
- leaderboard: user wants to see rankings, points, or who is winning
- stats: user wants to see their personal stats, daily summary, macros, what they ate today, what meals they had, what exercises they did, their report, weekly report, or monthly report
  e.g. "what did I eat today", "what have I eaten", "what i ate today", "show my meals", "what exercise did I do", "my stats", "my report", "report", "stats"
- check_in: user is doing a morning or evening check-in (gm, good morning, done for the day, etc)
- advice: user is asking a fitness or nutrition question, wants recommendations or guidance
  e.g. "what should I eat for fat loss", "best exercises for chest", "how much protein do I need",
       "is rice bad for weight loss", "what to eat before gym", "how to lose belly fat"
- unknown: anything else

Respond with ONLY the intent word. No explanation, no punctuation."""

VALID_INTENTS = {
    "diet", "exercise", "body_metrics", "goal_setting",
    "leaderboard", "stats", "check_in", "advice", "unknown",
}


async def classify_intent(message: str) -> str:
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=message),
    ]
    response = await llm.ainvoke(messages)
    intent = response.content.strip().lower()
    if intent not in VALID_INTENTS:
        return "unknown"
    return intent
