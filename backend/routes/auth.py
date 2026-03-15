import uuid
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException

from database import db
from config import settings
from models import (
    RegisterRequest, LoginRequest, OnboardingRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
    UpdateProfileRequest, ChangePasswordRequest,
)
from utils.security import (
    hash_password, verify_password, create_token, get_current_user,
)
from utils.helpers import safe_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
async def register(req: RegisterRequest):
    if not req.email and not req.mobile:
        raise HTTPException(status_code=400, detail="Email or mobile is required")

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
    trial_end = (datetime.now(timezone.utc) + timedelta(days=settings.TRIAL_DAYS)).isoformat()
    user = {
        "id": user_id,
        "name": req.name.strip(),
        "email": req.email.lower().strip() if req.email else None,
        "mobile": req.mobile.strip() if req.mobile else None,
        "password_hash": hash_password(req.password),
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
    return {"token": token, "user": safe_user(user)}


@router.post("/login")
async def login(req: LoginRequest):
    identifier = req.identifier.strip().lower()
    user = await db.users.find_one({"$or": [{"email": identifier}, {"mobile": identifier}]})
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user["id"])
    return {"token": token, "user": safe_user(user)}


@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    return {"user": user}


@router.put("/onboarding")
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


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    identifier = req.identifier.strip().lower()
    user = await db.users.find_one({"$or": [{"email": identifier}, {"mobile": identifier}]})
    if not user:
        return {"message": "If an account exists, a reset link has been sent."}
    reset_token = secrets.token_urlsafe(32)
    await db.password_resets.insert_one({
        "user_id": user["id"],
        "token": reset_token,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "used": False,
    })
    return {"message": "If an account exists, a reset link has been sent.", "reset_token": reset_token}


@router.post("/reset-password")
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
        {"$set": {"password_hash": hash_password(req.new_password)}}
    )
    await db.password_resets.update_one({"token": req.token}, {"$set": {"used": True}})
    return {"message": "Password reset successfully"}


@router.put("/profile")
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
    return {"user": safe_user(updated)}


@router.put("/change-password")
async def change_password(req: ChangePasswordRequest, user=Depends(get_current_user)):
    full_user = await db.users.find_one({"id": user["id"]})
    if not verify_password(req.current_password, full_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"password_hash": hash_password(req.new_password)}}
    )
    return {"message": "Password changed successfully"}


@router.post("/suspend")
async def suspend_account(user=Depends(get_current_user)):
    await db.users.update_one({"id": user["id"]}, {"$set": {"status": "suspended"}})
    return {"message": "Account suspended"}


@router.delete("/delete")
async def delete_account(user=Depends(get_current_user)):
    await db.users.delete_one({"id": user["id"]})
    await db.saved_topics.delete_many({"user_id": user["id"]})
    await db.payment_transactions.delete_many({"user_id": user["id"]})
    return {"message": "Account deleted"}


@router.put("/auto-renew")
async def toggle_auto_renew(user=Depends(get_current_user)):
    current = user.get("auto_renew", True)
    await db.users.update_one({"id": user["id"]}, {"$set": {"auto_renew": not current}})
    return {"auto_renew": not current}
