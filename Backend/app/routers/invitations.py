"""
Admin-invite-only onboarding (Institute Admin side).

The invite link is returned ONCE, when the invitation is created or
regenerated — only a hash is stored. Until email delivery is wired in, the
admin copies the link and sends it to the invitee themselves.
The public accept/preview endpoints live in routers/auth.py.
"""

from datetime import datetime, timezone
from typing import Literal, Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.core.database import invitations_collection, users_collection
from app.core.security import require_role
from app.core.tenant import scoped
from app.services.audit import log_action
from app.services.invitations import (
    build_invite_url,
    invitation_status,
    issue_invitation,
    reissue_invitation,
)

router = APIRouter(prefix="/api/invitations", tags=["invitations"])


class InvitationCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    # Admins can only invite teachers and students. Institute admins are
    # created by the platform Super Admin; parents arrive with the parent module.
    role: Literal["teacher", "student"]


class InvitationOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    status: Literal["pending", "accepted", "revoked", "expired"]
    expires_at: datetime
    created_at: datetime
    accepted_at: Optional[datetime] = None


class InvitationCreatedOut(InvitationOut):
    """Returned only when a link is minted: the one time the raw token is visible."""
    invite_token: str
    invite_url: str


def serialize_invitation(invitation: dict) -> InvitationOut:
    return InvitationOut(
        id=str(invitation["_id"]),
        name=invitation["name"],
        email=invitation["email"],
        role=invitation["role"],
        status=invitation_status(invitation),
        expires_at=invitation["expires_at"],
        created_at=invitation["created_at"],
        accepted_at=invitation.get("accepted_at"),
    )


def serialize_created(invitation: dict, token: str) -> InvitationCreatedOut:
    base = serialize_invitation(invitation)
    return InvitationCreatedOut(**base.model_dump(), invite_token=token, invite_url=build_invite_url(token))


def _oid(invitation_id: str) -> ObjectId:
    try:
        return ObjectId(invitation_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invitation id")


@router.post("", response_model=InvitationCreatedOut, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    payload: InvitationCreateRequest,
    current_user: dict = Depends(require_role("admin")),
):
    invitation, token = await issue_invitation(
        institute_id=current_user["institute_id"],
        name=payload.name,
        email=payload.email,
        role=payload.role,
        invited_by=current_user["user_id"],
    )
    await log_action(
        institute_id=current_user["institute_id"], actor_id=current_user["user_id"],
        action="invitation.created", entity_type="invitation", entity_id=str(invitation["_id"]),
        details={"email": payload.email, "role": payload.role},
    )
    return serialize_created(invitation, token)


@router.get("", response_model=list[InvitationOut])
async def list_invitations(current_user: dict = Depends(require_role("admin"))):
    invitations = await invitations_collection.find(scoped(current_user)).sort("created_at", -1).to_list(length=500)
    return [serialize_invitation(i) for i in invitations]


@router.post("/{invitation_id}/regenerate", response_model=InvitationCreatedOut)
async def regenerate_invitation(invitation_id: str, current_user: dict = Depends(require_role("admin"))):
    """Mints a fresh link for a pending or expired invitation (the old link stops working)."""
    invitation = await invitations_collection.find_one(scoped(current_user, {"_id": _oid(invitation_id)}))
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    if invitation_status(invitation) not in ("pending", "expired"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending or expired invitations can be regenerated",
        )
    if await users_collection.find_one({"email": invitation["email"]}, {"_id": 1}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    updated, token = await reissue_invitation(invitation)
    await log_action(
        institute_id=current_user["institute_id"], actor_id=current_user["user_id"],
        action="invitation.regenerated", entity_type="invitation", entity_id=invitation_id,
    )
    return serialize_created(updated, token)


@router.delete("/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invitation(invitation_id: str, current_user: dict = Depends(require_role("admin"))):
    result = await invitations_collection.update_one(
        scoped(current_user, {"_id": _oid(invitation_id), "status": "pending"}),
        {"$set": {"status": "revoked", "revoked_at": datetime.now(timezone.utc)}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending invitation not found")
    await log_action(
        institute_id=current_user["institute_id"], actor_id=current_user["user_id"],
        action="invitation.revoked", entity_type="invitation", entity_id=invitation_id,
    )
