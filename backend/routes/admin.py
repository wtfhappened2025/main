import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request

from database import db
from config import settings
from models import AdminLoginRequest, AdminTopicRequest, AdminPromptUpdate
from utils.security import create_token, get_admin_user
from emergentintegrations.payments.stripe.checkout import StripeCheckout
from services.data_collector import collect_all_trending

router = APIRouter(prefix="/api", tags=["admin"])
logger = logging.getLogger(__name__)


@router.post("/admin/login")
async def admin_login(req: AdminLoginRequest):
    if req.email != settings.ADMIN_EMAIL or req.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    token = create_token("admin", role="admin", expiry_hours=24)
    return {"token": token, "role": "admin"}


@router.get("/admin/users")
async def admin_list_users(admin=Depends(get_admin_user)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(500)
    return {"users": users}


@router.put("/admin/users/{user_id}/status")
async def admin_update_user_status(user_id: str, status: str, admin=Depends(get_admin_user)):
    if status not in ("active", "suspended", "banned"):
        raise HTTPException(status_code=400, detail="Invalid status")
    result = await db.users.update_one({"id": user_id}, {"$set": {"status": status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User status updated to {status}"}


@router.get("/admin/prompts")
async def admin_get_prompts(admin=Depends(get_admin_user)):
    prompts = await db.ai_prompts.find({}, {"_id": 0}).to_list(50)
    if not prompts:
        from services.ai_engine import DEFAULT_PROMPTS
        for p in DEFAULT_PROMPTS:
            doc = {
                "id": str(uuid.uuid4()), "prompt_key": p["prompt_key"],
                "label": p["label"], "description": p["description"],
                "system_prompt": p["system_prompt"], "task_prompt": p["task_prompt"],
            }
            await db.ai_prompts.insert_one({**doc})
        prompts = await db.ai_prompts.find({}, {"_id": 0}).to_list(50)
    for p in prompts:
        p.pop("_id", None)
    return {"prompts": prompts}


@router.put("/admin/prompts/{prompt_id}")
async def admin_update_prompt(prompt_id: str, req: AdminPromptUpdate, admin=Depends(get_admin_user)):
    updates = {}
    if req.system_prompt:
        updates["system_prompt"] = req.system_prompt
    if req.task_prompt:
        updates["task_prompt"] = req.task_prompt
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")
    result = await db.ai_prompts.update_one({"id": prompt_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"message": "Prompt updated"}


@router.get("/admin/topics")
async def admin_list_topics(admin=Depends(get_admin_user)):
    topics = await db.topics.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return {"topics": topics}


@router.post("/admin/topics")
async def admin_create_topic(req: AdminTopicRequest, admin=Depends(get_admin_user)):
    topic = {
        "id": str(uuid.uuid4()), "title": req.title, "category": req.category,
        "source": req.source, "trend_score": req.trend_score,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.topics.insert_one({**topic})
    topic.pop("_id", None)
    return {"topic": topic}


@router.put("/admin/topics/{topic_id}")
async def admin_update_topic(topic_id: str, req: AdminTopicRequest, admin=Depends(get_admin_user)):
    result = await db.topics.update_one(
        {"id": topic_id},
        {"$set": {"title": req.title, "category": req.category, "trend_score": req.trend_score}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Topic not found")
    return {"message": "Topic updated"}


@router.delete("/admin/topics/{topic_id}")
async def admin_delete_topic(topic_id: str, admin=Depends(get_admin_user)):
    await db.topics.delete_one({"id": topic_id})
    await db.explanations.delete_many({"topic_id": topic_id})
    return {"message": "Topic deleted"}


@router.get("/admin/stats")
async def admin_stats(admin=Depends(get_admin_user)):
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"status": "active"})
    trial_users = await db.users.count_documents({"subscription_status": "trial"})
    paid_users = await db.users.count_documents({"subscription_status": "active"})
    total_topics = await db.topics.count_documents({})
    total_explanations = await db.explanations.count_documents({})
    return {
        "total_users": total_users, "active_users": active_users,
        "trial_users": trial_users, "paid_users": paid_users,
        "total_topics": total_topics, "total_explanations": total_explanations,
    }


@router.get("/admin/published")
async def admin_published_cards(admin=Depends(get_admin_user)):
    cards = await db.published_cards.find({}, {"_id": 0}).sort("published_at", -1).limit(50).to_list(50)
    return {"published": cards}


@router.get("/admin/audit-log")
async def admin_audit_log(limit: int = 100, event: str = None, admin=Depends(get_admin_user)):
    """View security audit log."""
    query = {}
    if event:
        query["event"] = event
    entries = await db.audit_log.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    return {"audit_log": entries, "count": len(entries)}


@router.get("/admin/api-usage")
async def admin_api_usage(limit: int = 100, usage_type: str = None, admin=Depends(get_admin_user)):
    """View API usage tracking — monitors AI/expensive endpoint calls."""
    query = {}
    if usage_type:
        query["type"] = usage_type
    entries = await db.api_usage.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    # Aggregate stats
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    last_hour = (now - timedelta(hours=1)).isoformat()
    last_day = (now - timedelta(days=1)).isoformat()
    hourly_count = await db.api_usage.count_documents({"timestamp": {"$gte": last_hour}})
    daily_count = await db.api_usage.count_documents({"timestamp": {"$gte": last_day}})
    ai_daily = await db.api_usage.count_documents({"timestamp": {"$gte": last_day}, "type": {"$in": ["ai_explanation", "ai_explain"]}})
    return {
        "usage": entries,
        "stats": {"hourly_total": hourly_count, "daily_total": daily_count, "daily_ai_calls": ai_daily},
    }


@router.post("/admin/publish-now")
async def admin_publish_now(background_tasks: BackgroundTasks, admin=Depends(get_admin_user)):
    from services.publisher import auto_publish_job
    background_tasks.add_task(auto_publish_job)
    return {"message": "Auto-publish triggered"}


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    try:
        from datetime import timedelta
        stripe_checkout = StripeCheckout(api_key=settings.STRIPE_API_KEY, webhook_url="")
        event = await stripe_checkout.handle_webhook(body, sig)
        if event.payment_status == "paid":
            txn = await db.payment_transactions.find_one({"session_id": event.session_id})
            if txn and txn.get("payment_status") != "paid":
                await db.payment_transactions.update_one(
                    {"session_id": event.session_id}, {"$set": {"payment_status": "paid"}}
                )
                user_id = event.metadata.get("user_id") or txn.get("user_id")
                if user_id:
                    from datetime import timedelta
                    sub_end = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
                    await db.users.update_one(
                        {"id": user_id},
                        {"$set": {"subscription_status": "active", "subscription_end": sub_end}}
                    )
        return {"received": True}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"received": True}
