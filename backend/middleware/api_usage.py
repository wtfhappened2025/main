"""API usage tracking — logs every AI/expensive endpoint call for cost monitoring."""
import logging
import json
from datetime import datetime, timezone
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("api_usage")

# Endpoints considered "expensive" (AI calls, external API hits)
TRACKED_ENDPOINTS = {
    "/api/explanation/": "ai_explanation",
    "/api/explain": "ai_explain",
    "/api/render-card/": "card_render",
    "/api/refresh-trending": "data_refresh",
    "/api/admin/publish-now": "auto_publish",
}


class APIUsageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        tracked_type = None

        for prefix, usage_type in TRACKED_ENDPOINTS.items():
            if path.startswith(prefix):
                tracked_type = usage_type
                break

        response = await call_next(request)

        if tracked_type and request.method in ("GET", "POST") and response.status_code < 400:
            # Extract user from auth header
            user_id = "anonymous"
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                try:
                    import jwt
                    from config import settings
                    payload = jwt.decode(auth_header.split(" ")[1], settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
                    user_id = payload.get("sub", "anonymous")
                except Exception:
                    pass

            usage_entry = {
                "endpoint": path,
                "type": tracked_type,
                "method": request.method,
                "user_id": user_id,
                "ip": request.client.host if request.client else "unknown",
                "status": response.status_code,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            try:
                from database import db
                await db.api_usage.insert_one(usage_entry)
            except Exception:
                pass

            logger.info(json.dumps({"api_usage": tracked_type, "user_id": user_id, "status": response.status_code}))

        return response
