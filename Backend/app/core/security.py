from datetime import datetime, timedelta, timezone
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.database import users_collection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Platform-level role: manages institutes, not any single institute's data.
# Every other role ("admin" = Institute Admin, "teacher", "student") belongs
# to exactly one institute.
SUPER_ADMIN_ROLE = "super_admin"


# ---------- Password hashing ----------

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ---------- JWT ----------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """data should contain at least {'sub': user_id, 'role': role, 'institute_id': institute_id}"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def authenticate_token(token: str) -> dict:
    """
    Validates a JWT *and* re-checks the account in the database, so that a
    deactivated/deleted user, or a changed role/institute, takes effect on
    the very next request instead of when the token eventually expires.

    The role and institute are taken from the database, never from the
    token payload, so they cannot be forged or go stale.

    Shared by the HTTP dependencies below and by the WebSocket routes.
    Returns {'user_id', 'role', 'institute_id'}.
    """
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id or not payload.get("role"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    try:
        oid = ObjectId(user_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = await users_collection.find_one({"_id": oid}, {"role": 1, "status": 1, "institute_id": 1})
    if not user or user.get("status", "active") != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account is no longer active",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = user["role"]
    institute_id = user.get("institute_id")
    if role != SUPER_ADMIN_ROLE and not institute_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is not linked to an institute")

    return {"user_id": user_id, "role": role, "institute_id": institute_id}


# ---------- Dependencies ----------

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    The signed-in user of an institute (tenant). Every institute-scoped
    endpoint depends on this, which is what guarantees the caller has an
    `institute_id` to scope queries with. Platform admins are rejected here
    — they use `get_platform_admin` and the /api/super-admin routes.
    """
    user = await authenticate_token(token)
    if user["role"] == SUPER_ADMIN_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform administrators cannot use institute endpoints",
        )
    return user


async def get_platform_admin(token: str = Depends(oauth2_scheme)) -> dict:
    """The platform Super Admin (not tied to any institute)."""
    user = await authenticate_token(token)
    if user["role"] != SUPER_ADMIN_ROLE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform administrator access required")
    return user


def require_role(*allowed_roles: str):
    """Dependency factory for backend-enforced role-based authorization (PRD section 5)."""

    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return role_checker
