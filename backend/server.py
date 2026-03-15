"""
WTFHappened API — Main application entry point.
All business logic lives in /routes, /services, /utils, /models.
"""
import logging
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from config import settings
from database import create_indexes, client
from middleware import SecurityHeadersMiddleware, RequestLoggingMiddleware, RateLimitMiddleware
from services.scheduler import seed_initial_data, start_scheduler, stop_scheduler

# Routes
from routes.auth import router as auth_router
from routes.content import router as content_router
from routes.subscription import router as subscription_router
from routes.admin import router as admin_router
from routes.system import router as system_router

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s %(message)s',
)
logger = logging.getLogger("wtfhappened")

# --- App ---
app = FastAPI(title="WTFHappened API", version="2.0.0")

# --- Middleware (order matters: last added = first executed) ---
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, default_rpm=60, auth_rpm=10)

# --- Global Exception Handler ---
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(status_code=500, content={
        "success": False, "error": {"message": "Internal server error", "code": 500}
    })

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={
        "success": False, "error": {"message": "Not found", "code": 404}
    })

# --- Register Routes ---
app.include_router(auth_router)
app.include_router(content_router)
app.include_router(subscription_router)
app.include_router(admin_router)
app.include_router(system_router)

# --- Lifecycle ---
@app.on_event("startup")
async def startup():
    await create_indexes()
    await seed_initial_data()
    await start_scheduler()
    logger.info("WTFHappened API v2.0 started")

@app.on_event("shutdown")
async def shutdown():
    stop_scheduler()
    client.close()
