import logging
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

logger = logging.getLogger(__name__)

client = AsyncIOMotorClient(
    settings.MONGO_URL,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    retryWrites=True,
    retryReads=True,
)
db = client[settings.DB_NAME]


async def check_connection() -> bool:
    try:
        await db.command("ping")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


async def create_indexes():
    try:
        await db.topics.create_index("id", unique=True)
        await db.topics.create_index("trend_score")
        await db.topics.create_index("category")
        await db.topics.create_index("title")
        await db.explanations.create_index("topic_id")
        await db.saved_topics.create_index("topic_id")
        await db.saved_topics.create_index("user_id")
        await db.users.create_index("id", unique=True)
        await db.users.create_index("email", sparse=True)
        await db.users.create_index("mobile", sparse=True)
        await db.payment_transactions.create_index("session_id")
        await db.payment_transactions.create_index("user_id")
        await db.password_resets.create_index("token")
        await db.ai_prompts.create_index("prompt_key")
        await db.published_cards.create_index("topic_id")
        await db.system_meta.create_index("key", unique=True)
        logger.info("Database indexes created")
    except Exception as e:
        logger.error(f"Index creation failed: {e}")
