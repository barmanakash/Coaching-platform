from datetime import datetime, timezone
from typing import Literal

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.core.database import users_collection
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)
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


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    user = await users_collection.find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if user.get("status") == "inactive":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    token = create_access_token({"sub": str(user["_id"]), "role": user["role"]})
    return TokenResponse(
        access_token=token,
        role=user["role"],
        user_id=str(user["_id"]),
        name=user.get("name", ""),
    )


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest):
    existing = await users_collection.find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    new_user = {
        "name": payload.name,
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "role": payload.role,
        "phone": payload.phone,
        "status": "active",
        "created_at": datetime.now(timezone.utc),
    }
    result = await users_collection.insert_one(new_user)

    token = create_access_token({"sub": str(result.inserted_id), "role": payload.role})
    return TokenResponse(
        access_token=token,
        role=payload.role,
        user_id=str(result.inserted_id),
        name=payload.name,
    )


# NOTE: Admin-driven creation of Teacher/Student accounts (with admin approval,
# course assignment, etc.) will be added under /api/users once Student &
# Teacher Management (PRD sections 5 & 6) are built. This /signup endpoint
# is the self-service path only.
