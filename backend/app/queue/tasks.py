from celery.schedules import crontab
from sqlalchemy import select

from app.container import build_orchestrator
from app.db import SessionLocal
from app.models.source import Source
from app.queue.celery_app import celery_app
from app.utils.logging import get_logger


logger = get_logger("celery-tasks")


@celery_app.task(name="process_source")
def process_source(source_id: int, user_profile: str = "") -> dict:
    orchestrator = build_orchestrator()
    with SessionLocal() as db:
        result = orchestrator.run_source(db, source_id=source_id, user_profile=user_profile)
        return {
            "source_id": result.source_id,
            "discovered_links": result.discovered_links,
            "extracted_jobs": result.extracted_jobs,
            "failed_links": result.failed_links,
            "errors": result.errors,
        }


@celery_app.task(name="refresh_active_sources")
def refresh_active_sources() -> int:
    with SessionLocal() as db:
        stmt = select(Source.id).where(Source.status == "active")
        source_ids = [row[0] for row in db.execute(stmt).all()]
    for source_id in source_ids:
        process_source.delay(source_id=source_id, user_profile="")
    logger.info(
        "Queued active sources",
        extra={"context": {"count": len(source_ids)}},
    )
    return len(source_ids)


celery_app.conf.beat_schedule = {
    "refresh-sources-every-15-minutes": {
        "task": "refresh_active_sources",
        "schedule": crontab(minute="*/15"),
    }
}
