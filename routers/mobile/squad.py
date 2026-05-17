from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from backend.db.session import get_db
from backend.core.deps import get_current_user
from backend.models.db_models import User, Squad, SquadMember
from backend.services.leaderboard_service import get_daily_leaderboard, get_weekly_leaderboard

router = APIRouter(prefix="/squad", tags=["squad"])


class RenameRequest(BaseModel):
    name: str


async def _get_user_squad(user: User, db: AsyncSession) -> Squad:
    result = await db.execute(
        select(Squad)
        .join(SquadMember, SquadMember.squad_id == Squad.id)
        .where(SquadMember.user_id == user.id)
    )
    squad = result.scalar_one_or_none()
    if not squad:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No squad found")
    return squad


@router.get("/")
async def get_squad(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    squad = await _get_user_squad(current_user, db)
    members_result = await db.execute(
        select(User).join(SquadMember, SquadMember.user_id == User.id).where(SquadMember.squad_id == squad.id)
    )
    members = members_result.scalars().all()
    return {
        "id": str(squad.id),
        "name": squad.name,
        "invite_code": squad.invite_code,
        "member_count": len(members),
        "members": [{"id": str(m.id), "name": m.name, "phone": m.phone} for m in members],
    }


@router.get("/leaderboard/daily")
async def daily_leaderboard(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    squad = await _get_user_squad(current_user, db)
    board = await get_daily_leaderboard(str(squad.id), date.today(), db)
    return {"date": date.today().isoformat(), "leaderboard": board}


@router.get("/leaderboard/weekly")
async def weekly_leaderboard(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    squad = await _get_user_squad(current_user, db)
    board = await get_weekly_leaderboard(str(squad.id), date.today(), db)
    return {"week": date.today().isocalendar()._asdict(), "leaderboard": board}


@router.patch("/rename")
async def rename_squad(body: RenameRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    squad = await _get_user_squad(current_user, db)
    squad.name = body.name
    await db.commit()
    return {"id": str(squad.id), "name": squad.name}


@router.post("/leave")
async def leave_squad(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    squad = await _get_user_squad(current_user, db)
    await db.execute(
        delete(SquadMember).where(SquadMember.squad_id == squad.id, SquadMember.user_id == current_user.id)
    )
    await db.commit()
    return {"message": "Left squad successfully"}
