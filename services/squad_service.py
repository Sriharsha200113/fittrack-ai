import random
import string
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.db_models import Squad, SquadMember, User


def _generate_invite_code(length: int = 6) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


async def get_or_create_squad(wa_group_id: str, db: AsyncSession) -> Squad:
    result = await db.execute(select(Squad).where(Squad.wa_group_id == wa_group_id))
    squad = result.scalar_one_or_none()

    if not squad:
        invite_code = _generate_invite_code()
        squad = Squad(
            name=f"FitSquad-{invite_code}",
            invite_code=invite_code,
            wa_group_id=wa_group_id,
        )
        db.add(squad)
        await db.commit()
        await db.refresh(squad)

    return squad


async def ensure_member(user: User, squad: Squad, db: AsyncSession):
    result = await db.execute(
        select(SquadMember).where(
            SquadMember.user_id == user.id,
            SquadMember.squad_id == squad.id,
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        member = SquadMember(user_id=user.id, squad_id=squad.id)
        db.add(member)
        await db.commit()
