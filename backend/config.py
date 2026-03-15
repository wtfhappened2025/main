import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')


class Settings:
    # Database
    MONGO_URL: str = os.environ.get("MONGO_URL")
    DB_NAME: str = os.environ.get("DB_NAME")

    # Security
    JWT_SECRET: str = os.environ.get("JWT_SECRET", secrets.token_hex(64))
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 72

    # CORS
    CORS_ORIGINS: list = os.environ.get("CORS_ORIGINS", "https://web-pulse-4.preview.emergentagent.com").split(",")

    # Stripe
    STRIPE_API_KEY: str = os.environ.get("STRIPE_API_KEY", "")
    SUBSCRIPTION_PRICE: float = 4.99
    TRIAL_DAYS: int = 2

    # Admin
    ADMIN_EMAIL: str = os.environ.get("ADMIN_EMAIL", "admin@wtfhappened.app")
    ADMIN_PASSWORD: str = os.environ.get("ADMIN_PASSWORD", "WTFadmin2026!")

    # Scheduler
    DATA_REFRESH_MINUTES: int = 10

    # X/Twitter
    X_API_KEY: str = os.environ.get("X_API_KEY", "")
    X_API_SECRET: str = os.environ.get("X_API_SECRET", "")
    X_ACCESS_TOKEN: str = os.environ.get("X_ACCESS_TOKEN", "")
    X_ACCESS_SECRET: str = os.environ.get("X_ACCESS_SECRET", "")
    X_BEARER_TOKEN: str = os.environ.get("X_BEARER_TOKEN", "")

    # Environment
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "production")
    DEBUG: bool = ENVIRONMENT == "development"


settings = Settings()
