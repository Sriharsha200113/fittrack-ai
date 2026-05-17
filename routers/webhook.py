from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.schemas.webhook import WhatsAppWebhook, DMWebhook, GroupJoinWebhook, WebhookResponse, GroupJoinResponse
from backend.services.user_service import get_or_create_user
from backend.services.squad_service import get_or_create_squad, ensure_member
from backend.agents.supervisor import process
from backend.agents.onboarding_agent import handle_onboarding
from backend.models.db_models import User
from backend.db.session import get_db

router = APIRouter()


@router.post("/webhook/dm", response_model=WebhookResponse)
async def dm_webhook(
    payload: DMWebhook,
    db: AsyncSession = Depends(get_db),
):
    user = await get_or_create_user(payload.phone, payload.sender_name, db)
    if user.is_onboarded:
        return WebhookResponse(reply=(
            f"✅ You're already registered, {user.name}!\n\n"
            f"Head to the group and tag me to log your meals and workouts.\n"
            f"E.g. _@FitBot had chicken rice for lunch_ 💪"
        ))
    reply = await handle_onboarding(payload.message, user, db)
    return WebhookResponse(reply=reply)


@router.post("/webhook/group-join", response_model=GroupJoinResponse)
async def group_join_webhook(
    payload: GroupJoinWebhook,
    db: AsyncSession = Depends(get_db),
):
    registered = []
    unregistered_phones = []

    for phone in payload.member_phones:
        result = await db.execute(select(User).where(User.phone == phone))
        user = result.scalar_one_or_none()
        if user and user.is_onboarded:
            registered.append(user.name or f"+{phone}")
        else:
            unregistered_phones.append(phone)

    lines = ["👋 *FitSquad has joined the group!*\n"]

    if registered:
        lines.append(f"✅ *Ready to track ({len(registered)}):*")
        for name in registered:
            lines.append(f"  • {name}")

    if unregistered_phones:
        lines.append(f"\n⏳ *Not registered yet ({len(unregistered_phones)}):*")
        for phone in unregistered_phones:
            lines.append(f"  • +{phone}")
        lines.append("\n📩 I've sent them a DM to get started!")

    lines += [
        "\n*How to use me:*",
        "Tag me in any message — @FitBot",
        "_@FitBot had chicken rice for lunch_",
        "_@FitBot 45 min gym session_",
        "_@FitBot stats_",
    ]

    dm_invites = [
        {
            "phone": phone,
            "message": (
                "👋 Hey! You've been added to a *FitSquad* group.\n\n"
                "Reply to this message to register and set up your fitness goals. "
                "It takes under 2 minutes! 💪\n\n"
                "Once registered, you can log meals, workouts, and compete with your squad."
            ),
        }
        for phone in unregistered_phones
    ]

    return GroupJoinResponse(reply="\n".join(lines), dm_invites=dm_invites)


@router.post("/webhook/whatsapp", response_model=WebhookResponse)
async def whatsapp_webhook(
    payload: WhatsAppWebhook,
    db: AsyncSession = Depends(get_db),
):
    user = await get_or_create_user(payload.phone, payload.sender_name, db)
    if not user.is_onboarded:
        return WebhookResponse(reply=(
            f"👋 Hey {user.name or 'there'}! You need to register first.\n\n"
            f"📩 *DM this number directly* to set up your profile and goals. "
            f"It only takes 2 minutes!"
        ))
    squad = await get_or_create_squad(payload.group_id, db)
    await ensure_member(user, squad, db)
    reply = await process(user, squad, payload.message, db, payload.image_data, payload.image_mimetype)
    return WebhookResponse(reply=reply)
