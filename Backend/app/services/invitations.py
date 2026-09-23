"""
Invitation logic (admin-invite-only onboarding).

Accounts are never self-registered. An Institute Admin (or the platform
Super Admin, for an institute's first admin) issues an invitation; the
invitee opens the one-time link, sets a password, and their account is
created already active and bound to the inviting institute.

Only a SHA-256 hash of the token is stored, so a database leak does not
expose usable invite links. The raw token is shown once, at creation.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.database import invitations_collection, users_collection


def generate_invite_token() -> str:
    return secrets.token_urlsafe(32)


def hash_invite_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def build_invite_url(token: str) -> str:
    origin = settings.frontend_origin.split(",")[0].strip().rstrip("/")
    return f"{origin}/accept-invite?token={token}"


def _as_utc(value: datetime) -> datetime:
    # PyMongo returns naive datetimes (already UTC) unless tz_aware is set.
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _new_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.invitation_expire_days)


def invitation_status(invitation: dict) -> str:
    """pending / accepted / revoked, or 'expired' for a pending invite past its deadline."""
    stored = invitation.get("status", "pending")
    if stored == "pending" and _as_utc(invitation["expires_at"]) <= datetime.now(timezone.utc):
        return "expired"
    return stored


async def issue_invitation(
    *, institute_id: str, name: str, email: str, role: str, invited_by: str, student_ids: list[str] | None = None,
) -> tuple[dict, str]:
    """Creates an invitation and returns (document, raw_token).

    Any earlier still-pending invitation to the same email in the same
    institute is revoked, so only the newest link works.

    `student_ids` is only meaningful for role="parent": the children the
    parent will be linked to the moment they accept.
    """
    if await users_collection.find_one({"email": email}, {"_id": 1}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    now = datetime.now(timezone.utc)
    await invitations_collection.update_many(
        {"institute_id": institute_id, "email": email, "status": "pending"},
        {"$set": {"status": "revoked", "revoked_at": now}},
    )

    token = generate_invite_token()
    doc = {
        "institute_id": institute_id,
        "name": name,
        "email": email,
        "role": role,
        "student_ids": student_ids or [],
        "token_hash": hash_invite_token(token),
        "status": "pending",
        "invited_by": invited_by,
        "expires_at": _new_expiry(),
        "created_at": now,
    }
    result = await invitations_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc, token


async def reissue_invitation(invitation: dict) -> tuple[dict, str]:
    """Replaces the token and extends the deadline of a pending/expired invitation."""
    token = generate_invite_token()
    updated = await invitations_collection.find_one_and_update(
        {"_id": invitation["_id"]},
        {"$set": {
            "token_hash": hash_invite_token(token),
            "status": "pending",
            "expires_at": _new_expiry(),
            "regenerated_at": datetime.now(timezone.utc),
        }},
        return_document=True,
    )
    return updated, token
