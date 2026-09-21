"""
Platform Super Admin (PRD sections 3 and 29): onboards institutes.

Creating an institute also issues an invitation for its first Institute
Admin, keeping the whole platform invite-only. Subscriptions, plans and
platform analytics arrive in Phase 7.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from pymongo.errors import DuplicateKeyError

from app.core.database import institutes_collection, users_collection
from app.core.security import get_platform_admin
from app.core.validators import validate_institute_code
from app.routers.invitations import InvitationCreatedOut, serialize_created
from app.services.audit import log_action
from app.services.institutes import new_institute_doc
from app.services.invitations import issue_invitation

router = APIRouter(prefix="/api/super-admin", tags=["super admin"])


class InstituteCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    code: str = Field(description="Short unique identifier: lowercase letters, numbers, hyphens")
    admin_name: str = Field(min_length=2, max_length=100)
    admin_email: EmailStr

    _validate_code = field_validator("code")(validate_institute_code)


class InstituteSummaryOut(BaseModel):
    id: str
    name: str
    code: str
    status: str
    created_at: Optional[datetime] = None
    admin_count: int = 0
    teacher_count: int = 0
    student_count: int = 0


class InstituteCreatedOut(BaseModel):
    institute: InstituteSummaryOut
    admin_invitation: InvitationCreatedOut


async def _summarize(institute: dict) -> InstituteSummaryOut:
    institute_id = str(institute["_id"])

    async def count(role: str) -> int:
        return await users_collection.count_documents({"institute_id": institute_id, "role": role})

    return InstituteSummaryOut(
        id=institute_id,
        name=institute["name"],
        code=institute["code"],
        status=institute.get("status", "active"),
        created_at=institute.get("created_at"),
        admin_count=await count("admin"),
        teacher_count=await count("teacher"),
        student_count=await count("student"),
    )


@router.get("/institutes", response_model=list[InstituteSummaryOut])
async def list_institutes(current_user: dict = Depends(get_platform_admin)):
    institutes = await institutes_collection.find({}).sort("created_at", -1).to_list(length=500)
    return [await _summarize(i) for i in institutes]


@router.post("/institutes", response_model=InstituteCreatedOut, status_code=status.HTTP_201_CREATED)
async def create_institute(payload: InstituteCreateRequest, current_user: dict = Depends(get_platform_admin)):
    if await institutes_collection.find_one({"code": payload.code}, {"_id": 1}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An institute with this code already exists")
    if await users_collection.find_one({"email": payload.admin_email}, {"_id": 1}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this admin email already exists")

    doc = new_institute_doc(payload.name, payload.code)
    try:
        result = await institutes_collection.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An institute with this code already exists")
    doc["_id"] = result.inserted_id
    institute_id = str(result.inserted_id)

    invitation, token = await issue_invitation(
        institute_id=institute_id,
        name=payload.admin_name,
        email=payload.admin_email,
        role="admin",
        invited_by=current_user["user_id"],
    )
    await log_action(
        institute_id=institute_id, actor_id=current_user["user_id"],
        action="institute.created", entity_type="institute", entity_id=institute_id,
        details={"name": payload.name, "code": payload.code},
    )

    return InstituteCreatedOut(
        institute=await _summarize(doc),
        admin_invitation=serialize_created(invitation, token),
    )
