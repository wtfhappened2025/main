import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)


def _require(key: str) -> str:
    """Get a required env var. Fail fast with clear error if missing."""
    val = os.environ.get(key)
    if not val:
        logger.critical(f"FATAL: Required environment variable '{key}' is not set. Check .env file.")
        sys.exit(1)
    return val


def _optional(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


class Settings:
    # Database (required)
    MONGO_URL: str = _require("MONGO_URL")
    DB_NAME: str = _require("DB_NAME")

    # Security (required — no fallback for secrets)
    JWT_SECRET: str = _require("JWT_SECRET")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 72
    REFRESH_TOKEN_DAYS: int = 30

    # CORS
    CORS_ORIGINS: list = _optional("CORS_ORIGINS", "https://web-pulse-4.preview.emergentagent.com").split(",")

    # Stripe
    STRIPE_API_KEY: str = _optional("STRIPE_API_KEY")
    SUBSCRIPTION_PRICE: float = 4.99
    TRIAL_DAYS: int = 2

    # Admin (required — no hardcoded defaults)
    ADMIN_EMAIL: str = _require("ADMIN_EMAIL")
    ADMIN_PASSWORD: str = _require("ADMIN_PASSWORD")

    # Scheduler
    DATA_REFRESH_MINUTES: int = 10

    # X/Twitter
    X_API_KEY: str = _optional("X_API_KEY")
    X_API_SECRET: str = _optional("X_API_SECRET")
    X_ACCESS_TOKEN: str = _optional("X_ACCESS_TOKEN")
    X_ACCESS_SECRET: str = _optional("X_ACCESS_SECRET")
    X_BEARER_TOKEN: str = _optional("X_BEARER_TOKEN")

    # Resend (email)
    RESEND_API_KEY: str = _optional("RESEND_API_KEY")
    SENDER_EMAIL: str = _optional("SENDER_EMAIL", "onboarding@resend.dev")

    # Environment
    ENVIRONMENT: str = _optional("ENVIRONMENT", "production")
    DEBUG: bool = ENVIRONMENT == "development"

    # Rate limits
    AI_RPM_PER_USER: int = 5       # AI explanation calls per user per minute
    AI_RPM_ANONYMOUS: int = 3      # AI calls for non-authenticated users per minute


settings = Settings()
