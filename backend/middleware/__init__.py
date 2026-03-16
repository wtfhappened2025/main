import logging
import json
import uuid
from datetime import datetime, timezone
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("wtfhappened")


# --- Standardized Response Helpers ---

def success_response(data=None, message=None):
    body = {"success": True}
    if data is not None:
        body["data"] = data
    if message:
        body["message"] = message
    return body


def error_response(message: str, code: int = 400, details=None):
    body = {"success": False, "error": {"message": message, "code": code}}
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=code, content=body)


# --- Security Headers Middleware ---

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store" if "/api/" in str(request.url) else "public, max-age=3600"
        return response


# --- Request Logging Middleware ---

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = datetime.now(timezone.utc)

        response = await call_next(request)

        duration_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 1),
            "ip": request.client.host if request.client else "unknown",
        }
        if response.status_code >= 400:
            logger.warning(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))
        response.headers["X-Request-ID"] = request_id
        return response


# --- Rate Limiting Middleware (IP + per-user on expensive endpoints) ---

class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory rate limiter with per-user AI endpoint limits."""

    def __init__(self, app, default_rpm: int = 60, auth_rpm: int = 10, ai_rpm: int = 5):
        super().__init__(app)
        self.default_rpm = default_rpm
        self.auth_rpm = auth_rpm
        self.ai_rpm = ai_rpm
        self._requests: dict = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        now = datetime.now(timezone.utc)

        # Determine rate limit category
        is_auth = "/auth/login" in path or "/auth/register" in path or "/admin/login" in path
        is_ai = "/explain" in path or "/explanation/" in path

        if is_auth:
            rpm_limit = self.auth_rpm
            key = f"auth:{client_ip}:{path}"
        elif is_ai:
            # Per-user for AI: extract user ID from auth header if present
            auth_header = request.headers.get("authorization", "")
            user_key = "anon"
            if auth_header.startswith("Bearer "):
                try:
                    import jwt
                    from config import settings
                    payload = jwt.decode(auth_header.split(" ")[1], settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
                    user_key = payload.get("sub", "anon")
                except Exception:
                    pass
            rpm_limit = self.ai_rpm
            key = f"ai:{user_key}"
        else:
            rpm_limit = self.default_rpm
            key = f"general:{client_ip}"

        # Clean old entries
        if key not in self._requests:
            self._requests[key] = []
        self._requests[key] = [
            ts for ts in self._requests[key]
            if (now - ts).total_seconds() < 60
        ]

        if len(self._requests[key]) >= rpm_limit:
            logger.warning(json.dumps({
                "event": "rate_limit_exceeded",
                "key": key,
                "path": path,
                "ip": client_ip,
                "limit": rpm_limit,
            }))
            return JSONResponse(
                status_code=429,
                content={"success": False, "error": {"message": "Too many requests. Please slow down.", "code": 429}},
            )

        self._requests[key].append(now)

        # Periodic cleanup
        if sum(len(v) for v in self._requests.values()) > 10000:
            self._requests.clear()

        return await call_next(request)
