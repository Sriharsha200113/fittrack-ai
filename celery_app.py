import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery = Celery(
    "fitsquad",
    broker=REDIS_URL,
    backend=REDIS_URL.rsplit("/", 1)[0] + "/1",
)

celery.conf.timezone = "Asia/Kolkata"

celery.conf.beat_schedule = {
    "morning-ping": {
        "task": "backend.tasks.scheduled.morning_ping",
        "schedule": crontab(hour=8, minute=0),
    },
    "evening-reminder": {
        "task": "backend.tasks.scheduled.evening_reminder",
        "schedule": crontab(hour=20, minute=30),
    },
    "eod-summary": {
        "task": "backend.tasks.scheduled.eod_summary",
        "schedule": crontab(hour=22, minute=0),
    },
    "weekly-reset": {
        "task": "backend.tasks.scheduled.weekly_reset",
        "schedule": crontab(hour=23, minute=55, day_of_week=0),  # Sunday
    },
    "weekly-reports": {
        "task": "backend.tasks.scheduled.weekly_reports",
        "schedule": crontab(hour=22, minute=0, day_of_week=0),  # Sunday 10 PM
    },
    "monthly-reports": {
        "task": "backend.tasks.scheduled.monthly_reports",
        "schedule": crontab(hour=21, minute=0),  # daily 9 PM, task checks if last day
    },
}
