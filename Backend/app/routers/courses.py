from typing import Optional, Literal
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.database import courses_collection, users_collection
from app.core.security import require_role, get_current_user

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


async def _serialize_course(course: dict) -> CourseOut:
    teacher_ids = course.get("teacher_ids", [])
    teacher_names = []
    if teacher_ids:
        cursor = users_collection.find({"_id": {"$in": [ObjectId(t) for t in teacher_ids]}})
        teacher_names = [t["name"] async for t in cursor]

    from app.core.database import enrollments_collection
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
    - Admin: sees every course (draft + published).
    - Teacher: sees only courses they are assigned to teach.
    - Student: sees published courses (self-enrollment/assignment UI is a
      future phase, so for now every student can browse the live catalog).
    """
    role = current_user["role"]
    if role == "admin":
        query = {}
    elif role == "teacher":
        query = {"teacher_ids": current_user["user_id"]}
    else:  # student
        query = {"status": "published"}

    courses = await courses_collection.find(query).sort("created_at", -1).to_list(length=1000)
    return [await _serialize_course(c) for c in courses]


@router.get("/{course_id}", response_model=CourseOut)
async def get_course(course_id: str, current_user: dict = Depends(get_current_user)):
    course = await courses_collection.find_one({"_id": _oid(course_id)})
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    role = current_user["role"]
    if role == "teacher" and current_user["user_id"] not in course.get("teacher_ids", []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot view this course")
    if role == "student" and course.get("status") != "published":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot view this course")

    return await _serialize_course(course)


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
async def create_course(
    payload: CourseCreateRequest,
    current_user: dict = Depends(require_role("admin")),
):
    doc = {
        "title": payload.title,
        "description": payload.description,
        "teacher_ids": payload.teacher_ids,
        "status": "draft",
        "created_at": datetime.now(timezone.utc),
    }
    result = await courses_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
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

    result = await courses_collection.find_one_and_update(
        {"_id": _oid(course_id)},
        {"$set": update_fields},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return await _serialize_course(result)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(course_id: str, current_user: dict = Depends(require_role("admin"))):
    result = await courses_collection.delete_one({"_id": _oid(course_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
