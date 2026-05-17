from datetime import date
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.session import get_db
from backend.core.deps import get_current_user
from backend.models.db_models import User, WeeklySnapshot, SquadMember
from backend.services.report_service import get_weekly_report_data, get_monthly_report_data
from backend.services.pdf_service import generate_monthly_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/weekly")
async def get_weekly_report(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    data = await get_weekly_report_data(current_user, db)
    return data


@router.get("/monthly/pdf")
async def get_monthly_pdf(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    data = await get_monthly_report_data(current_user, db)
    pdf_bytes = generate_monthly_pdf(data)
    month_label = date.today().strftime("%Y-%m")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="report_{month_label}.pdf"'},
    )


@router.get("/weekly/history")
async def get_weekly_history(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    squad_result = await db.execute(
        select(SquadMember.squad_id).where(SquadMember.user_id == current_user.id)
    )
    squad_ids = [row[0] for row in squad_result.all()]

    if not squad_ids:
        return {"history": []}

    result = await db.execute(
        select(WeeklySnapshot)
        .where(WeeklySnapshot.squad_id.in_(squad_ids))
        .order_by(WeeklySnapshot.week_start.desc())
        .limit(12)
    )
    snapshots = result.scalars().all()
    return {
        "history": [
            {
                "week_start": s.week_start.isoformat(),
                "week_end": s.week_end.isoformat(),
                "rankings": s.rankings,
                "winner_user_id": str(s.winner_user_id) if s.winner_user_id else None,
            }
            for s in snapshots
        ]
    }
