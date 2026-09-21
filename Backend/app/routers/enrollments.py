from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.database import enrollments_collection, courses_collection, users_collection
from app.core.security import get_current_user, require_role
from app.core.tenant import scoped
from app.services.audit import log_action
from app.services.notifications import create_notification

router = APIRouter(prefix="/api", tags=["enrollments"])


def _oid(id_str: str, label: str = "id") -> ObjectId:
    try:
        return ObjectId(id_str)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {label}")


class EnrollRequest(BaseModel):
    student_id: str


class EnrolledStudentOut(BaseModel):
    id: str
    name: str
    email: str
    enrolled_at: datetime


class MyStudentOut(BaseModel):
    id: str
    name: str
    email: str
    course_titles: list[str]


async def _assert_course_manageable(course_id: str, current_user: dict) -> dict:
    course = await courses_collection.find_one(scoped(current_user, {"_id": _oid(course_id, "course id")}))
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    if current_user["role"] == "admin":
        return course
    if current_user["role"] == "teacher" and current_user["user_id"] in course.get("teacher_ids", []):
        return course
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot manage enrollments for this course")


@router.post("/courses/{course_id}/enrollments", response_model=EnrolledStudentOut, status_code=status.HTTP_201_CREATED)
async def enroll_student(course_id: str, payload: EnrollRequest, current_user: dict = Depends(require_role("admin"))):
    course = await courses_collection.find_one(scoped(current_user, {"_id": _oid(course_id, "course id")}))
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    student = await users_collection.find_one(
        scoped(current_user, {"_id": _oid(payload.student_id, "student id"), "role": "student"})
    )
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    existing = await enrollments_collection.find_one(
        scoped(current_user, {"course_id": course_id, "student_id": payload.student_id})
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student is already enrolled")

    now = datetime.now(timezone.utc)
    await enrollments_collection.insert_one({
        "institute_id": current_user["institute_id"],
        "course_id": course_id,
        "student_id": payload.student_id,
        "enrolled_at": now,
    })

    await create_notification(
        user_id=payload.student_id,
        type="enrollment",
        title="You've been enrolled in a course",
        message=f'You now have access to "{course["title"]}"',
        link="/student/courses",
        institute_id=current_user["institute_id"],
    )
    await log_action(
        institute_id=current_user["institute_id"], actor_id=current_user["user_id"],
        action="enrollment.created", entity_type="course", entity_id=course_id,
        details={"student_id": payload.student_id},
    )

    return EnrolledStudentOut(id=str(student["_id"]), name=student["name"], email=student["email"], enrolled_at=now)


@router.delete("/courses/{course_id}/enrollments/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unenroll_student(course_id: str, student_id: str, current_user: dict = Depends(require_role("admin"))):
    result = await enrollments_collection.delete_one(
        scoped(current_user, {"course_id": course_id, "student_id": student_id})
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
    await log_action(
        institute_id=current_user["institute_id"], actor_id=current_user["user_id"],
        action="enrollment.deleted", entity_type="course", entity_id=course_id,
        details={"student_id": student_id},
    )


@router.get("/courses/{course_id}/enrollments", response_model=list[EnrolledStudentOut])
async def list_course_enrollments(course_id: str, current_user: dict = Depends(get_current_user)):
    await _assert_course_manageable(course_id, current_user)
    enrollments = await enrollments_collection.find(scoped(current_user, {"course_id": course_id})).to_list(length=1000)

    out = []
    for e in enrollments:
        student = await users_collection.find_one(scoped(current_user, {"_id": ObjectId(e["student_id"])}))
        if student:
            out.append(EnrolledStudentOut(
                id=str(student["_id"]), name=student["name"], email=student["email"], enrolled_at=e["enrolled_at"],
            ))
    return out


@router.get("/enrollments/my-students", response_model=list[MyStudentOut])
async def list_my_students(current_user: dict = Depends(require_role("teacher"))):
    """All students enrolled across every course this teacher is assigned to."""
    courses = await courses_collection.find(scoped(current_user, {"teacher_ids": current_user["user_id"]})).to_list(length=1000)
    course_ids = [str(c["_id"]) for c in courses]
    title_by_course_id = {str(c["_id"]): c["title"] for c in courses}

    enrollments = await enrollments_collection.find(
        scoped(current_user, {"course_id": {"$in": course_ids}})
    ).to_list(length=5000)

    students_to_courses: dict[str, set] = {}
    for e in enrollments:
        students_to_courses.setdefault(e["student_id"], set()).add(title_by_course_id.get(e["course_id"], "Unknown"))

    out = []
    for student_id, titles in students_to_courses.items():
        student = await users_collection.find_one(scoped(current_user, {"_id": ObjectId(student_id)}))
        if student:
            out.append(MyStudentOut(
                id=str(student["_id"]), name=student["name"], email=student["email"],
                course_titles=sorted(titles),
            ))
    return out
