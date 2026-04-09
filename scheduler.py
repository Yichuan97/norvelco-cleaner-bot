"""
Background scheduler — runs daily tasks at configured times.
Uses asyncio + APScheduler for reliable cron-like scheduling.
"""

import logging
import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from config import settings

logger = logging.getLogger(__name__)


async def start_scheduler():
    """Start the APScheduler with all daily jobs."""
    # Import here to avoid circular imports
    from main import task_manager

    tz = pytz.timezone(settings.TIMEZONE)
    scheduler = AsyncIOScheduler(timezone=tz)

    # ── 7:30 AM: Bad review warnings (before cleaners start) ─────────────────
    scheduler.add_job(
        task_manager.check_and_warn_bad_reviews,
        CronTrigger(
            hour=settings.REVIEW_CHECK_HOUR,
            minute=settings.REVIEW_CHECK_MINUTE,
            timezone=tz
        ),
        id="bad_review_warnings",
        name="Bad Review Warnings",
        replace_existing=True
    )

    # ── 8:00 AM: Daily task dispatch ──────────────────────────────────────────
    scheduler.add_job(
        task_manager.dispatch_daily_tasks,
        CronTrigger(
            hour=settings.DAILY_TASK_HOUR,
            minute=settings.DAILY_TASK_MINUTE,
            timezone=tz
        ),
        id="daily_task_dispatch",
        name="Daily Task Dispatch",
        replace_existing=True
    )

    # ── 6:00 PM: Celebrate good reviews ────────────────────────────────────────
    scheduler.add_job(
        task_manager.celebrate_good_reviews,
        CronTrigger(
            hour=settings.CELEBRATE_HOUR,
            minute=settings.CELEBRATE_MINUTE,
            timezone=tz
        ),
        id="celebrate_reviews",
        name="Celebrate Good Reviews",
        replace_existing=True
    )

    scheduler.start()
    logger.info(
        f"⏰ Scheduler started (timezone: {settings.TIMEZONE})\n"
        f"   • {settings.REVIEW_CHECK_HOUR:02d}:{settings.REVIEW_CHECK_MINUTE:02d} — Bad review warnings\n"
        f"   • {settings.DAILY_TASK_HOUR:02d}:{settings.DAILY_TASK_MINUTE:02d} — Daily task dispatch\n"
        f"   • {settings.CELEBRATE_HOUR:02d}:{settings.CELEBRATE_MINUTE:02d} — Celebrate good reviews"
    )

    # Keep scheduler running
    try:
        while True:
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        scheduler.shutdown()
        logger.info("⏰ Scheduler stopped")
