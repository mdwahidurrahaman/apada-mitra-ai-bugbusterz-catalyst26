import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import SessionLocal
from app.services.alert_engine import run_alert_pipeline
from app.config import settings

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")


async def scheduled_job():
    logger.info("[SCHEDULER] Alert pipeline triggered")
    db = SessionLocal()
    try:
        count = await run_alert_pipeline(db)
        logger.info(f"[SCHEDULER] Done — {count} alerts triggered")
    except Exception as e:
        logger.error(f"[SCHEDULER] Failed: {e}")
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        scheduled_job,
        trigger="interval",
        minutes=settings.CRON_INTERVAL_MINUTES,
        id="alert_pipeline",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        f"[SCHEDULER] Started — every {settings.CRON_INTERVAL_MINUTES} min")
