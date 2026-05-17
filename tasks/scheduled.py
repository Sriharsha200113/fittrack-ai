import asyncio
from datetime import date, timedelta
from calendar import monthrange
from uuid import UUID
from sqlalchemy import select
from backend.celery_app import celery
from backend.db.session import AsyncSessionLocal
from backend.models.db_models import Squad, SquadMember, User, DailyPoints, WeeklySnapshot, DeviceToken
from backend.services.leaderboard_service import get_daily_leaderboard, get_weekly_leaderboard
from backend.services.streak_service import get_streak
from backend.services.badge_service import _award_badge_if_new
from backend.services.whatsapp_service import send_message, send_pdf
from backend.services.push_service import send_push

MEDALS = ["🥇", "🥈", "🥉"]


async def _send_notification_to_user(user: User, title: str, body: str, db) -> None:
    result = await db.execute(
        select(DeviceToken).where(DeviceToken.user_id == user.id, DeviceToken.is_active == True)
    )
    tokens = result.scalars().all()
    for device in tokens:
        await send_push(device.token, title, body)


# ─── MORNING PING (8:00 AM IST) ───────────────────────────────────────────────

@celery.task
def morning_ping():
    asyncio.run(_morning_ping())


async def _morning_ping():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Squad))
        squads = result.scalars().all()
        today = date.today()
        for squad in squads:
            msg = (
                f"🌅 *Good morning {squad.name}!*\n\n"
                f"📅 {today.strftime('%A, %B %d')}\n\n"
                f"Today's game plan:\n"
                f"🍽️ Log your meals\n"
                f"🏋️ Log your workouts\n"
                f"⚖️ Log your weight\n\n"
                f"Type *leaderboard* for rankings, *stats* for your targets 🏆"
            )
            await send_message(squad.wa_group_id, msg)

            members_result = await db.execute(
                select(User).join(SquadMember, SquadMember.user_id == User.id).where(
                    SquadMember.squad_id == squad.id
                )
            )
            for member in members_result.scalars().all():
                await _send_notification_to_user(
                    member, "Good morning! 🌅", f"Time to log for {today.strftime('%A')}!", db
                )


# ─── EVENING REMINDER (8:30 PM IST) ──────────────────────────────────────────

@celery.task
def evening_reminder():
    asyncio.run(_evening_reminder())


async def _evening_reminder():
    today = date.today()
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Squad))
        squads = result.scalars().all()

        for squad in squads:
            members_result = await db.execute(
                select(User).join(SquadMember, SquadMember.user_id == User.id).where(
                    SquadMember.squad_id == squad.id
                )
            )
            members = members_result.scalars().all()

            inactive_names = []
            inactive_members = []
            for member in members:
                dp_result = await db.execute(
                    select(DailyPoints).where(
                        DailyPoints.user_id == member.id,
                        DailyPoints.squad_id == squad.id,
                        DailyPoints.date == today,
                    )
                )
                dp = dp_result.scalar_one_or_none()
                if not dp or (dp.meals_logged == 0 and dp.workouts_logged == 0):
                    inactive_names.append(member.name or member.phone)
                    inactive_members.append(member)

            if inactive_names:
                names = ", ".join(inactive_names)
                msg = (
                    f"⏰ *Reminder!*\n\n"
                    f"Hey {names} — log your meals and workouts before midnight!\n"
                    f"Don't lose your streak 🔥 Points reset at midnight!"
                )
                await send_message(squad.wa_group_id, msg)

            for member in inactive_members:
                await _send_notification_to_user(
                    member, "⏰ Don't forget!", "Log your meals and workouts before midnight!", db
                    )


# ─── EOD SQUAD SUMMARY (10:00 PM IST) ────────────────────────────────────────

@celery.task
def eod_summary():
    asyncio.run(_eod_summary())


async def _eod_summary():
    today = date.today()
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Squad))
        squads = result.scalars().all()

        for squad in squads:
            entries = await get_daily_leaderboard(str(squad.id), today, db)
            if not entries:
                continue

            lines = [f"🏆 *{squad.name} — Daily Summary*", f"📅 {today.strftime('%A, %B %d')}\n"]

            for i, entry in enumerate(entries):
                medal = MEDALS[i] if i < 3 else f"{i+1}."
                streak_data = await get_streak(entry["user_id"])
                streak = streak_data["current_streak"]
                streak_str = f" 🔥{streak}" if streak > 1 else ""
                lines.append(f"{medal} {entry['user_name']} — {entry['points']} pts{streak_str}")

            mvp = entries[0]
            lines.append(f"\n👑 Today's MVP: *{mvp['user_name']}* with {mvp['points']} pts!")

            weekly = await get_weekly_leaderboard(str(squad.id), today, db)
            if weekly:
                lines.append(f"\n📊 Weekly standings:")
                for i, entry in enumerate(weekly[:3]):
                    medal = MEDALS[i] if i < 3 else f"{i+1}."
                    lines.append(f"{medal} {entry['user_name']} — {entry['points']} pts")

            lines.append("\nKeep going tomorrow! 💪")
            await send_message(squad.wa_group_id, "\n".join(lines))


# ─── WEEKLY RESET (Sunday 11:55 PM IST) ──────────────────────────────────────

@celery.task
def weekly_reset():
    asyncio.run(_weekly_reset())


async def _weekly_reset():
    today = date.today()  # Sunday
    week_start = today - timedelta(days=6)  # Monday

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Squad))
        squads = result.scalars().all()

        for squad in squads:
            weekly = await get_weekly_leaderboard(str(squad.id), today, db)
            if not weekly:
                continue

            lines = [
                f"🏆 *{squad.name} — Weekly Report*",
                f"📅 {week_start.strftime('%b %d')} – {today.strftime('%b %d')}\n",
            ]

            for i, entry in enumerate(weekly):
                medal = MEDALS[i] if i < 3 else f"{i+1}."
                lines.append(f"{medal} {entry['user_name']} — {entry['points']} pts")

            winner_user = None
            if weekly:
                winner = weekly[0]
                lines.append(f"\n🎉 *Weekly Champion: {winner['user_name']}!* 🏆")

                winner_result = await db.execute(
                    select(User).where(User.id == UUID(winner["user_id"]))
                )
                winner_user = winner_result.scalar_one_or_none()
                if winner_user:
                    await _award_badge_if_new(winner_user.id, "weekly_winner", db)

            snapshot = WeeklySnapshot(
                squad_id=squad.id,
                week_start=week_start,
                week_end=today,
                rankings=weekly,
                winner_user_id=winner_user.id if winner_user else None,
            )
            db.add(snapshot)
            await db.commit()

            lines.append("\nNew week starts tomorrow. Let's go! 🚀")
            await send_message(squad.wa_group_id, "\n".join(lines))


# ─── WEEKLY REPORTS (Sunday 10:00 PM IST) ────────────────────────────────────

@celery.task
def weekly_reports():
    asyncio.run(_weekly_reports())


async def _weekly_reports():
    from backend.services.report_service import get_weekly_report_data, format_weekly_report_text

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Squad))
        squads = result.scalars().all()

        for squad in squads:
            members_result = await db.execute(
                select(User).join(SquadMember, SquadMember.user_id == User.id).where(
                    SquadMember.squad_id == squad.id
                )
            )
            members = members_result.scalars().all()

            for member in members:
                data = await get_weekly_report_data(member, db)
                text = format_weekly_report_text(data)
                await send_message(squad.wa_group_id, f"📊 Report for {member.name}:\n\n{text}")


# ─── MONTHLY REPORTS (Last day of month, 9:00 PM IST) ────────────────────────

@celery.task
def monthly_reports():
    asyncio.run(_monthly_reports())


async def _monthly_reports():
    from backend.services.report_service import get_monthly_report_data
    from backend.services.pdf_service import generate_monthly_pdf

    today = date.today()
    _, last_day = monthrange(today.year, today.month)
    if today.day != last_day:
        return  # Only run on the last day of the month

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Squad))
        squads = result.scalars().all()

        for squad in squads:
            members_result = await db.execute(
                select(User).join(SquadMember, SquadMember.user_id == User.id).where(
                    SquadMember.squad_id == squad.id
                )
            )
            members = members_result.scalars().all()

            for member in members:
                data = await get_monthly_report_data(member, db)
                pdf_bytes = generate_monthly_pdf(data)
                filename = f"fitsquad_{member.name}_{today.strftime('%Y_%m')}"
                caption = (
                    f"📊 {member.name}'s Monthly Report — {data['month']} | "
                    f"{data['total_points']} pts | {data['active_days']} active days"
                )
                await send_pdf(squad.wa_group_id, pdf_bytes, filename, caption)
