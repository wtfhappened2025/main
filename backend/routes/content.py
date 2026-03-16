import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from database import db
from utils.security import get_current_user
from utils.helpers import time_ago, CATEGORY_COLORS, INTEREST_TO_CATEGORY
from models import ExplainRequest
from services.ai_engine import generate_explanation, generate_caption

router = APIRouter(prefix="/api", tags=["content"])
logger = logging.getLogger(__name__)


@router.get("/feed")
async def get_feed(limit: int = 20, category: Optional[str] = None):
    query = {}
    if category and category != "all":
        query["category"] = category
    topics = await db.topics.find(query, {"_id": 0}).sort("trend_score", -1).limit(limit).to_list(limit)
    for t in topics:
        exp = await db.explanations.find_one({"topic_id": t["id"]}, {"_id": 0, "id": 1})
        t["has_explanation"] = exp is not None
        t["time_ago"] = time_ago(t.get("created_at", ""))
    return {"topics": topics}


@router.get("/feed/personalized")
async def get_personalized_feed(limit: int = 30, user=Depends(get_current_user)):
    prefs = user.get("preferences", {})
    interests = [i.lower() for i in prefs.get("interests", [])]
    followed = [f.lower() for f in prefs.get("followed_topics", [])]

    preferred_cats = list(set(
        INTEREST_TO_CATEGORY.get(i, "world_news") for i in interests
    ))
    followed_keywords = followed + [i for i in interests if i not in INTEREST_TO_CATEGORY]

    all_topics = await db.topics.find({}, {"_id": 0}).sort("trend_score", -1).limit(200).to_list(200)

    def relevance_score(topic):
        score = topic.get("trend_score", 0)
        if topic.get("category", "") in preferred_cats:
            score += 25
        title_lower = topic.get("title", "").lower()
        for kw in followed_keywords:
            if kw in title_lower:
                score += 30
                break
        return score

    all_topics.sort(key=relevance_score, reverse=True)
    topics = all_topics[:limit]
    for t in topics:
        exp = await db.explanations.find_one({"topic_id": t["id"]}, {"_id": 0, "id": 1})
        t["has_explanation"] = exp is not None
        t["time_ago"] = time_ago(t.get("created_at", ""))
        t["personalized"] = True
    return {"topics": topics, "preferences_used": {"categories": preferred_cats, "keywords": followed_keywords[:5]}}


@router.get("/explanation/{topic_id}")
async def get_explanation(topic_id: str):
    explanation = await db.explanations.find_one({"topic_id": topic_id}, {"_id": 0})
    if not explanation:
        topic = await db.topics.find_one({"id": topic_id}, {"_id": 0})
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        try:
            ai_result = await generate_explanation(topic["title"], db=db)
            explanation = {
                "id": str(uuid.uuid4()),
                "topic_id": topic_id,
                "topic_title": topic["title"],
                "normalized_question": ai_result.get("normalized_question", topic["title"]),
                "card_1": ai_result["card_1"],
                "card_2": ai_result["card_2"],
                "card_3": ai_result["card_3"],
                "card_1_detail": ai_result.get("card_1_detail", ""),
                "card_2_detail": ai_result.get("card_2_detail", ""),
                "card_3_detail": ai_result.get("card_3_detail", ""),
                "card_3_affects": ai_result.get("card_3_affects", []),
                "card_3_action": ai_result.get("card_3_action", []),
                "category": ai_result.get("category", topic.get("category", "world_news")),
                "visual_type": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            doc = {**explanation}
            await db.explanations.insert_one(doc)
            explanation.pop("_id", None)
        except Exception as e:
            logger.error(f"Explanation generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")
    return {"explanation": explanation}


@router.post("/explain")
async def explain_topic(req: ExplainRequest):
    user_input = req.input.strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="Input is required")
    try:
        ai_result = await generate_explanation(user_input, db=db)
        topic_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        category = ai_result.get("category", "world_news")
        topic = {
            "id": topic_id, "title": user_input, "category": category,
            "source": "user_input", "trend_score": 50, "created_at": now,
        }
        await db.topics.insert_one({**topic})
        explanation = {
            "id": str(uuid.uuid4()), "topic_id": topic_id, "topic_title": user_input,
            "normalized_question": ai_result.get("normalized_question", user_input),
            "card_1": ai_result["card_1"], "card_2": ai_result["card_2"], "card_3": ai_result["card_3"],
            "card_1_detail": ai_result.get("card_1_detail", ""),
            "card_2_detail": ai_result.get("card_2_detail", ""),
            "card_3_detail": ai_result.get("card_3_detail", ""),
            "card_3_affects": ai_result.get("card_3_affects", []),
            "card_3_action": ai_result.get("card_3_action", []),
            "category": category, "visual_type": None, "created_at": now,
        }
        await db.explanations.insert_one({**explanation})
        topic.pop("_id", None)
        explanation.pop("_id", None)
        return {"topic": topic, "explanation": explanation}
    except Exception as e:
        logger.error(f"Explain failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending")
async def get_trending(limit: int = 10):
    topics = await db.topics.find({}, {"_id": 0}).sort("trend_score", -1).limit(limit).to_list(limit)
    for t in topics:
        t["time_ago"] = time_ago(t.get("created_at", ""))
    return {"trending": topics}


@router.post("/save/{topic_id}")
async def save_topic(topic_id: str, user=Depends(get_current_user)):
    topic = await db.topics.find_one({"id": topic_id}, {"_id": 0})
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    existing = await db.saved_topics.find_one({"topic_id": topic_id, "user_id": user["id"]})
    if existing:
        await db.saved_topics.delete_one({"topic_id": topic_id, "user_id": user["id"]})
        return {"saved": False, "message": "Topic removed from saved"}
    saved = {
        "id": str(uuid.uuid4()), "user_id": user["id"],
        "topic_id": topic_id, "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.saved_topics.insert_one(saved)
    return {"saved": True, "message": "Topic saved"}


@router.get("/saved")
async def get_saved(user=Depends(get_current_user)):
    saved_items = await db.saved_topics.find({"user_id": user["id"]}, {"_id": 0}).sort("saved_at", -1).to_list(100)
    result = []
    for item in saved_items:
        topic = await db.topics.find_one({"id": item["topic_id"]}, {"_id": 0})
        if topic:
            explanation = await db.explanations.find_one({"topic_id": item["topic_id"]}, {"_id": 0})
            result.append({"topic": topic, "explanation": explanation, "saved_at": item.get("saved_at", "")})
    return {"saved": result}


@router.get("/render-card/{topic_id}")
async def render_card(topic_id: str, template_type: str = "standard"):
    explanation = await db.explanations.find_one({"topic_id": topic_id}, {"_id": 0})
    if not explanation:
        raise HTTPException(status_code=404, detail="Explanation not found")
    topic = await db.topics.find_one({"id": topic_id}, {"_id": 0})
    title = topic["title"] if topic else explanation.get("topic_title", "")
    caption_data = await generate_caption(
        title, explanation["card_1"], explanation["card_2"], explanation["card_3"]
    )
    category = explanation.get("category", "world_news")
    colors = CATEGORY_COLORS.get(category, {"bg": "#F5F5F5", "accent": "#6B7280"})
    templates = {
        "standard": {"width": 1080, "height": 1080, "platform": "Instagram/LinkedIn"},
        "twitter": {"width": 1200, "height": 675, "platform": "X/Twitter"},
        "story": {"width": 1080, "height": 1920, "platform": "Stories/Reels"},
    }
    template = templates.get(template_type, templates["standard"])
    return {
        "card_data": {
            "title": title, "card_1": explanation["card_1"],
            "card_2": explanation["card_2"], "card_3": explanation["card_3"],
            "category": category, "colors": colors, "template": template,
            "template_type": template_type, "caption": caption_data.get("caption", ""),
            "hashtags": caption_data.get("hashtags", []), "brand": "wtfhappened.app",
        }
    }
