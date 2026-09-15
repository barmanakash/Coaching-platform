# Backend — Coaching & School Learning Platform

FastAPI + MongoDB (Motor) + JWT + WebSocket backend.

## Setup

```bash
cd Backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env       # then edit values (Mongo URI, JWT secret)
```

## Run

```bash
uvicorn app.main:app --reload
```

- API base: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Structure

```
app/
  main.py            # FastAPI app, CORS, router registration
  core/
    config.py        # Settings (env vars)
    security.py       # Password hashing, JWT, role-based auth dependencies
    database.py       # Motor client + collection references
  models/            # Pydantic/Mongo document models
  schemas/           # Request/response schemas
  routers/           # API route handlers (grouped by resource)
  services/          # Business logic
  repositories/      # Data access layer
  websocket/
    manager.py       # Connection manager (per-user socket tracking)
    chat.py          # (to be added) chat socket route
    presence.py       # (to be added) online/offline presence route
```

## Development order (per PRD §33)

1. Project setup ✅ (this)
2. Authentication (`/api/auth/login` ✅ — registration next)
3. Admin dashboard / users / courses
4. Teacher dashboard / resources / classes
5. Student dashboard / course consumption
6. Doubts
7. WebSocket chat / presence
8. Notifications
9. Live classes / WebRTC
10. Testing, security, deployment
