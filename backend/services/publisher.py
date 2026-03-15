import uuid
import logging
import hashlib
import hmac
import time
import urllib.parse
import base64
import httpx
from datetime import datetime, timezone

from database import db
from config import settings

logger = logging.getLogger(__name__)


async def select_top_cards(limit: int = 3) -> list:
    topics = await db.topics.find({"trend_score": {"$gte": 70}}, {"_id": 0}).sort("trend_score", -1).limit(limit * 2).to_list(limit * 2)
    publishable = []
    for topic in topics:
        explanation = await db.explanations.find_one({"topic_id": topic["id"]}, {"_id": 0})
        if not explanation:
            continue
        already = await db.published_cards.find_one({"topic_id": topic["id"]})
        if already:
            continue
        publishable.append({"topic": topic, "explanation": explanation})
        if len(publishable) >= limit:
            break
    return publishable


async def publish_to_x(title: str, card_1: str, card_2: str, card_3: str, topic_id: str) -> dict:
    if not all([settings.X_API_KEY, settings.X_API_SECRET, settings.X_ACCESS_TOKEN, settings.X_ACCESS_SECRET]):
        return {"status": "skipped", "reason": "X OAuth 1.0a write credentials not configured"}
    try:
        tweet_text = f"WTF just happened?\n\n{title}\n\n"
        tweet_text += f"What: {card_1[:80]}\nWhy: {card_2[:80]}\nYou: {card_3[:80]}\n\n"
        tweet_text += "#WTFHappened #Explained"
        if len(tweet_text) > 280:
            tweet_text = tweet_text[:277] + "..."
        url = "https://api.x.com/2/tweets"
        timestamp = str(int(time.time()))
        nonce = uuid.uuid4().hex
        params = {
            "oauth_consumer_key": settings.X_API_KEY, "oauth_nonce": nonce,
            "oauth_signature_method": "HMAC-SHA256", "oauth_timestamp": timestamp,
            "oauth_token": settings.X_ACCESS_TOKEN, "oauth_version": "1.0",
        }
        param_str = "&".join(f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}" for k, v in sorted(params.items()))
        base_string = f"POST&{urllib.parse.quote(url, safe='')}&{urllib.parse.quote(param_str, safe='')}"
        signing_key = f"{urllib.parse.quote(settings.X_API_SECRET, safe='')}&{urllib.parse.quote(settings.X_ACCESS_SECRET, safe='')}"
        signature = base64.b64encode(hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha256).digest()).decode()
        auth_header = (
            f'OAuth oauth_consumer_key="{urllib.parse.quote(settings.X_API_KEY, safe="")}", '
            f'oauth_nonce="{nonce}", oauth_signature="{urllib.parse.quote(signature, safe="")}", '
            f'oauth_signature_method="HMAC-SHA256", oauth_timestamp="{timestamp}", '
            f'oauth_token="{urllib.parse.quote(settings.X_ACCESS_TOKEN, safe="")}", oauth_version="1.0"'
        )
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json={"text": tweet_text}, headers={"Authorization": auth_header, "Content-Type": "application/json"})
            if resp.status_code in (200, 201):
                return {"status": "published", "tweet_id": resp.json().get("data", {}).get("id")}
            return {"status": "failed", "error": resp.text[:200], "status_code": resp.status_code}
    except Exception as e:
        logger.error(f"X publishing failed: {e}")
        return {"status": "failed", "error": str(e)}


async def auto_publish_job():
    try:
        cards = await select_top_cards(limit=2)
        if not cards:
            logger.info("Auto-publisher: No new cards to publish")
            return
        for item in cards:
            topic, exp = item["topic"], item["explanation"]
            results = {"x_twitter": await publish_to_x(topic["title"], exp["card_1"], exp["card_2"], exp["card_3"], topic["id"])}
            await db.published_cards.insert_one({
                "id": str(uuid.uuid4()), "topic_id": topic["id"],
                "topic_title": topic["title"], "platforms": results,
                "published_at": datetime.now(timezone.utc).isoformat(),
            })
            logger.info(f"Auto-published: {topic['title'][:60]} -> {results}")
        await db.system_meta.update_one(
            {"key": "last_auto_publish"},
            {"$set": {"key": "last_auto_publish", "value": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )
    except Exception as e:
        logger.error(f"Auto-publish job failed: {e}")
