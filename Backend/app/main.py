from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import ping_database
from app.routers import auth, users, courses, admin

app = FastAPI(title="Coaching & School Learning Platform API", version="0.1.0")

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
# Future: students, teachers (dedicated endpoints beyond /api/users), modules,
# resources, enrollments, classes, doubts, conversations, notifications.

# ---------- WebSocket routes ----------
# Future: /ws/chat/{conversation_id}, /ws/presence,
# /ws/notifications, /ws/meeting/{meeting_id}


@app.get("/")
async def root():
    return {"message": "Coaching & School Learning Platform API is running"}


@app.get("/health")
async def health_check():
    db_ok = await ping_database()
    return {"status": "ok" if db_ok else "degraded", "mongodb_connected": db_ok, "env": settings.app_env}
