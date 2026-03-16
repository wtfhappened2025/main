import uuid
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request

from database import db
from config import settings
from models import (
    RegisterRequest, LoginRequest, OnboardingRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
    UpdateProfileRequest, ChangePasswordRequest,
)
from utils.security import (
    hash_password, verify_password, create_token, create_refresh_token,
    get_current_user, audit_log,
)
from utils.helpers import safe_user
from services.email_service import send_password_reset_email

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
async def register(req: RegisterRequest, request: Request):
    if not req.email and not req.mobile:
        raise HTTPException(status_code=400, detail="Email or mobile is required")

    query = []
    if req.email:
        query.append({"email": req.email.lower().strip()})
    if req.mobile:
        query.append({"mobile": req.mobile.strip()})

    existing = await db.users.find_one({"$or": query})
    if existing:
        await audit_log("register_duplicate", {"identifier": req.email or req.mobile}, ip=request.client.host)
        raise HTTPException(status_code=409, detail="User already exists with this email or mobile")

    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    trial_end = (datetime.now(timezone.utc) + timedelta(days=settings.TRIAL_DAYS)).isoformat()
    refresh = create_refresh_token()
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
        "refresh_token": refresh,
        "created_at": now,
    }
    await db.users.insert_one({**user})
    token = create_token(user_id)
    await audit_log("register_success", {"email": req.email}, user_id=user_id, ip=request.client.host)
    return {"token": token, "refresh_token": refresh, "user": safe_user(user)}


@router.post("/login")
async def login(req: LoginRequest, request: Request):
    identifier = req.identifier.strip().lower()
    user = await db.users.find_one({"$or": [{"email": identifier}, {"mobile": identifier}]})
    if not user or not verify_password(req.password, user["password_hash"]):
        await audit_log("login_failed", {"identifier": identifier}, ip=request.client.host)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.get("status") == "suspended":
        await audit_log("login_suspended", {"identifier": identifier}, user_id=user["id"], ip=request.client.host)
        raise HTTPException(status_code=403, detail="Account suspended")
    if user.get("status") == "banned":
        await audit_log("login_banned", {"identifier": identifier}, user_id=user["id"], ip=request.client.host)
        raise HTTPException(status_code=403, detail="Account banned")
    # Issue new refresh token
    refresh = create_refresh_token()
    await db.users.update_one({"id": user["id"]}, {"$set": {"refresh_token": refresh}})
    token = create_token(user["id"])
    await audit_log("login_success", {"identifier": identifier}, user_id=user["id"], ip=request.client.host)
    return {"token": token, "refresh_token": refresh, "user": safe_user(user)}


@router.post("/refresh")
async def refresh_token(request: Request):
    """Exchange a valid refresh token for a new access token."""
    body = await request.json()
    refresh = body.get("refresh_token", "")
    if not refresh:
        raise HTTPException(status_code=400, detail="refresh_token is required")
    user = await db.users.find_one({"refresh_token": refresh}, {"_id": 0})
    if not user:
        await audit_log("refresh_invalid", {"token_prefix": refresh[:8]}, ip=request.client.host)
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    # Rotate refresh token
    new_refresh = create_refresh_token()
    await db.users.update_one({"id": user["id"]}, {"$set": {"refresh_token": new_refresh}})
    token = create_token(user["id"])
    await audit_log("refresh_success", {}, user_id=user["id"], ip=request.client.host)
    return {"token": token, "refresh_token": new_refresh}


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
async def forgot_password(req: ForgotPasswordRequest, request: Request):
    identifier = req.identifier.strip().lower()
    user = await db.users.find_one({"$or": [{"email": identifier}, {"mobile": identifier}]})
    if not user:
        await audit_log("password_reset_unknown", {"identifier": identifier}, ip=request.client.host)
        return {"message": "If an account exists, a reset link has been sent.", "email_sent": False}
    reset_token = secrets.token_urlsafe(32)
    await db.password_resets.insert_one({
        "user_id": user["id"],
        "token": reset_token,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "used": False,
    })
    await audit_log("password_reset_requested", {"identifier": identifier}, user_id=user["id"], ip=request.client.host)
    # Send email if user has an email address
    email_result = {"status": "skipped", "reason": "No email on account"}
    if user.get("email"):
        email_result = await send_password_reset_email(user["email"], reset_token)
    return {"message": "If an account exists, a reset link has been sent.", "email_sent": email_result.get("status") == "sent"}


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, request: Request):
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    reset = await db.password_resets.find_one({"token": req.token, "used": False})
    if not reset:
        await audit_log("password_reset_invalid_token", {}, ip=request.client.host)
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    expires = datetime.fromisoformat(reset["expires_at"])
    if datetime.now(timezone.utc) > expires:
        await audit_log("password_reset_expired", {}, user_id=reset["user_id"], ip=request.client.host)
        raise HTTPException(status_code=400, detail="Reset token has expired")
    await db.users.update_one(
        {"id": reset["user_id"]},
        {"$set": {"password_hash": hash_password(req.new_password)}}
    )
    await db.password_resets.update_one({"token": req.token}, {"$set": {"used": True}})
    await audit_log("password_reset_success", {}, user_id=reset["user_id"], ip=request.client.host)
    return {"message": "Password reset successfully"}


@router.put("/profile")
async def update_profile(req: UpdateProfileRequest, request: Request, user=Depends(get_current_user)):
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
        await audit_log("profile_updated", {"fields": list(updates.keys())}, user_id=user["id"], ip=request.client.host)
    updated = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 0})
    return {"user": safe_user(updated)}


@router.put("/change-password")
async def change_password(req: ChangePasswordRequest, request: Request, user=Depends(get_current_user)):
    full_user = await db.users.find_one({"id": user["id"]})
    if not verify_password(req.current_password, full_user["password_hash"]):
        await audit_log("password_change_failed", {}, user_id=user["id"], ip=request.client.host)
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"password_hash": hash_password(req.new_password)}}
    )
    await audit_log("password_change_success", {}, user_id=user["id"], ip=request.client.host)
    return {"message": "Password changed successfully"}


@router.post("/suspend")
async def suspend_account(request: Request, user=Depends(get_current_user)):
    await db.users.update_one({"id": user["id"]}, {"$set": {"status": "suspended"}})
    await audit_log("account_suspended", {}, user_id=user["id"], ip=request.client.host)
    return {"message": "Account suspended"}


@router.delete("/delete")
async def delete_account(request: Request, user=Depends(get_current_user)):
    await audit_log("account_deleted", {"email": user.get("email")}, user_id=user["id"], ip=request.client.host)
    await db.users.delete_one({"id": user["id"]})
    await db.saved_topics.delete_many({"user_id": user["id"]})
    await db.payment_transactions.delete_many({"user_id": user["id"]})
    return {"message": "Account deleted"}


@router.put("/auto-renew")
async def toggle_auto_renew(user=Depends(get_current_user)):
    current = user.get("auto_renew", True)
    await db.users.update_one({"id": user["id"]}, {"$set": {"auto_renew": not current}})
    return {"auto_renew": not current}
