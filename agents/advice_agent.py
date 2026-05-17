import cohere
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.chroma_client import get_knowledge_collection
from backend.models.db_models import User, UserGoals
from backend.core.config import settings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
co = cohere.AsyncClient(api_key=settings.COHERE_API_KEY)

SYSTEM_PROMPT = """You are FitBot, a personalised fitness and nutrition advisor inside a WhatsApp group.
You have access to retrieved fitness knowledge relevant to the user's question.
You also know the user's personal goal and current progress.

Rules:
- Be concise — WhatsApp messages should be readable on a phone
- Be specific and actionable — give concrete numbers and examples
- Use Indian food examples where relevant
- Reference the user's goal type when giving advice
- Use emojis sparingly for readability
- Never recommend supplements beyond basic protein powder or creatine
- Always end with one actionable tip the user can apply today
- Format: short paragraphs, max 200 words total"""


async def handle_advice(
    message: str,
    user: User,
    db: AsyncSession,
) -> str:
    goal_result = await db.execute(select(UserGoals).where(UserGoals.user_id == user.id))
    goals = goal_result.scalar_one_or_none()

    goal_context = ""
    if goals:
        goal_context = (
            f"User's goal: {goals.goal_type} | "
            f"Calorie target: {goals.daily_calories} kcal | "
            f"Protein target: {goals.protein_g}g | "
            f"Activity level: {goals.activity_level}"
        )

    query_vector = await embeddings.aembed_query(message)

    collection = get_knowledge_collection()
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=10,
        include=["documents", "metadatas", "distances"],
    )

    documents = results["documents"][0] if results["documents"] else []
    if not documents:
        goal_type = goals.goal_type if goals else "fitness"
        return (
            f"💡 Great question, {user.name}! I don't have specific data on that right now. "
            f"Based on your {goal_type} goal: focus on hitting your protein target and "
            f"training consistently — that covers 80% of your results."
        )

    rerank_response = await co.rerank(
        model="rerank-english-v3.0",
        query=message,
        documents=documents,
        top_n=3,
    )

    top_docs = [documents[r.index] for r in rerank_response.results]
    context = "\n\n".join(top_docs)

    prompt = f"""User question: {message}

User context: {goal_context if goal_context else "No goals set yet"}

Relevant knowledge:
{context}

Answer the question concisely and personally for this user."""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    response = await llm.ainvoke(messages)
    return f"💡 {response.content.strip()}"
