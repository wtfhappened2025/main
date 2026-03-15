import uuid
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from database import db
from config import settings
from services.data_collector import get_seed_topics, SEED_EXPLANATIONS, collect_all_trending
from services.publisher import auto_publish_job

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler()


def get_scheduler() -> AsyncIOScheduler:
    return _scheduler


async def seed_initial_data():
    count = await db.topics.count_documents({})
    if count > 0:
        return
    logger.info("Seeding initial data...")
    seed_topics = get_seed_topics()
    now = datetime.now(timezone.utc).isoformat()
    for topic_data in seed_topics:
        topic_id = str(uuid.uuid4())
        topic = {
            "id": topic_id, "title": topic_data["title"],
            "category": topic_data["category"], "source": topic_data["source"],
            "trend_score": topic_data["trend_score"], "created_at": now,
        }
        await db.topics.insert_one(topic)
        if topic_data["title"] in SEED_EXPLANATIONS:
            exp_data = SEED_EXPLANATIONS[topic_data["title"]]
            explanation = {
                "id": str(uuid.uuid4()), "topic_id": topic_id,
                "topic_title": topic_data["title"],
                "normalized_question": topic_data["title"],
                "card_1": exp_data["card_1"], "card_2": exp_data["card_2"], "card_3": exp_data["card_3"],
                "card_1_detail": exp_data.get("card_1_detail", ""),
                "card_2_detail": exp_data.get("card_2_detail", ""),
                "card_3_detail": exp_data.get("card_3_detail", ""),
                "category": exp_data.get("category", topic_data["category"]),
                "visual_type": None, "created_at": now,
            }
            await db.explanations.insert_one(explanation)
    logger.info(f"Seeded {len(seed_topics)} topics")


async def ingest_trending_data():
    try:
        new_topics = await collect_all_trending()
        now = datetime.now(timezone.utc).isoformat()
        added = 0
        for topic_data in new_topics:
            existing = await db.topics.find_one({"title": topic_data["title"]})
            if existing:
                continue
            topic = {
                "id": str(uuid.uuid4()), "title": topic_data["title"],
                "category": topic_data["category"], "source": topic_data["source"],
                "trend_score": topic_data["trend_score"], "created_at": now,
            }
            await db.topics.insert_one(topic)
            added += 1
        logger.info(f"Ingested {added} new trending topics")
        await db.system_meta.update_one(
            {"key": "last_data_refresh"},
            {"$set": {"key": "last_data_refresh", "value": now}},
            upsert=True,
        )
    except Exception as e:
        logger.error(f"Trending data ingestion failed: {e}")


async def start_scheduler():
    _scheduler.add_job(
        ingest_trending_data,
        trigger=IntervalTrigger(minutes=settings.DATA_REFRESH_MINUTES),
        id="data_refresh", replace_existing=True,
    )
    _scheduler.add_job(
        auto_publish_job,
        trigger=IntervalTrigger(minutes=30),
        id="auto_publisher", replace_existing=True,
    )
    _scheduler.start()
    logger.info(f"Scheduler started. Data refresh every {settings.DATA_REFRESH_MINUTES}min. Auto-publisher every 30min.")


def stop_scheduler():
    _scheduler.shutdown(wait=False)
