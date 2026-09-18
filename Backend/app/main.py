from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.database import ping_database
from app.core.storage import MEDIA_ROOT
from app.routers import auth, users, courses, admin, modules, doubts, conversations, notifications, enrollments, classes, uploads
from app.websocket import chat as ws_chat, presence as ws_presence, meeting as ws_meeting

app = FastAPI(title="Coaching & School Learning Platform API", version="0.1.0")

os.makedirs(MEDIA_ROOT, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")

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
