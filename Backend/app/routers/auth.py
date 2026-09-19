from datetime import datetime, timezone
from typing import Literal

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field

from app.core.database import users_collection
from app.core.security import hash_password, verify_password, create_access_token
from app.core.rate_limit import limiter
from app.core.logging_config import logger
from app.services.notifications import create_notification

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    # Public signup is only for Teacher/Student. Admin accounts are seeded
    # separately (see app/scripts/seed_admin.py) and never self-registered.
    role: Literal["teacher", "student"]
    phone: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    name: str


class SignupResponse(BaseModel):
    message: str
    email: EmailStr
    status: str = "pending"


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, payload: LoginRequest):
    user = await users_collection.find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        logger.warning(f"Failed login attempt for email={payload.email} from {request.client.host}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    account_status = user.get("status", "active")
    if account_status == "pending":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending admin approval. You'll be able to log in once an admin verifies you.",
        )
    if account_status == "inactive":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    token = create_access_token({"sub": str(user["_id"]), "role": user["role"]})
    return TokenResponse(
        access_token=token,
        role=user["role"],
        user_id=str(user["_id"]),
        name=user.get("name", ""),
    )


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def signup(request: Request, payload: SignupRequest):
    existing = await users_collection.find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    new_user = {
        "name": payload.name,
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "role": payload.role,
        "phone": payload.phone,
        # New self-signups start as "pending" and cannot log in until an
        # admin approves them (see PATCH /api/users/{id}/approve).
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
    }
    result = await users_collection.insert_one(new_user)

    admins = await users_collection.find({"role": "admin"}).to_list(length=100)
    for admin in admins:
        await create_notification(
            user_id=str(admin["_id"]),
            type="signup_pending",
            title="New signup pending approval",
            message=f"{payload.name} signed up as a {payload.role}",
            link="/admin/approvals",
        )

    return SignupResponse(
        message="Your account has been created and is pending admin approval. You'll be able to log in once approved.",
        email=payload.email,
        status="pending",
    )


# NOTE: This /signup endpoint is the self-service path for Teacher/Student.
# Accounts start as "pending" and require admin approval (app/routers/users.py)
# before they can log in. Admin accounts are seeded separately and never
# self-registered (see app/scripts/seed_admin.py).
