from datetime import datetime, timezone


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


def safe_user(user: dict) -> dict:
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


# Category color mapping (shared across routes)
CATEGORY_COLORS = {
    "technology": {"bg": "#EBF5FF", "accent": "#3B82F6"},
    "finance": {"bg": "#F0FDF4", "accent": "#22C55E"},
    "economy": {"bg": "#FFFBEB", "accent": "#F59E0B"},
    "ai": {"bg": "#F3E8FF", "accent": "#8B5CF6"},
    "crypto": {"bg": "#FFF7ED", "accent": "#F97316"},
    "science": {"bg": "#EDE9FE", "accent": "#7C3AED"},
    "world_news": {"bg": "#FEF2F2", "accent": "#EF4444"},
    "internet_culture": {"bg": "#FFF1F2", "accent": "#F43F5E"},
    "politics": {"bg": "#FEF2F2", "accent": "#DC2626"},
    "entertainment": {"bg": "#FDF2F8", "accent": "#EC4899"},
    "lifestyle": {"bg": "#FAF5FF", "accent": "#A855F7"},
}

# Interest-to-category mapping
INTEREST_TO_CATEGORY = {
    "technology": "technology", "ai": "ai", "startups": "technology",
    "finance": "finance", "crypto": "crypto", "business": "economy",
    "global news": "world_news", "politics": "politics", "science": "science",
    "space": "science", "health": "science", "psychology": "science",
    "internet culture": "internet_culture", "memes": "internet_culture",
    "viral trends": "internet_culture", "celebrities": "entertainment",
    "movies & tv": "entertainment", "music": "entertainment",
    "fashion": "lifestyle", "gaming": "technology", "sports": "world_news",
    "travel": "lifestyle", "food": "lifestyle", "strange news": "world_news",
    "future tech": "technology",
}
