from datetime import datetime, timezone
from typing import Optional, Literal

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.core.database import courses_collection, modules_collection, resources_collection, enrollments_collection
from app.core.security import get_current_user
from app.core.tenant import scoped
from app.core.validators import validate_safe_url as _validate_resource_url

router = APIRouter(tags=["modules & resources"])


# ---------- Helpers ----------

def _oid(id_str: str, label: str = "id") -> ObjectId:
    try:
        return ObjectId(id_str)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {label}")


async def _get_course_or_404(course_id: str, current_user: dict) -> dict:
    course = await courses_collection.find_one(scoped(current_user, {"_id": _oid(course_id, "course id")}))
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


async def _get_module_or_404(module_id: str, current_user: dict) -> dict:
    module = await modules_collection.find_one(scoped(current_user, {"_id": _oid(module_id, "module id")}))
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return module


async def _assert_can_edit_course(course: dict, current_user: dict):
    """Admin can edit any course; a teacher can only edit courses they're assigned to."""
    if current_user["role"] == "admin":
        return
    if current_user["role"] == "teacher" and current_user["user_id"] in course.get("teacher_ids", []):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot manage this course")


async def _assert_can_view_course(course: dict, current_user: dict):
    """Admin: always. Teacher: if assigned. Student: only if actually enrolled
    and the course is published (mirrors the course catalog's visibility rule)."""
    role = current_user["role"]
    if role == "admin":
        return
    if role == "teacher" and current_user["user_id"] in course.get("teacher_ids", []):
        return
    if role == "student" and course.get("status") == "published":
        enrollment = await enrollments_collection.find_one(
            scoped(current_user, {"course_id": str(course["_id"]), "student_id": current_user["user_id"]})
        )
        if enrollment:
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot view this course")


# ---------- Schemas ----------

class ModuleCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: str = ""
    order: int = 0


class ModuleUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None


class ModuleOut(BaseModel):
    id: str
    course_id: str
    title: str
    description: str
    order: int
    resource_count: int = 0
    created_at: Optional[datetime] = None


class ResourceCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: str = ""
    type: Literal["pdf", "image", "video", "document", "link", "assignment"]
    url: str = Field(min_length=1, description="External http(s) link, or an uploaded /media/ file URL")

    _validate_url = field_validator("url")(_validate_resource_url)


class ResourceUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[Literal["pdf", "image", "video", "document", "link", "assignment"]] = None
    url: Optional[str] = None

    _validate_url = field_validator("url")(lambda cls, v: _validate_resource_url(v) if v is not None else v)


class ResourceOut(BaseModel):
    id: str
    module_id: str
    course_id: str
    title: str
    description: str
    type: str
    url: str
    created_by: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


def _serialize_module(m: dict, resource_count: int = 0) -> ModuleOut:
    return ModuleOut(
        id=str(m["_id"]),
        course_id=m["course_id"],
        title=m["title"],
        description=m.get("description", ""),
        order=m.get("order", 0),
        resource_count=resource_count,
        created_at=m.get("created_at"),
    )


def _serialize_resource(r: dict) -> ResourceOut:
    return ResourceOut(
        id=str(r["_id"]),
        module_id=r["module_id"],
        course_id=r["course_id"],
        title=r["title"],
        description=r.get("description", ""),
        type=r["type"],
        url=r["url"],
        created_by=r.get("created_by", ""),
        created_at=r.get("created_at"),
        updated_at=r.get("updated_at"),
    )


# ---------- Module endpoints ----------

@router.get("/api/courses/{course_id}/modules", response_model=list[ModuleOut])
async def list_modules(course_id: str, current_user: dict = Depends(get_current_user)):
    course = await _get_course_or_404(course_id, current_user)
    await _assert_can_view_course(course, current_user)

    modules = await modules_collection.find(
        scoped(current_user, {"course_id": course_id})
    ).sort("order", 1).to_list(length=500)
    out = []
    for m in modules:
        count = await resources_collection.count_documents(scoped(current_user, {"module_id": str(m["_id"])}))
        out.append(_serialize_module(m, count))
    return out


@router.post("/api/courses/{course_id}/modules", response_model=ModuleOut, status_code=status.HTTP_201_CREATED)
async def create_module(
    course_id: str,
    payload: ModuleCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    course = await _get_course_or_404(course_id, current_user)
    await _assert_can_edit_course(course, current_user)

    doc = {
        "institute_id": current_user["institute_id"],
        "course_id": course_id,
        "title": payload.title,
        "description": payload.description,
        "order": payload.order,
        "created_by": current_user["user_id"],
        "created_at": datetime.now(timezone.utc),
    }
    result = await modules_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize_module(doc)


@router.patch("/api/modules/{module_id}", response_model=ModuleOut)
async def update_module(
    module_id: str,
    payload: ModuleUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    module = await _get_module_or_404(module_id, current_user)
    course = await _get_course_or_404(module["course_id"], current_user)
    await _assert_can_edit_course(course, current_user)

    update_fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    result = await modules_collection.find_one_and_update(
        {"_id": module["_id"]}, {"$set": update_fields}, return_document=True,
    )
    count = await resources_collection.count_documents(scoped(current_user, {"module_id": module_id}))
    return _serialize_module(result, count)


@router.delete("/api/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(module_id: str, current_user: dict = Depends(get_current_user)):
    module = await _get_module_or_404(module_id, current_user)
    course = await _get_course_or_404(module["course_id"], current_user)
    await _assert_can_edit_course(course, current_user)

    await resources_collection.delete_many(scoped(current_user, {"module_id": module_id}))
    await modules_collection.delete_one({"_id": module["_id"]})


# ---------- Resource endpoints ----------

@router.get("/api/modules/{module_id}/resources", response_model=list[ResourceOut])
async def list_resources(module_id: str, current_user: dict = Depends(get_current_user)):
    module = await _get_module_or_404(module_id, current_user)
    course = await _get_course_or_404(module["course_id"], current_user)
    await _assert_can_view_course(course, current_user)

    resources = await resources_collection.find(
        scoped(current_user, {"module_id": module_id})
    ).sort("created_at", 1).to_list(length=500)
    return [_serialize_resource(r) for r in resources]


@router.post("/api/modules/{module_id}/resources", response_model=ResourceOut, status_code=status.HTTP_201_CREATED)
async def create_resource(
    module_id: str,
    payload: ResourceCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    module = await _get_module_or_404(module_id, current_user)
    course = await _get_course_or_404(module["course_id"], current_user)
    await _assert_can_edit_course(course, current_user)

    doc = {
        "institute_id": current_user["institute_id"],
        "module_id": module_id,
        "course_id": module["course_id"],
        "title": payload.title,
        "description": payload.description,
        "type": payload.type,
        "url": payload.url,
        "created_by": current_user["user_id"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    result = await resources_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize_resource(doc)


@router.patch("/api/resources/{resource_id}", response_model=ResourceOut)
async def update_resource(
    resource_id: str,
    payload: ResourceUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    resource = await resources_collection.find_one(scoped(current_user, {"_id": _oid(resource_id, "resource id")}))
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    course = await _get_course_or_404(resource["course_id"], current_user)
    await _assert_can_edit_course(course, current_user)

    update_fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    update_fields["updated_at"] = datetime.now(timezone.utc)

    result = await resources_collection.find_one_and_update(
        {"_id": resource["_id"]}, {"$set": update_fields}, return_document=True,
    )
    return _serialize_resource(result)


@router.delete("/api/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(resource_id: str, current_user: dict = Depends(get_current_user)):
    resource = await resources_collection.find_one(scoped(current_user, {"_id": _oid(resource_id, "resource id")}))
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    course = await _get_course_or_404(resource["course_id"], current_user)
    await _assert_can_edit_course(course, current_user)

    await resources_collection.delete_one({"_id": resource["_id"]})
