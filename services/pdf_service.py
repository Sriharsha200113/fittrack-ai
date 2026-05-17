from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER
import io
from datetime import date

PRIMARY = colors.HexColor("#22C55E")
DARK = colors.HexColor("#111827")
GRAY = colors.HexColor("#6B7280")
LIGHT = colors.HexColor("#F9FAFB")


def generate_monthly_pdf(data: dict) -> bytes:
    """Generate monthly report PDF. Returns bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    title_style = ParagraphStyle("Title", fontSize=22, textColor=PRIMARY, spaceAfter=4, alignment=TA_CENTER, fontName="Helvetica-Bold")
    subtitle_style = ParagraphStyle("Subtitle", fontSize=12, textColor=GRAY, spaceAfter=16, alignment=TA_CENTER)
    heading_style = ParagraphStyle("Heading", fontSize=14, textColor=DARK, spaceBefore=12, spaceAfter=6, fontName="Helvetica-Bold")
    body_style = ParagraphStyle("Body", fontSize=10, textColor=DARK, spaceAfter=4)
    footer_style = ParagraphStyle("Footer", fontSize=8, textColor=GRAY, alignment=TA_CENTER, spaceBefore=8)

    story = []
    g = data["goals"]

    story.append(Paragraph("FitSquad", title_style))
    story.append(Paragraph(f"Monthly Report — {data['month']}", subtitle_style))
    story.append(Paragraph(f"Prepared for: {data['user_name']}", body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=12))

    # Goal
    goal_labels = {
        "fat_loss": "Fat Loss", "muscle_gain": "Muscle Gain",
        "recomp": "Body Recomposition", "maintain": "Maintenance",
    }
    story.append(Paragraph("Your Goal", heading_style))
    story.append(Paragraph(goal_labels.get(g["goal_type"], "General Fitness"), body_style))
    if g.get("target_weight_kg"):
        story.append(Paragraph(f"Target weight: {g['target_weight_kg']} kg", body_style))
    story.append(Spacer(1, 8))

    # Activity summary
    story.append(Paragraph("Activity Summary", heading_style))
    activity_data = [
        ["Metric", "Value"],
        ["Active Days", f"{data['active_days']} / {data['total_days']}"],
        ["Workout Days", str(data["total_workout_days"])],
        ["Total Points", str(data["total_points"])],
        ["Best Day", f"{data['best_day_pts']} pts"],
        ["Current Streak", f"{data['current_streak']} days"],
        ["Longest Streak", f"{data['longest_streak']} days"],
    ]
    story.append(_make_table(activity_data))
    story.append(Spacer(1, 12))

    # Nutrition
    story.append(Paragraph("Nutrition (Daily Averages)", heading_style))
    nutrition_data = [
        ["Nutrient", "Average", "Target", "Status"],
        ["Calories", f"{data['avg_calories']} kcal", f"{g['daily_calories']} kcal", _status_icon(data["avg_calories"], g["daily_calories"])],
        ["Protein", f"{data['avg_protein']}g", f"{g['protein_g']}g", _status_icon(data["avg_protein"], g["protein_g"])],
        ["Carbohydrates", f"{data['avg_carbs']}g", "—", ""],
        ["Fat", f"{data['avg_fat']}g", "—", ""],
        ["Total Meals Logged", str(data["total_meals"]), "—", ""],
    ]
    story.append(_make_table(nutrition_data))
    story.append(Spacer(1, 12))

    # Weight trend
    if data["weight_logs"]:
        story.append(Paragraph("Weight Trend", heading_style))
        if data["weight_change"] is not None:
            direction = "↓" if data["weight_change"] < 0 else "↑"
            story.append(Paragraph(
                f"{data['first_weight']} kg → {data['last_weight']} kg  ({direction} {abs(data['weight_change'])} kg this month)",
                body_style,
            ))
        weight_table_data = [["Date", "Weight (kg)"]] + [
            [w["date"], str(w["weight"])] for w in data["weight_logs"]
        ]
        story.append(_make_table(weight_table_data))
        story.append(Spacer(1, 12))

    # Badges
    if data["all_badges"]:
        story.append(Paragraph("Badges Earned", heading_style))
        badge_rows = [["Badge", "Description"]] + [
            [f"{b['emoji']} {b['label']}", b["description"]]
            for b in data["all_badges"]
        ]
        story.append(_make_table(badge_rows))
        story.append(Spacer(1, 12))

    # Weekly snapshots
    if data["weekly_snapshots"]:
        story.append(Paragraph("Weekly Snapshots", heading_style))
        for snap in data["weekly_snapshots"]:
            week_label = f"Week of {snap['week_start']}"
            story.append(Paragraph(week_label, ParagraphStyle("WeekLabel", fontSize=11, textColor=DARK, fontName="Helvetica-Bold", spaceBefore=8)))
            rankings = snap.get("rankings", [])
            if rankings:
                rank_data = [["Rank", "Name", "Points"]] + [
                    [str(r.get("rank", i + 1)), r.get("user_name", "—"), str(r.get("points", 0))]
                    for i, r in enumerate(rankings[:5])
                ]
                story.append(_make_table(rank_data))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=GRAY))
    story.append(Paragraph(
        f"Generated by FitSquad on {date.today().strftime('%B %d, %Y')}",
        footer_style,
    ))

    doc.build(story)
    return buffer.getvalue()


def _make_table(data: list) -> Table:
    t = Table(data, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def _status_icon(actual: float, target: float) -> str:
    if not target:
        return ""
    pct = (actual / target) * 100
    if 90 <= pct <= 110:
        return "On track"
    elif pct < 90:
        return f"Low ({pct:.0f}%)"
    else:
        return f"Over ({pct:.0f}%)"
