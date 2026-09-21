from typing import Optional, Literal
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.database import courses_collection, users_collection, enrollments_collection
from app.core.security import require_role, get_current_user
from app.core.tenant import scoped
from app.services.audit import log_action

router = APIRouter(prefix="/api/courses", tags=["courses"])


class CourseCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: str = ""
    teacher_ids: list[str] = []


class CourseUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    teacher_ids: Optional[list[str]] = None
    status: Optional[Literal["draft", "published"]] = None


class CourseOut(BaseModel):
    id: str
    title: str
    description: str
    status: str
    teacher_ids: list[str] = []
    teacher_names: list[str] = []
    student_count: int = 0
    created_at: Optional[datetime] = None


def _oid(course_id: str) -> ObjectId:
    try:
        return ObjectId(course_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid course id")


async def _assert_teachers_in_institute(teacher_ids: list[str], current_user: dict) -> None:
    """Every assigned teacher must be a teacher of THIS institute."""
    unique_ids = set(teacher_ids)
    if not unique_ids:
        return
    count = await users_collection.count_documents(
        scoped(current_user, {"_id": {"$in": [_oid(t) for t in unique_ids]}, "role": "teacher"})
    )
    if count != len(unique_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more selected teachers do not exist in this institute",
        )


async def _serialize_course(course: dict) -> CourseOut:
    teacher_ids = course.get("teacher_ids", [])
    teacher_names = []
    if teacher_ids:
        cursor = users_collection.find({"_id": {"$in": [ObjectId(t) for t in teacher_ids]}})
        teacher_names = [t["name"] async for t in cursor]

    student_count = await enrollments_collection.count_documents({"course_id": str(course["_id"])})

    return CourseOut(
        id=str(course["_id"]),
        title=course["title"],
        description=course.get("description", ""),
        status=course.get("status", "draft"),
        teacher_ids=teacher_ids,
        teacher_names=teacher_names,
        student_count=student_count,
        created_at=course.get("created_at"),
    )


@router.get("", response_model=list[CourseOut])
async def list_courses(current_user: dict = Depends(get_current_user)):
    """
    - Admin: sees every course of their institute (draft + published).
    - Teacher: sees only courses they are assigned to teach.
    - Student: sees only courses they've been enrolled in by an admin
      (see /api/courses/{id}/enrollments), and only while published.
    """
    role = current_user["role"]
    if role == "admin":
        query = scoped(current_user)
    elif role == "teacher":
        query = scoped(current_user, {"teacher_ids": current_user["user_id"]})
    else:  # student
        enrollments = await enrollments_collection.find(
            scoped(current_user, {"student_id": current_user["user_id"]})
        ).to_list(length=1000)
        course_ids = [ObjectId(e["course_id"]) for e in enrollments]
        query = scoped(current_user, {"_id": {"$in": course_ids}, "status": "published"})

    courses = await courses_collection.find(query).sort("created_at", -1).to_list(length=1000)
    return [await _serialize_course(c) for c in courses]


@router.get("/{course_id}", response_model=CourseOut)
async def get_course(course_id: str, current_user: dict = Depends(get_current_user)):
    course = await courses_collection.find_one(scoped(current_user, {"_id": _oid(course_id)}))
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    role = current_user["role"]
    if role == "teacher" and current_user["user_id"] not in course.get("teacher_ids", []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot view this course")
    if role == "student":
        enrollment = await enrollments_collection.find_one(
            scoped(current_user, {"course_id": course_id, "student_id": current_user["user_id"]})
        )
        if not enrollment or course.get("status") != "published":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot view this course")

    return await _serialize_course(course)


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
async def create_course(
    payload: CourseCreateRequest,
    current_user: dict = Depends(require_role("admin")),
):
    await _assert_teachers_in_institute(payload.teacher_ids, current_user)

    doc = {
        "institute_id": current_user["institute_id"],
        "title": payload.title,
        "description": payload.description,
        "teacher_ids": payload.teacher_ids,
        "status": "draft",
        "created_at": datetime.now(timezone.utc),
    }
    result = await courses_collection.insert_one(doc)
    doc["_id"] = result.inserted_id

    await log_action(
        institute_id=current_user["institute_id"], actor_id=current_user["user_id"],
        action="course.created", entity_type="course", entity_id=str(result.inserted_id),
        details={"title": payload.title},
    )
    return await _serialize_course(doc)


@router.patch("/{course_id}", response_model=CourseOut)
async def update_course(
    course_id: str,
    payload: CourseUpdateRequest,
    current_user: dict = Depends(require_role("admin")),
):
    update_fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    if "teacher_ids" in update_fields:
        await _assert_teachers_in_institute(update_fields["teacher_ids"], current_user)

    result = await courses_collection.find_one_and_update(
        scoped(current_user, {"_id": _oid(course_id)}),
        {"$set": update_fields},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    await log_action(
        institute_id=current_user["institute_id"], actor_id=current_user["user_id"],
        action="course.updated", entity_type="course", entity_id=course_id,
        details={"fields": sorted(update_fields.keys())},
    )
    return await _serialize_course(result)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(course_id: str, current_user: dict = Depends(require_role("admin"))):
    result = await courses_collection.delete_one(scoped(current_user, {"_id": _oid(course_id)}))
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    await log_action(
        institute_id=current_user["institute_id"], actor_id=current_user["user_id"],
        action="course.deleted", entity_type="course", entity_id=course_id,
    )
