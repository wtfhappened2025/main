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
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


# --- Request Logging Middleware ---

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = datetime.now(timezone.utc)

        response = await call_next(request)

        duration_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        logger.info(json.dumps({
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 1),
        }))
        response.headers["X-Request-ID"] = request_id
        return response


# --- Rate Limiting Middleware ---

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter. For production, use Redis-backed."""

    def __init__(self, app, default_rpm: int = 60, auth_rpm: int = 10):
        super().__init__(app)
        self.default_rpm = default_rpm
        self.auth_rpm = auth_rpm
        self._requests: dict = {}  # {ip: [(timestamp, path), ...]}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        now = datetime.now(timezone.utc)

        # Choose limit based on path
        is_auth = "/auth/login" in path or "/auth/register" in path or "/admin/login" in path
        rpm_limit = self.auth_rpm if is_auth else self.default_rpm

        # Clean old entries (older than 60s)
        key = f"{client_ip}:{path}" if is_auth else client_ip
        if key not in self._requests:
            self._requests[key] = []
        self._requests[key] = [
            ts for ts in self._requests[key]
            if (now - ts).total_seconds() < 60
        ]

        if len(self._requests[key]) >= rpm_limit:
            return JSONResponse(
                status_code=429,
                content={"success": False, "error": {"message": "Too many requests", "code": 429}},
            )

        self._requests[key].append(now)

        # Periodic cleanup (every 100 requests)
        if sum(len(v) for v in self._requests.values()) > 10000:
            self._requests.clear()

        return await call_next(request)
