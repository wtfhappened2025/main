import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request

from database import db
from config import settings
from models import SubscriptionCheckoutRequest
from utils.security import get_current_user
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest
import logging

router = APIRouter(prefix="/api/subscription", tags=["subscription"])
logger = logging.getLogger(__name__)


@router.get("/info")
async def get_subscription_info(user=Depends(get_current_user)):
    full_user = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 0})
    trial_end = full_user.get("trial_end", "")
    sub_status = full_user.get("subscription_status", "trial")
    if sub_status == "trial" and trial_end:
        try:
            end_dt = datetime.fromisoformat(trial_end)
            if datetime.now(timezone.utc) > end_dt:
                sub_status = "expired"
                await db.users.update_one({"id": user["id"]}, {"$set": {"subscription_status": "expired"}})
        except Exception:
            pass
    last_payment = await db.payment_transactions.find_one(
        {"user_id": user["id"], "payment_status": "paid"}, {"_id": 0}, sort=[("created_at", -1)]
    )
    return {
        "subscription_status": sub_status, "trial_end": trial_end,
        "auto_renew": full_user.get("auto_renew", True), "last_payment": last_payment,
    }


@router.post("/checkout")
async def create_subscription_checkout(req: SubscriptionCheckoutRequest, user=Depends(get_current_user)):
    if not settings.STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    host_url = req.origin_url.rstrip("/")
    success_url = f"{host_url}?session_id={{CHECKOUT_SESSION_ID}}&payment=success"
    cancel_url = f"{host_url}?payment=cancelled"
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=settings.STRIPE_API_KEY, webhook_url=webhook_url)
    checkout_req = CheckoutSessionRequest(
        amount=settings.SUBSCRIPTION_PRICE, currency="usd",
        success_url=success_url, cancel_url=cancel_url,
        metadata={"user_id": user["id"], "type": "subscription"}
    )
    session = await stripe_checkout.create_checkout_session(checkout_req)
    await db.payment_transactions.insert_one({
        "id": str(uuid.uuid4()), "session_id": session.session_id,
        "user_id": user["id"], "amount": settings.SUBSCRIPTION_PRICE,
        "currency": "usd", "payment_status": "pending",
        "metadata": {"type": "subscription"},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"url": session.url, "session_id": session.session_id}


@router.get("/status/{session_id}")
async def check_subscription_status(session_id: str, user=Depends(get_current_user)):
    if not settings.STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    txn = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if txn and txn.get("payment_status") == "paid":
        return {"status": "complete", "payment_status": "paid", "already_processed": True}
    stripe_checkout = StripeCheckout(api_key=settings.STRIPE_API_KEY, webhook_url="")
    status = await stripe_checkout.get_checkout_status(session_id)
    new_status = status.payment_status
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {"payment_status": new_status, "status": status.status}}
    )
    if new_status == "paid":
        sub_end = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"subscription_status": "active", "subscription_end": sub_end}}
        )
    return {"status": status.status, "payment_status": new_status,
            "amount_total": status.amount_total, "currency": status.currency}
