from datetime import datetime, timezone
from typing import Optional, Literal

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.database import doubts_collection, courses_collection, users_collection, enrollments_collection
from app.core.security import get_current_user
from app.core.tenant import scoped
from app.services.notifications import create_notification

router = APIRouter(prefix="/api/doubts", tags=["doubts"])


def _oid(id_str: str, label: str = "id") -> ObjectId:
    try:
        return ObjectId(id_str)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {label}")


# ---------- Schemas ----------

class DoubtCreateRequest(BaseModel):
    subject: str = Field(min_length=2, max_length=150)
    question: str = Field(min_length=2, max_length=3000)
    course_id: Optional[str] = None
    attachment_url: Optional[str] = None


class ReplyCreateRequest(BaseModel):
    message: str = Field(min_length=1, max_length=3000)


class ReplyOut(BaseModel):
    author_id: str
    author_name: str
    author_role: str
    message: str
    created_at: datetime


class DoubtOut(BaseModel):
    id: str
    student_id: str
    student_name: str
    course_id: Optional[str] = None
    course_title: Optional[str] = None
    subject: str
    question: str
    attachment_url: Optional[str] = None
    status: Literal["OPEN", "IN_PROGRESS", "RESOLVED"]
    replies: list[ReplyOut] = []
    created_at: datetime
    updated_at: datetime


class DoubtStatusUpdateRequest(BaseModel):
    status: Literal["OPEN", "IN_PROGRESS", "RESOLVED"]


# ---------- Helpers ----------

async def _serialize_doubt(d: dict) -> DoubtOut:
    student = await users_collection.find_one({"_id": ObjectId(d["student_id"])})
    course_title = None
    if d.get("course_id"):
        course = await courses_collection.find_one({"_id": ObjectId(d["course_id"])})
        course_title = course["title"] if course else None

    return DoubtOut(
        id=str(d["_id"]),
        student_id=d["student_id"],
        student_name=student["name"] if student else "Unknown",
        course_id=d.get("course_id"),
        course_title=course_title,
        subject=d["subject"],
        question=d["question"],
        attachment_url=d.get("attachment_url"),
        status=d.get("status", "OPEN"),
        replies=[ReplyOut(**r) for r in d.get("replies", [])],
        created_at=d["created_at"],
        updated_at=d.get("updated_at", d["created_at"]),
    )


async def _get_doubt_or_404(doubt_id: str, current_user: dict) -> dict:
    doubt = await doubts_collection.find_one(scoped(current_user, {"_id": _oid(doubt_id, "doubt id")}))
    if not doubt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doubt not found")
    return doubt


async def _assert_can_view_or_reply(doubt: dict, current_user: dict):
    role = current_user["role"]
    if role == "admin":
        return
    if role == "student" and current_user["user_id"] == doubt["student_id"]:
        return
    if role == "teacher" and doubt.get("course_id"):
        course = await courses_collection.find_one(scoped(current_user, {"_id": ObjectId(doubt["course_id"])}))
        if course and current_user["user_id"] in course.get("teacher_ids", []):
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot access this doubt")


# ---------- Endpoints ----------

@router.post("", response_model=DoubtOut, status_code=status.HTTP_201_CREATED)
async def create_doubt(payload: DoubtCreateRequest, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can raise doubts")

    if payload.course_id:
        course = await courses_collection.find_one(scoped(current_user, {"_id": _oid(payload.course_id, "course id")}))
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        enrollment = await enrollments_collection.find_one(
            scoped(current_user, {"course_id": payload.course_id, "student_id": current_user["user_id"]})
        )
        if not enrollment:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not enrolled in this course")

    now = datetime.now(timezone.utc)
    doc = {
        "institute_id": current_user["institute_id"],
        "student_id": current_user["user_id"],
        "course_id": payload.course_id,
        "subject": payload.subject,
        "question": payload.question,
        "attachment_url": payload.attachment_url,
        "status": "OPEN",
        "replies": [],
        "created_at": now,
        "updated_at": now,
    }
    result = await doubts_collection.insert_one(doc)
    doc["_id"] = result.inserted_id

    if payload.course_id:
        student = await users_collection.find_one({"_id": ObjectId(current_user["user_id"])})
        for teacher_id in course.get("teacher_ids", []):
            await create_notification(
                user_id=teacher_id,
                type="doubt_new",
                title="New doubt raised",
                message=f"{student['name'] if student else 'A student'} asked: {payload.subject}",
                link="/teacher/doubts",
                institute_id=current_user["institute_id"],
            )

    return await _serialize_doubt(doc)


@router.get("", response_model=list[DoubtOut])
async def list_doubts(current_user: dict = Depends(get_current_user)):
    """
    - Student: sees only their own doubts.
    - Teacher: sees doubts raised on courses they're assigned to teach.
    - Admin: sees every doubt in their institute.
    """
    role = current_user["role"]
    if role == "admin":
        query = scoped(current_user)
    elif role == "student":
        query = scoped(current_user, {"student_id": current_user["user_id"]})
    else:  # teacher
        courses = await courses_collection.find(
            scoped(current_user, {"teacher_ids": current_user["user_id"]})
        ).to_list(length=1000)
        course_ids = [str(c["_id"]) for c in courses]
        query = scoped(current_user, {"course_id": {"$in": course_ids}})

    doubts = await doubts_collection.find(query).sort("updated_at", -1).to_list(length=1000)
    return [await _serialize_doubt(d) for d in doubts]


@router.get("/{doubt_id}", response_model=DoubtOut)
async def get_doubt(doubt_id: str, current_user: dict = Depends(get_current_user)):
    doubt = await _get_doubt_or_404(doubt_id, current_user)
    await _assert_can_view_or_reply(doubt, current_user)
    return await _serialize_doubt(doubt)


@router.post("/{doubt_id}/replies", response_model=DoubtOut)
async def add_reply(doubt_id: str, payload: ReplyCreateRequest, current_user: dict = Depends(get_current_user)):
    doubt = await _get_doubt_or_404(doubt_id, current_user)
    await _assert_can_view_or_reply(doubt, current_user)

    user = await users_collection.find_one({"_id": ObjectId(current_user["user_id"])})
    reply = {
        "author_id": current_user["user_id"],
        "author_name": user["name"] if user else "Unknown",
        "author_role": current_user["role"],
        "message": payload.message,
        "created_at": datetime.now(timezone.utc),
    }

    update = {
        "$push": {"replies": reply},
        "$set": {"updated_at": datetime.now(timezone.utc)},
    }
    # A teacher's first reply moves the doubt from OPEN to IN_PROGRESS automatically.
    if current_user["role"] in ("teacher", "admin") and doubt.get("status") == "OPEN":
        update["$set"]["status"] = "IN_PROGRESS"

    result = await doubts_collection.find_one_and_update(
        {"_id": doubt["_id"]}, update, return_document=True,
    )

    # Notify whichever side didn't just reply.
    if current_user["role"] in ("teacher", "admin"):
        await create_notification(
            user_id=doubt["student_id"],
            type="doubt_reply",
            title="Your doubt got a reply",
            message=f"{reply['author_name']} replied to \"{doubt['subject']}\"",
            link="/student/doubts",
            institute_id=current_user["institute_id"],
        )
    elif current_user["role"] == "student" and doubt.get("course_id"):
        course = await courses_collection.find_one(scoped(current_user, {"_id": ObjectId(doubt["course_id"])}))
        if course:
            for teacher_id in course.get("teacher_ids", []):
                await create_notification(
                    user_id=teacher_id,
                    type="doubt_reply",
                    title="New follow-up on a doubt",
                    message=f"{reply['author_name']} followed up on \"{doubt['subject']}\"",
                    link="/teacher/doubts",
                    institute_id=current_user["institute_id"],
                )

    return await _serialize_doubt(result)


@router.patch("/{doubt_id}/status", response_model=DoubtOut)
async def update_doubt_status(doubt_id: str, payload: DoubtStatusUpdateRequest, current_user: dict = Depends(get_current_user)):
    doubt = await _get_doubt_or_404(doubt_id, current_user)
    await _assert_can_view_or_reply(doubt, current_user)

    result = await doubts_collection.find_one_and_update(
        {"_id": doubt["_id"]},
        {"$set": {"status": payload.status, "updated_at": datetime.now(timezone.utc)}},
        return_document=True,
    )
    return await _serialize_doubt(result)
