from typing import Literal, Optional
from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.core.database import users_collection, enrollments_collection, courses_collection
from app.core.security import require_role
from app.core.tenant import scoped
from app.services.audit import log_action
from app.services.notifications import create_notification

router = APIRouter(prefix="/api/users", tags=["users"])


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    status: str
    phone: Optional[str] = None
    created_at: Optional[datetime] = None
    enrolled_courses_count: Optional[int] = None
    assigned_courses_count: Optional[int] = None


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[Literal["pending", "active", "inactive"]] = None


def _oid(user_id: str) -> ObjectId:
    try:
        return ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")


async def _serialize_user(user: dict) -> UserOut:
    role = user["role"]
    enrolled_count = None
    assigned_count = None
    if role == "student":
        enrolled_count = await enrollments_collection.count_documents({"student_id": str(user["_id"])})
    elif role == "teacher":
        assigned_count = await courses_collection.count_documents({"teacher_ids": str(user["_id"])})

    return UserOut(
        id=str(user["_id"]),
        name=user.get("name", ""),
        email=user["email"],
        role=role,
        status=user.get("status", "active"),
        phone=user.get("phone"),
        created_at=user.get("created_at"),
        enrolled_courses_count=enrolled_count,
        assigned_courses_count=assigned_count,
    )


@router.get("/pending", response_model=list[UserOut])
async def list_pending_users(current_user: dict = Depends(require_role("admin"))):
    """Accounts still awaiting approval. New accounts are created through
    invitations and are active immediately, so this only lists accounts
    that pre-date invite-only onboarding."""
    pending = await users_collection.find(scoped(current_user, {"status": "pending"})).sort("created_at", 1).to_list(length=1000)
    return [await _serialize_user(p) for p in pending]


@router.get("/students", response_model=list[UserOut])
async def list_students(current_user: dict = Depends(require_role("admin"))):
    students = await users_collection.find(scoped(current_user, {"role": "student"})).sort("created_at", -1).to_list(length=1000)
    return [await _serialize_user(s) for s in students]


@router.get("/teachers", response_model=list[UserOut])
async def list_teachers(current_user: dict = Depends(require_role("admin"))):
    teachers = await users_collection.find(scoped(current_user, {"role": "teacher"})).sort("created_at", -1).to_list(length=1000)
    return [await _serialize_user(t) for t in teachers]


@router.post("/{user_id}/approve", response_model=UserOut)
async def approve_user(user_id: str, current_user: dict = Depends(require_role("admin"))):
    result = await users_collection.find_one_and_update(
        scoped(current_user, {"_id": _oid(user_id), "status": "pending"}),
        {"$set": {"status": "active"}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending user not found")

    await create_notification(
        user_id=user_id,
        type="account_approved",
        title="Your account has been approved",
        message="You can now log in and start using the platform.",
        link="/login",
        institute_id=current_user["institute_id"],
    )
    await log_action(
        institute_id=current_user["institute_id"], actor_id=current_user["user_id"],
        action="user.approved", entity_type="user", entity_id=user_id,
    )

    return await _serialize_user(result)


@router.post("/{user_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
async def reject_user(user_id: str, current_user: dict = Depends(require_role("admin"))):
    """Rejects a pending account by deleting it outright — they were never an active account."""
    result = await users_collection.delete_one(scoped(current_user, {"_id": _oid(user_id), "status": "pending"}))
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending user not found")
    await log_action(
        institute_id=current_user["institute_id"], actor_id=current_user["user_id"],
        action="user.rejected", entity_type="user", entity_id=user_id,
    )


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    current_user: dict = Depends(require_role("admin")),
):
    update_fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    if user_id == current_user["user_id"] and update_fields.get("status", "active") != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot deactivate your own account")

    result = await users_collection.find_one_and_update(
        scoped(current_user, {"_id": _oid(user_id)}),
        {"$set": update_fields},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await log_action(
        institute_id=current_user["institute_id"], actor_id=current_user["user_id"],
        action="user.updated", entity_type="user", entity_id=user_id,
        details={"fields": sorted(update_fields.keys())},
    )
    return await _serialize_user(result)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, current_user: dict = Depends(require_role("admin"))):
    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete your own account")

    result = await users_collection.delete_one(scoped(current_user, {"_id": _oid(user_id)}))
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await log_action(
        institute_id=current_user["institute_id"], actor_id=current_user["user_id"],
        action="user.deleted", entity_type="user", entity_id=user_id,
    )
