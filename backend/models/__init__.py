from pydantic import BaseModel
from typing import List, Optional


# --- Auth Models ---

class RegisterRequest(BaseModel):
    email: Optional[str] = None
    mobile: Optional[str] = None
    password: str
    name: str


class LoginRequest(BaseModel):
    identifier: str
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
    identifier: str


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


# --- Subscription Models ---

class SubscriptionCheckoutRequest(BaseModel):
    origin_url: str


# --- Admin Models ---

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
    system_prompt: str = ""
    task_prompt: str = ""


# --- Content Models ---

class ExplainRequest(BaseModel):
    input: str


class ReactionRequest(BaseModel):
    emoji: str
