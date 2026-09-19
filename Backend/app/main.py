import os

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import ping_database, ensure_indexes
from app.core.storage import MEDIA_ROOT
from app.core.logging_config import logger
from app.core.rate_limit import limiter
from app.routers import auth, users, courses, admin, modules, doubts, conversations, notifications, enrollments, classes, uploads
from app.websocket import chat as ws_chat, presence as ws_presence, meeting as ws_meeting

app = FastAPI(title="Coaching & School Learning Platform API", version="0.1.0")

os.makedirs(MEDIA_ROOT, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")

# ---------- Rate limiting (PRD section 27/32: prevent brute force / abuse) ----------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def _normalize_origin(origin: str) -> str:
    return origin.strip().rstrip("/")


_configured_origins = [
    _normalize_origin(o) for o in settings.frontend_origin.split(",") if o.strip()
]

# In development, allow any localhost/127.0.0.1 port (CRA often bumps to
# 3001, 3002, etc. if 3000 is busy) so this doesn't need editing every time.
# In production, fall back to the explicit FRONTEND_ORIGIN(s) from .env only.
if settings.app_env == "development":
    cors_kwargs = {
        "allow_origins": _configured_origins,
        "allow_origin_regex": r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    }
else:
    cors_kwargs = {"allow_origins": _configured_origins}

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    **cors_kwargs,
)


# ---------- Security headers (PRD section 27) ----------
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(self), camera=(self)"
    if settings.app_env != "development":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


# ---------- Secure error handling (PRD section 27): never leak internals ----------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


@app.on_event("startup")
async def on_startup():
    logger.info(f"Starting up in '{settings.app_env}' mode")
    if settings.app_env != "development" and settings.jwt_secret_key == "change-this-to-a-long-random-secret":
        logger.critical(
            "JWT_SECRET_KEY is still the default placeholder in a non-development environment! "
            "Set a long random secret in .env before exposing this publicly."
        )
    db_ok = await ping_database()
    logger.info(f"MongoDB connection: {'ok' if db_ok else 'FAILED'}")
    if db_ok:
        await ensure_indexes()
        logger.info("Database indexes ensured")


# ---------- Routers (grouped per PRD section 23) ----------
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(courses.router)
app.include_router(admin.router)
app.include_router(modules.router)
app.include_router(doubts.router)
app.include_router(conversations.router)
app.include_router(notifications.router)
app.include_router(enrollments.router)
app.include_router(classes.router)
app.include_router(uploads.router)
# Future: students, teachers (dedicated endpoints beyond /api/users).

# ---------- WebSocket routes ----------
app.include_router(ws_chat.router)
app.include_router(ws_presence.router)
app.include_router(ws_meeting.router)
# Future: /ws/notifications


@app.get("/")
async def root():
    return {"message": "Coaching & School Learning Platform API is running"}


@app.get("/health")
async def health_check():
    db_ok = await ping_database()
    return {"status": "ok" if db_ok else "degraded", "mongodb_connected": db_ok, "env": settings.app_env}
