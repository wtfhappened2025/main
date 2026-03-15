import logging
from fastapi import APIRouter, BackgroundTasks

from database import db, check_connection
from config import settings

router = APIRouter(prefix="/api", tags=["system"])
logger = logging.getLogger(__name__)


@router.get("/")
async def root():
    return {"message": "WTFHappened API", "status": "running"}


@router.get("/health")
async def health():
    db_ok = await check_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "environment": settings.ENVIRONMENT,
    }


@router.post("/refresh-trending")
async def refresh_trending(background_tasks: BackgroundTasks):
    from services.scheduler import ingest_trending_data
    background_tasks.add_task(ingest_trending_data)
    return {"message": "Refresh started"}


@router.get("/scheduler/status")
async def scheduler_status():
    from services.scheduler import get_scheduler
    sched = get_scheduler()
    job = sched.get_job("data_refresh") if sched else None
    if job:
        next_run = job.next_run_time.isoformat() if job.next_run_time else None
        return {"running": sched.running, "next_run": next_run, "interval_minutes": settings.DATA_REFRESH_MINUTES}
    return {"running": False, "next_run": None, "interval_minutes": settings.DATA_REFRESH_MINUTES}


@router.get("/admin/scheduler")
async def admin_scheduler_status():
    from services.scheduler import get_scheduler
    sched = get_scheduler()
    job = sched.get_job("data_refresh") if sched else None
    last_refresh = await db.system_meta.find_one({"key": "last_data_refresh"}, {"_id": 0})
    pub_job = sched.get_job("auto_publisher") if sched else None
    last_publish = await db.system_meta.find_one({"key": "last_auto_publish"}, {"_id": 0})
    return {
        "data_refresh": {
            "running": job is not None,
            "next_run": job.next_run_time.isoformat() if job and job.next_run_time else None,
            "interval_minutes": settings.DATA_REFRESH_MINUTES,
            "last_run": last_refresh.get("value") if last_refresh else None,
        },
        "auto_publisher": {
            "running": pub_job is not None,
            "next_run": pub_job.next_run_time.isoformat() if pub_job and pub_job.next_run_time else None,
            "last_run": last_publish.get("value") if last_publish else None,
        },
    }
