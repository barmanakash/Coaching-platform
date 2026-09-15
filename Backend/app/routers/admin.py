from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.database import users_collection, courses_collection, classes_collection, doubts_collection
from app.core.security import require_role

router = APIRouter(prefix="/api/admin", tags=["admin"])


class AdminDashboardStats(BaseModel):
    total_students: int
    total_teachers: int
    total_courses: int
    active_classes: int
    upcoming_classes: int
    pending_doubts: int


@router.get("/dashboard", response_model=AdminDashboardStats)
async def get_dashboard_stats(current_user: dict = Depends(require_role("admin"))):
    total_students = await users_collection.count_documents({"role": "student"})
    total_teachers = await users_collection.count_documents({"role": "teacher"})
    total_courses = await courses_collection.count_documents({})
    # Classes/doubts collections are populated once Phase 4/6 (Classes, Doubts) are built.
    active_classes = await classes_collection.count_documents({"status": "live"})
    upcoming_classes = await classes_collection.count_documents({"status": "scheduled"})
    pending_doubts = await doubts_collection.count_documents({"status": {"$in": ["OPEN", "IN_PROGRESS"]}})

    return AdminDashboardStats(
        total_students=total_students,
        total_teachers=total_teachers,
        total_courses=total_courses,
        active_classes=active_classes,
        upcoming_classes=upcoming_classes,
        pending_doubts=pending_doubts,
    )
