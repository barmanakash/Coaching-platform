from datetime import datetime, timezone
from typing import Optional, Literal

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.database import classes_collection, courses_collection, enrollments_collection, users_collection
from app.core.security import get_current_user
from app.core.tenant import scoped
from app.services.notifications import create_notification

router = APIRouter(prefix="/api/classes", tags=["classes"])


def _oid(id_str: str, label: str = "id") -> ObjectId:
    try:
        return ObjectId(id_str)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {label}")


# ---------- Schemas ----------

class ClassCreateRequest(BaseModel):
    course_id: str
    title: str = Field(min_length=2, max_length=150)
    description: str = ""
    scheduled_at: datetime
    duration_minutes: int = Field(default=45, ge=5, le=300)


class ClassUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=None, ge=5, le=300)


class ClassOut(BaseModel):
    id: str
    course_id: str
    course_title: str
    teacher_id: str
    teacher_name: str
    title: str
    description: str
    scheduled_at: datetime
    duration_minutes: int
    status: Literal["scheduled", "live", "ended"]
    created_at: datetime


# ---------- Helpers ----------

async def _serialize_class(c: dict) -> ClassOut:
    course = await courses_collection.find_one({"_id": ObjectId(c["course_id"])})
    teacher = await users_collection.find_one({"_id": ObjectId(c["teacher_id"])})
    return ClassOut(
        id=str(c["_id"]),
        course_id=c["course_id"],
        course_title=course["title"] if course else "Unknown course",
        teacher_id=c["teacher_id"],
        teacher_name=teacher["name"] if teacher else "Unknown",
        title=c["title"],
        description=c.get("description", ""),
        scheduled_at=c["scheduled_at"],
        duration_minutes=c.get("duration_minutes", 45),
        status=c.get("status", "scheduled"),
        created_at=c["created_at"],
    )


async def _get_class_or_404(class_id: str, current_user: dict) -> dict:
    cls = await classes_collection.find_one(scoped(current_user, {"_id": _oid(class_id, "class id")}))
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return cls


async def _assert_can_manage(cls: dict, current_user: dict):
    if current_user["role"] == "admin":
        return
    if current_user["role"] == "teacher" and current_user["user_id"] == cls["teacher_id"]:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot manage this class")


async def _assert_can_view(cls: dict, current_user: dict):
    role = current_user["role"]
    if role == "admin":
        return
    if role == "teacher" and current_user["user_id"] == cls["teacher_id"]:
        return
    if role == "student":
        enrollment = await enrollments_collection.find_one(
            scoped(current_user, {"course_id": cls["course_id"], "student_id": current_user["user_id"]})
        )
        if enrollment:
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot view this class")


# ---------- Endpoints ----------

@router.post("", response_model=ClassOut, status_code=status.HTTP_201_CREATED)
async def create_class(payload: ClassCreateRequest, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ("teacher", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can schedule classes")

    course = await courses_collection.find_one(scoped(current_user, {"_id": _oid(payload.course_id, "course id")}))
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    if current_user["role"] == "teacher" and current_user["user_id"] not in course.get("teacher_ids", []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not assigned to this course")

    now = datetime.now(timezone.utc)
    doc = {
        "institute_id": current_user["institute_id"],
        "course_id": payload.course_id,
        "teacher_id": current_user["user_id"],
        "title": payload.title,
        "description": payload.description,
        "scheduled_at": payload.scheduled_at,
        "duration_minutes": payload.duration_minutes,
        "status": "scheduled",
        "created_at": now,
    }
    result = await classes_collection.insert_one(doc)
    doc["_id"] = result.inserted_id

    enrollments = await enrollments_collection.find(
        scoped(current_user, {"course_id": payload.course_id})
    ).to_list(length=1000)
    for e in enrollments:
        await create_notification(
            user_id=e["student_id"],
            type="class_new",
            title="New class scheduled",
            message=f'"{payload.title}" on {payload.scheduled_at.strftime("%b %d, %I:%M %p")}',
            link="/student/classes",
            institute_id=current_user["institute_id"],
        )

    return await _serialize_class(doc)


@router.get("", response_model=list[ClassOut])
async def list_classes(current_user: dict = Depends(get_current_user)):
    role = current_user["role"]
    if role == "admin":
        query = scoped(current_user)
    elif role == "teacher":
        query = scoped(current_user, {"teacher_id": current_user["user_id"]})
    else:  # student
        enrollments = await enrollments_collection.find(
            scoped(current_user, {"student_id": current_user["user_id"]})
        ).to_list(length=1000)
        course_ids = [e["course_id"] for e in enrollments]
        query = scoped(current_user, {"course_id": {"$in": course_ids}})

    classes = await classes_collection.find(query).sort("scheduled_at", 1).to_list(length=500)
    return [await _serialize_class(c) for c in classes]


@router.get("/{class_id}", response_model=ClassOut)
async def get_class(class_id: str, current_user: dict = Depends(get_current_user)):
    cls = await _get_class_or_404(class_id, current_user)
    await _assert_can_view(cls, current_user)
    return await _serialize_class(cls)


@router.patch("/{class_id}", response_model=ClassOut)
async def update_class(class_id: str, payload: ClassUpdateRequest, current_user: dict = Depends(get_current_user)):
    cls = await _get_class_or_404(class_id, current_user)
    await _assert_can_manage(cls, current_user)

    update_fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    result = await classes_collection.find_one_and_update(
        {"_id": cls["_id"]}, {"$set": update_fields}, return_document=True,
    )
    return await _serialize_class(result)


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(class_id: str, current_user: dict = Depends(get_current_user)):
    cls = await _get_class_or_404(class_id, current_user)
    await _assert_can_manage(cls, current_user)
    await classes_collection.delete_one({"_id": cls["_id"]})


@router.post("/{class_id}/start", response_model=ClassOut)
async def start_class(class_id: str, current_user: dict = Depends(get_current_user)):
    cls = await _get_class_or_404(class_id, current_user)
    await _assert_can_manage(cls, current_user)

    result = await classes_collection.find_one_and_update(
        {"_id": cls["_id"]}, {"$set": {"status": "live"}}, return_document=True,
    )

    enrollments = await enrollments_collection.find(
        scoped(current_user, {"course_id": cls["course_id"]})
    ).to_list(length=1000)
    for e in enrollments:
        await create_notification(
            user_id=e["student_id"],
            type="class_live",
            title="Class is starting now",
            message=f'"{cls["title"]}" has started \u2014 join now',
            link="/student/classes",
            institute_id=current_user["institute_id"],
        )

    return await _serialize_class(result)


@router.post("/{class_id}/end", response_model=ClassOut)
async def end_class(class_id: str, current_user: dict = Depends(get_current_user)):
    cls = await _get_class_or_404(class_id, current_user)
    await _assert_can_manage(cls, current_user)

    result = await classes_collection.find_one_and_update(
        {"_id": cls["_id"]}, {"$set": {"status": "ended"}}, return_document=True,
    )
    return await _serialize_class(result)
