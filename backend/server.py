from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Depends, Header, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
import secrets
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest

from services.ai_engine import generate_explanation, generate_caption
from services.data_collector import get_seed_topics, SEED_EXPLANATIONS, collect_all_trending

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Auth config
JWT_SECRET = os.environ.get("JWT_SECRET", uuid.uuid4().hex + uuid.uuid4().hex)
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 72
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Stripe config
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
SUBSCRIPTION_PRICE = 4.99
TRIAL_DAYS = 2

# Admin config
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@wtfhappened.app")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "WTFadmin2026!")

# --- Auth Models ---

class RegisterRequest(BaseModel):
    email: Optional[str] = None
    mobile: Optional[str] = None
    password: str
    name: str

class LoginRequest(BaseModel):
    identifier: str  # email or mobile
    password: str

class OnboardingRequest(BaseModel):
    interests: List[str] = []
    curiosity_types: List[str] = []
    explanation_depth: str = "simple"
    country: str = ""
    region: str = ""
    professional_context: str = ""
    followed_topics: List[str] = []

class ForgotPasswordRequest(BaseModel):
    identifier: str  # email or mobile

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class SubscriptionCheckoutRequest(BaseModel):
    origin_url: str

class AdminLoginRequest(BaseModel):
    email: str
    password: str

class AdminTopicRequest(BaseModel):
    title: str
    category: str
    source: str = "admin"
    trend_score: float = 50

class AdminPromptUpdate(BaseModel):
    prompt_key: str
    prompt_text: str

# --- Auth Helpers ---

def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    user_id = verify_token(token)
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def get_optional_user(authorization: Optional[str] = Header(None)):
    """Returns user if authenticated, None otherwise."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split(" ")[1]
        user_id = verify_token(token)
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
        return user
    except Exception:
        return None

# --- Auth Routes ---

@api_router.post("/auth/register")
async def register(req: RegisterRequest):
    if not req.email and not req.mobile:
        raise HTTPException(status_code=400, detail="Email or mobile is required")

    # Check existing user
    query = []
    if req.email:
        query.append({"email": req.email.lower().strip()})
    if req.mobile:
        query.append({"mobile": req.mobile.strip()})

    existing = await db.users.find_one({"$or": query})
    if existing:
        raise HTTPException(status_code=409, detail="User already exists with this email or mobile")

    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    trial_end = (datetime.now(timezone.utc) + timedelta(days=TRIAL_DAYS)).isoformat()
    user = {
        "id": user_id,
        "name": req.name.strip(),
        "email": req.email.lower().strip() if req.email else None,
        "mobile": req.mobile.strip() if req.mobile else None,
        "password_hash": pwd_context.hash(req.password),
        "onboarding_complete": False,
        "preferences": {},
        "subscription_status": "trial",
        "trial_end": trial_end,
        "auto_renew": True,
        "status": "active",
        "role": "user",
        "created_at": now,
    }
    await db.users.insert_one({**user})

    token = create_token(user_id)
    return {
        "token": token,
        "user": _safe_user(user),
    }

def _safe_user(user: dict) -> dict:
    """Return user dict without sensitive fields."""
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user.get("email"),
        "mobile": user.get("mobile"),
        "onboarding_complete": user.get("onboarding_complete", False),
        "preferences": user.get("preferences", {}),
        "subscription_status": user.get("subscription_status", "trial"),
        "trial_end": user.get("trial_end"),
        "auto_renew": user.get("auto_renew", True),
        "status": user.get("status", "active"),
        "role": user.get("role", "user"),
    }

@api_router.post("/auth/login")
async def login(req: LoginRequest):
    identifier = req.identifier.strip().lower()
    user = await db.users.find_one({
        "$or": [{"email": identifier}, {"mobile": identifier}]
    })
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not pwd_context.verify(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user["id"])
    return {
        "token": token,
        "user": _safe_user(user),
    }

@api_router.get("/auth/me")
async def get_me(user=Depends(get_current_user)):
    return {"user": user}

@api_router.put("/auth/onboarding")
async def save_onboarding(req: OnboardingRequest, user=Depends(get_current_user)):
    preferences = {
        "interests": req.interests,
        "curiosity_types": req.curiosity_types,
        "explanation_depth": req.explanation_depth,
        "country": req.country,
        "region": req.region,
        "professional_context": req.professional_context,
        "followed_topics": req.followed_topics,
    }
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"preferences": preferences, "onboarding_complete": True}}
    )
    return {"message": "Onboarding complete", "preferences": preferences}

# --- Forgot / Reset Password ---

@api_router.post("/auth/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    identifier = req.identifier.strip().lower()
    user = await db.users.find_one({"$or": [{"email": identifier}, {"mobile": identifier}]})
    if not user:
        # Don't reveal whether user exists
        return {"message": "If an account exists, a reset link has been sent."}

    reset_token = secrets.token_urlsafe(32)
    await db.password_resets.insert_one({
        "user_id": user["id"],
        "token": reset_token,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "used": False,
    })
    # In production, this would send an email/SMS with the reset link
    return {"message": "If an account exists, a reset link has been sent.", "reset_token": reset_token}

@api_router.post("/auth/reset-password")
async def reset_password(req: ResetPasswordRequest):
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    reset = await db.password_resets.find_one({"token": req.token, "used": False})
    if not reset:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    expires = datetime.fromisoformat(reset["expires_at"])
    if datetime.now(timezone.utc) > expires:
        raise HTTPException(status_code=400, detail="Reset token has expired")

    await db.users.update_one(
        {"id": reset["user_id"]},
        {"$set": {"password_hash": pwd_context.hash(req.new_password)}}
    )
    await db.password_resets.update_one({"token": req.token}, {"$set": {"used": True}})
    return {"message": "Password reset successfully"}

# --- Profile / Settings ---

@api_router.put("/auth/profile")
async def update_profile(req: UpdateProfileRequest, user=Depends(get_current_user)):
    updates = {}
    if req.name is not None:
        updates["name"] = req.name.strip()
    if req.email is not None:
        email = req.email.lower().strip()
        existing = await db.users.find_one({"email": email, "id": {"$ne": user["id"]}})
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use")
        updates["email"] = email
    if req.mobile is not None:
        mobile = req.mobile.strip()
        existing = await db.users.find_one({"mobile": mobile, "id": {"$ne": user["id"]}})
        if existing:
            raise HTTPException(status_code=409, detail="Mobile already in use")
        updates["mobile"] = mobile

    if updates:
        await db.users.update_one({"id": user["id"]}, {"$set": updates})

    updated = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 0})
    return {"user": _safe_user(updated)}

@api_router.put("/auth/change-password")
async def change_password(req: ChangePasswordRequest, user=Depends(get_current_user)):
    full_user = await db.users.find_one({"id": user["id"]})
    if not pwd_context.verify(req.current_password, full_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"password_hash": pwd_context.hash(req.new_password)}}
    )
    return {"message": "Password changed successfully"}

@api_router.post("/auth/suspend")
async def suspend_account(user=Depends(get_current_user)):
    await db.users.update_one({"id": user["id"]}, {"$set": {"status": "suspended"}})
    return {"message": "Account suspended"}

@api_router.delete("/auth/delete")
async def delete_account(user=Depends(get_current_user)):
    await db.users.delete_one({"id": user["id"]})
    await db.saved_topics.delete_many({"user_id": user["id"]})
    await db.payment_transactions.delete_many({"user_id": user["id"]})
    return {"message": "Account deleted"}

@api_router.put("/auth/auto-renew")
async def toggle_auto_renew(user=Depends(get_current_user)):
    current = user.get("auto_renew", True)
    await db.users.update_one({"id": user["id"]}, {"$set": {"auto_renew": not current}})
    return {"auto_renew": not current}

# --- Subscription / Stripe ---

@api_router.get("/subscription/info")
async def get_subscription_info(user=Depends(get_current_user)):
    full_user = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 0})
    trial_end = full_user.get("trial_end", "")
    sub_status = full_user.get("subscription_status", "trial")

    # Check if trial has expired
    if sub_status == "trial" and trial_end:
        try:
            end_dt = datetime.fromisoformat(trial_end)
            if datetime.now(timezone.utc) > end_dt:
                sub_status = "expired"
                await db.users.update_one({"id": user["id"]}, {"$set": {"subscription_status": "expired"}})
        except Exception:
            pass

    last_payment = await db.payment_transactions.find_one(
        {"user_id": user["id"], "payment_status": "paid"},
        {"_id": 0},
        sort=[("created_at", -1)]
    )

    return {
        "subscription_status": sub_status,
        "trial_end": trial_end,
        "auto_renew": full_user.get("auto_renew", True),
        "last_payment": last_payment,
    }

@api_router.post("/subscription/checkout")
async def create_subscription_checkout(req: SubscriptionCheckoutRequest, user=Depends(get_current_user)):
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Payment system not configured")

    host_url = req.origin_url.rstrip("/")
    success_url = f"{host_url}?session_id={{CHECKOUT_SESSION_ID}}&payment=success"
    cancel_url = f"{host_url}?payment=cancelled"
    webhook_url = f"{host_url}/api/webhook/stripe"

    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)

    checkout_req = CheckoutSessionRequest(
        amount=SUBSCRIPTION_PRICE,
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": user["id"], "type": "subscription"}
    )
    session = await stripe_checkout.create_checkout_session(checkout_req)

    # Record transaction
    await db.payment_transactions.insert_one({
        "id": str(uuid.uuid4()),
        "session_id": session.session_id,
        "user_id": user["id"],
        "amount": SUBSCRIPTION_PRICE,
        "currency": "usd",
        "payment_status": "pending",
        "metadata": {"type": "subscription"},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    return {"url": session.url, "session_id": session.session_id}

@api_router.get("/subscription/status/{session_id}")
async def check_subscription_status(session_id: str, user=Depends(get_current_user)):
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Payment system not configured")

    # Check if already processed
    txn = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if txn and txn.get("payment_status") == "paid":
        return {"status": "complete", "payment_status": "paid", "already_processed": True}

    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")
    status = await stripe_checkout.get_checkout_status(session_id)

    # Update transaction
    new_status = status.payment_status
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {"payment_status": new_status, "status": status.status}}
    )

    # If paid, activate subscription
    if new_status == "paid":
        sub_end = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"subscription_status": "active", "subscription_end": sub_end}}
        )

    return {
        "status": status.status,
        "payment_status": new_status,
        "amount_total": status.amount_total,
        "currency": status.currency,
    }

# --- Stripe Webhook ---

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    try:
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")
        event = await stripe_checkout.handle_webhook(body, sig)
        if event.payment_status == "paid":
            txn = await db.payment_transactions.find_one({"session_id": event.session_id})
            if txn and txn.get("payment_status") != "paid":
                await db.payment_transactions.update_one(
                    {"session_id": event.session_id},
                    {"$set": {"payment_status": "paid"}}
                )
                user_id = event.metadata.get("user_id") or txn.get("user_id")
                if user_id:
                    sub_end = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
                    await db.users.update_one(
                        {"id": user_id},
                        {"$set": {"subscription_status": "active", "subscription_end": sub_end}}
                    )
        return {"received": True}
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return {"received": True}

# --- Admin ---

def create_admin_token(admin_id: str) -> str:
    payload = {
        "sub": admin_id,
        "role": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_admin_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@api_router.post("/admin/login")
async def admin_login(req: AdminLoginRequest):
    if req.email != ADMIN_EMAIL or req.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    token = create_admin_token("admin")
    return {"token": token, "role": "admin"}

@api_router.get("/admin/users")
async def admin_list_users(admin=Depends(get_admin_user)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(500)
    return {"users": users}

@api_router.put("/admin/users/{user_id}/status")
async def admin_update_user_status(user_id: str, status: str, admin=Depends(get_admin_user)):
    if status not in ("active", "suspended", "banned"):
        raise HTTPException(status_code=400, detail="Invalid status")
    result = await db.users.update_one({"id": user_id}, {"$set": {"status": status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User status updated to {status}"}

@api_router.get("/admin/prompts")
async def admin_get_prompts(admin=Depends(get_admin_user)):
    prompts = await db.ai_prompts.find({}, {"_id": 0}).to_list(50)
    if not prompts:
        # Seed default prompts from ai_engine
        from services.ai_engine import SYSTEM_PROMPT, EXPLANATION_PROMPT, CAPTION_PROMPT
        defaults = [
            {"id": str(uuid.uuid4()), "prompt_key": "system_prompt", "label": "System Prompt", "prompt_text": SYSTEM_PROMPT},
            {"id": str(uuid.uuid4()), "prompt_key": "explanation_prompt", "label": "Explanation Prompt", "prompt_text": EXPLANATION_PROMPT},
            {"id": str(uuid.uuid4()), "prompt_key": "caption_prompt", "label": "Caption Prompt", "prompt_text": CAPTION_PROMPT},
        ]
        for p in defaults:
            await db.ai_prompts.insert_one({**p})
        prompts = defaults
    # Clean _id
    for p in prompts:
        p.pop("_id", None)
    return {"prompts": prompts}

@api_router.put("/admin/prompts/{prompt_id}")
async def admin_update_prompt(prompt_id: str, req: AdminPromptUpdate, admin=Depends(get_admin_user)):
    result = await db.ai_prompts.update_one(
        {"id": prompt_id},
        {"$set": {"prompt_text": req.prompt_text}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"message": "Prompt updated"}

@api_router.get("/admin/topics")
async def admin_list_topics(admin=Depends(get_admin_user)):
    topics = await db.topics.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return {"topics": topics}

@api_router.post("/admin/topics")
async def admin_create_topic(req: AdminTopicRequest, admin=Depends(get_admin_user)):
    topic = {
        "id": str(uuid.uuid4()),
        "title": req.title,
        "category": req.category,
        "source": req.source,
        "trend_score": req.trend_score,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.topics.insert_one({**topic})
    topic.pop("_id", None)
    return {"topic": topic}

@api_router.put("/admin/topics/{topic_id}")
async def admin_update_topic(topic_id: str, req: AdminTopicRequest, admin=Depends(get_admin_user)):
    result = await db.topics.update_one(
        {"id": topic_id},
        {"$set": {"title": req.title, "category": req.category, "trend_score": req.trend_score}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Topic not found")
    return {"message": "Topic updated"}

@api_router.delete("/admin/topics/{topic_id}")
async def admin_delete_topic(topic_id: str, admin=Depends(get_admin_user)):
    await db.topics.delete_one({"id": topic_id})
    await db.explanations.delete_many({"topic_id": topic_id})
    return {"message": "Topic deleted"}

@api_router.get("/admin/stats")
async def admin_stats(admin=Depends(get_admin_user)):
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"status": "active"})
    trial_users = await db.users.count_documents({"subscription_status": "trial"})
    paid_users = await db.users.count_documents({"subscription_status": "active"})
    total_topics = await db.topics.count_documents({})
    total_explanations = await db.explanations.count_documents({})
    return {
        "total_users": total_users,
        "active_users": active_users,
        "trial_users": trial_users,
        "paid_users": paid_users,
        "total_topics": total_topics,
        "total_explanations": total_explanations,
    }

# --- Content Models ---

class TopicOut(BaseModel):
    id: str
    title: str
    category: str
    source: str
    trend_score: float
    created_at: str
    has_explanation: bool = False

class ExplanationOut(BaseModel):
    id: str
    topic_id: str
    topic_title: str
    normalized_question: str
    card_1: str
    card_2: str
    card_3: str
    card_1_detail: str
    card_2_detail: str
    card_3_detail: str
    category: str
    visual_type: Optional[str] = None
    created_at: str

class ExplainRequest(BaseModel):
    input: str

class SaveRequest(BaseModel):
    topic_id: str

class RenderCardRequest(BaseModel):
    topic_id: str
    template_type: str = "standard"

# --- Helpers ---

def time_ago(dt_str: str) -> str:
    try:
        dt = datetime.fromisoformat(dt_str)
        now = datetime.now(timezone.utc)
        diff = now - dt
        hours = int(diff.total_seconds() / 3600)
        if hours < 1:
            mins = int(diff.total_seconds() / 60)
            return f"{max(1, mins)}m ago"
        if hours < 24:
            return f"{hours}h ago"
        days = int(hours / 24)
        return f"{days}d ago"
    except Exception:
        return "recently"

# --- Routes ---

@api_router.get("/")
async def root():
    return {"message": "WTFHappened API", "status": "running"}

@api_router.get("/health")
async def health():
    try:
        await db.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception:
        return {"status": "degraded", "database": "disconnected"}

@api_router.get("/feed")
async def get_feed(limit: int = 20, category: Optional[str] = None):
    """Get trending topics feed, sorted by trend score."""
    query = {}
    if category and category != "all":
        query["category"] = category

    topics = await db.topics.find(query, {"_id": 0}).sort("trend_score", -1).limit(limit).to_list(limit)

    # Check which have explanations
    for t in topics:
        exp = await db.explanations.find_one({"topic_id": t["id"]}, {"_id": 0, "id": 1})
        t["has_explanation"] = exp is not None
        t["time_ago"] = time_ago(t.get("created_at", ""))

    return {"topics": topics}

@api_router.get("/explanation/{topic_id}")
async def get_explanation(topic_id: str):
    """Get explanation cards for a topic."""
    explanation = await db.explanations.find_one({"topic_id": topic_id}, {"_id": 0})
    if not explanation:
        # Try to generate one
        topic = await db.topics.find_one({"id": topic_id}, {"_id": 0})
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        try:
            ai_result = await generate_explanation(topic["title"])
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
                "category": ai_result.get("category", topic.get("category", "world_news")),
                "visual_type": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            doc_to_insert = {**explanation}
            await db.explanations.insert_one(doc_to_insert)
            explanation.pop("_id", None)
        except Exception as e:
            logging.error(f"Explanation generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")

    return {"explanation": explanation}

@api_router.post("/explain")
async def explain_topic(req: ExplainRequest):
    """Generate explanation from user input (headline/question)."""
    user_input = req.input.strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="Input is required")

    try:
        ai_result = await generate_explanation(user_input)

        # Create topic
        topic_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        category = ai_result.get("category", "world_news")

        topic = {
            "id": topic_id,
            "title": user_input,
            "category": category,
            "source": "user_input",
            "trend_score": 50,
            "created_at": now,
        }
        await db.topics.insert_one({**topic})

        explanation = {
            "id": str(uuid.uuid4()),
            "topic_id": topic_id,
            "topic_title": user_input,
            "normalized_question": ai_result.get("normalized_question", user_input),
            "card_1": ai_result["card_1"],
            "card_2": ai_result["card_2"],
            "card_3": ai_result["card_3"],
            "card_1_detail": ai_result.get("card_1_detail", ""),
            "card_2_detail": ai_result.get("card_2_detail", ""),
            "card_3_detail": ai_result.get("card_3_detail", ""),
            "category": category,
            "visual_type": None,
            "created_at": now,
        }
        await db.explanations.insert_one({**explanation})

        # Remove _id from response
        topic.pop("_id", None)
        explanation.pop("_id", None)

        return {"topic": topic, "explanation": explanation}

    except Exception as e:
        logging.error(f"Explain failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/trending")
async def get_trending(limit: int = 10):
    """Get trending confusion index - topics people are searching/asking about."""
    topics = await db.topics.find({}, {"_id": 0}).sort("trend_score", -1).limit(limit).to_list(limit)
    for t in topics:
        t["time_ago"] = time_ago(t.get("created_at", ""))
    return {"trending": topics}

@api_router.post("/save/{topic_id}")
async def save_topic(topic_id: str, user=Depends(get_current_user)):
    """Save/bookmark a topic for the authenticated user."""
    topic = await db.topics.find_one({"id": topic_id}, {"_id": 0})
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    existing = await db.saved_topics.find_one({"topic_id": topic_id, "user_id": user["id"]})
    if existing:
        await db.saved_topics.delete_one({"topic_id": topic_id, "user_id": user["id"]})
        return {"saved": False, "message": "Topic removed from saved"}

    saved = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "topic_id": topic_id,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.saved_topics.insert_one(saved)
    return {"saved": True, "message": "Topic saved"}

@api_router.get("/saved")
async def get_saved(user=Depends(get_current_user)):
    """Get saved topics for the authenticated user."""
    saved_items = await db.saved_topics.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort("saved_at", -1).to_list(100)
    result = []
    for item in saved_items:
        topic = await db.topics.find_one({"id": item["topic_id"]}, {"_id": 0})
        if topic:
            explanation = await db.explanations.find_one({"topic_id": item["topic_id"]}, {"_id": 0})
            result.append({
                "topic": topic,
                "explanation": explanation,
                "saved_at": item.get("saved_at", ""),
            })
    return {"saved": result}

@api_router.get("/render-card/{topic_id}")
async def render_card(topic_id: str, template_type: str = "standard"):
    """Get social card data for a topic."""
    explanation = await db.explanations.find_one({"topic_id": topic_id}, {"_id": 0})
    if not explanation:
        raise HTTPException(status_code=404, detail="Explanation not found")

    topic = await db.topics.find_one({"id": topic_id}, {"_id": 0})
    title = topic["title"] if topic else explanation.get("topic_title", "")

    # Generate caption
    caption_data = await generate_caption(
        title, explanation["card_1"], explanation["card_2"], explanation["card_3"]
    )

    # Category colors
    category_colors = {
        "technology": {"bg": "#EBF5FF", "accent": "#3B82F6"},
        "finance": {"bg": "#F0FDF4", "accent": "#22C55E"},
        "economy": {"bg": "#FFFBEB", "accent": "#F59E0B"},
        "ai": {"bg": "#F3E8FF", "accent": "#8B5CF6"},
        "crypto": {"bg": "#FFF7ED", "accent": "#F97316"},
        "science": {"bg": "#EDE9FE", "accent": "#7C3AED"},
        "world_news": {"bg": "#FEF2F2", "accent": "#EF4444"},
        "internet_culture": {"bg": "#FFF1F2", "accent": "#F43F5E"},
        "politics": {"bg": "#FEF2F2", "accent": "#DC2626"},
    }

    category = explanation.get("category", "world_news")
    colors = category_colors.get(category, {"bg": "#F5F5F5", "accent": "#6B7280"})

    # Template sizes
    templates = {
        "standard": {"width": 1080, "height": 1080, "platform": "Instagram/LinkedIn"},
        "twitter": {"width": 1200, "height": 675, "platform": "X/Twitter"},
        "story": {"width": 1080, "height": 1920, "platform": "Stories/Reels"},
    }
    template = templates.get(template_type, templates["standard"])

    return {
        "card_data": {
            "title": title,
            "card_1": explanation["card_1"],
            "card_2": explanation["card_2"],
            "card_3": explanation["card_3"],
            "category": category,
            "colors": colors,
            "template": template,
            "template_type": template_type,
            "caption": caption_data.get("caption", ""),
            "hashtags": caption_data.get("hashtags", []),
            "brand": "wtfhappened.app",
        }
    }

@api_router.post("/refresh-trending")
async def refresh_trending(background_tasks: BackgroundTasks):
    """Trigger a refresh of trending data from external sources."""
    background_tasks.add_task(ingest_trending_data)
    return {"message": "Refresh started"}

# --- Data Seeding ---

async def seed_initial_data():
    """Seed the database with initial topics and explanations."""
    count = await db.topics.count_documents({})
    if count > 0:
        return

    logging.info("Seeding initial data...")
    seed_topics = get_seed_topics()
    now = datetime.now(timezone.utc).isoformat()

    for topic_data in seed_topics:
        topic_id = str(uuid.uuid4())
        topic = {
            "id": topic_id,
            "title": topic_data["title"],
            "category": topic_data["category"],
            "source": topic_data["source"],
            "trend_score": topic_data["trend_score"],
            "created_at": now,
        }
        await db.topics.insert_one(topic)

        # Add seed explanation if available
        if topic_data["title"] in SEED_EXPLANATIONS:
            exp_data = SEED_EXPLANATIONS[topic_data["title"]]
            explanation = {
                "id": str(uuid.uuid4()),
                "topic_id": topic_id,
                "topic_title": topic_data["title"],
                "normalized_question": f"Why: {topic_data['title']}?",
                "card_1": exp_data["card_1"],
                "card_2": exp_data["card_2"],
                "card_3": exp_data["card_3"],
                "card_1_detail": exp_data.get("card_1_detail", ""),
                "card_2_detail": exp_data.get("card_2_detail", ""),
                "card_3_detail": exp_data.get("card_3_detail", ""),
                "category": exp_data.get("category", topic_data["category"]),
                "visual_type": None,
                "created_at": now,
            }
            await db.explanations.insert_one(explanation)

    logging.info(f"Seeded {len(seed_topics)} topics")


async def ingest_trending_data():
    """Fetch and store trending topics from external sources."""
    try:
        new_topics = await collect_all_trending()
        now = datetime.now(timezone.utc).isoformat()
        added = 0
        for topic_data in new_topics:
            # Check for duplicate titles
            existing = await db.topics.find_one({"title": topic_data["title"]})
            if existing:
                continue
            topic = {
                "id": str(uuid.uuid4()),
                "title": topic_data["title"],
                "category": topic_data["category"],
                "source": topic_data["source"],
                "trend_score": topic_data["trend_score"],
                "created_at": now,
            }
            await db.topics.insert_one(topic)
            added += 1
        logging.info(f"Ingested {added} new trending topics")
    except Exception as e:
        logging.error(f"Trending data ingestion failed: {e}")


# --- App Events ---

@app.on_event("startup")
async def startup():
    # Create indexes
    await db.topics.create_index("id", unique=True)
    await db.topics.create_index("trend_score")
    await db.topics.create_index("category")
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
    # Seed data
    await seed_initial_data()
    logging.info("WTFHappened API started")

@app.on_event("shutdown")
async def shutdown():
    client.close()

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
