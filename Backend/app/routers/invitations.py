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
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

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
    # Admins can invite teachers, students and parents. Institute admins are
    # created by the platform Super Admin instead (see routers/super_admin.py).
    role: Literal["teacher", "student", "parent"]
    # Required (and only meaningful) when role="parent": the children this
    # parent will be linked to the moment they accept the invite.
    student_ids: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def _check_student_ids(self):
        if self.role == "parent" and not self.student_ids:
            raise ValueError("Select at least one student to link this parent to")
        if self.role != "parent" and self.student_ids:
            raise ValueError("student_ids is only used when inviting a parent")
        return self

    @field_validator("student_ids")
    @classmethod
    def _validate_ids(cls, values: list[str]) -> list[str]:
        for value in values:
            if not ObjectId.is_valid(value):
                raise ValueError("Invalid student id")
        # De-duplicate while preserving order.
        seen: set[str] = set()
        return [v for v in values if not (v in seen or seen.add(v))]


class InvitationOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    status: Literal["pending", "accepted", "revoked", "expired"]
    student_ids: list[str] = []
    student_names: list[str] = []
    expires_at: datetime
    created_at: datetime
    accepted_at: Optional[datetime] = None


class InvitationCreatedOut(InvitationOut):
    """Returned only when a link is minted: the one time the raw token is visible."""
    invite_token: str
    invite_url: str


async def _student_names(student_ids: list[str]) -> list[str]:
    if not student_ids:
        return []
    cursor = users_collection.find({"_id": {"$in": [ObjectId(s) for s in student_ids]}}, {"name": 1})
    names_by_id = {str(u["_id"]): u["name"] async for u in cursor}
    return [names_by_id[s] for s in student_ids if s in names_by_id]


async def serialize_invitation(invitation: dict) -> InvitationOut:
    student_ids = invitation.get("student_ids", [])
    return InvitationOut(
        id=str(invitation["_id"]),
        name=invitation["name"],
        email=invitation["email"],
        role=invitation["role"],
        status=invitation_status(invitation),
        student_ids=student_ids,
        student_names=await _student_names(student_ids),
        expires_at=invitation["expires_at"],
        created_at=invitation["created_at"],
        accepted_at=invitation.get("accepted_at"),
    )


async def serialize_created(invitation: dict, token: str) -> InvitationCreatedOut:
    base = await serialize_invitation(invitation)
    return InvitationCreatedOut(**base.model_dump(), invite_token=token, invite_url=build_invite_url(token))


def _oid(invitation_id: str) -> ObjectId:
    try:
        return ObjectId(invitation_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invitation id")


async def _assert_students_in_institute(student_ids: list[str], current_user: dict) -> None:
    count = await users_collection.count_documents(
        scoped(current_user, {"_id": {"$in": [ObjectId(s) for s in student_ids]}, "role": "student"})
    )
    if count != len(student_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more selected students do not exist in this institute",
        )


@router.post("", response_model=InvitationCreatedOut, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    payload: InvitationCreateRequest,
    current_user: dict = Depends(require_role("admin")),
):
    if payload.role == "parent":
        await _assert_students_in_institute(payload.student_ids, current_user)

    invitation, token = await issue_invitation(
        institute_id=current_user["institute_id"],
        name=payload.name,
        email=payload.email,
        role=payload.role,
        invited_by=current_user["user_id"],
        student_ids=payload.student_ids,
    )
    await log_action(
        institute_id=current_user["institute_id"], actor_id=current_user["user_id"],
        action="invitation.created", entity_type="invitation", entity_id=str(invitation["_id"]),
        details={"email": payload.email, "role": payload.role},
    )
    return await serialize_created(invitation, token)


@router.get("", response_model=list[InvitationOut])
async def list_invitations(current_user: dict = Depends(require_role("admin"))):
    invitations = await invitations_collection.find(scoped(current_user)).sort("created_at", -1).to_list(length=500)
    return [await serialize_invitation(i) for i in invitations]


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
    return await serialize_created(updated, token)


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
