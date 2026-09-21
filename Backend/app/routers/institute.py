"""
Institute profile and academic configuration (PRD section 6).

There is deliberately no institute id in any URL: every user can only ever
see/modify the institute recorded on their own account, so there is no
id to tamper with.
"""

from datetime import datetime
from typing import Literal, Optional, Union

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.database import institutes_collection
from app.core.security import get_current_user, require_role
from app.core.validators import validate_safe_url
from app.services.audit import log_action

router = APIRouter(prefix="/api/institute", tags=["institute"])

MAX_LIST_ITEMS = 100
MAX_ITEM_LENGTH = 80


def _clean_list(values: list[str]) -> list[str]:
    """Trims, drops blanks, and removes case-insensitive duplicates (keeps first spelling / order)."""
    seen: set[str] = set()
    cleaned: list[str] = []
    for value in values:
        value = value.strip()
        if not value:
            continue
        if len(value) > MAX_ITEM_LENGTH:
            raise ValueError(f"Each entry must be at most {MAX_ITEM_LENGTH} characters")
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(value)
    if len(cleaned) > MAX_LIST_ITEMS:
        raise ValueError(f"At most {MAX_LIST_ITEMS} entries are allowed")
    return cleaned


class GradeBand(BaseModel):
    grade: str = Field(min_length=1, max_length=10)
    min_percent: float = Field(ge=0, le=100)


class AcademicConfig(BaseModel):
    academic_year: str = Field(default="", max_length=20)
    subjects: list[str] = []
    classes: list[str] = []
    departments: list[str] = []
    grading: list[GradeBand] = []

    @field_validator("subjects", "classes", "departments")
    @classmethod
    def _clean(cls, values: list[str]) -> list[str]:
        return _clean_list(values)

    @field_validator("grading")
    @classmethod
    def _validate_grading(cls, bands: list[GradeBand]) -> list[GradeBand]:
        if not bands:
            return bands
        grades = [b.grade.strip().lower() for b in bands]
        if len(set(grades)) != len(grades):
            raise ValueError("Each grade may only appear once")
        if not any(b.min_percent == 0 for b in bands):
            raise ValueError("The grading scale must include a band starting at 0%, so every score gets a grade")
        return sorted(bands, key=lambda b: b.min_percent, reverse=True)


class InstituteOut(BaseModel):
    id: str
    name: str
    code: str
    logo_url: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    description: str = ""
    academic: AcademicConfig = AcademicConfig()
    status: str = "active"
    created_at: Optional[datetime] = None


class InstituteUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    logo_url: Optional[str] = Field(default=None, max_length=500)
    address: Optional[str] = Field(default=None, max_length=300)
    phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[Union[EmailStr, Literal[""]]] = None
    website: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    academic: Optional[AcademicConfig] = None

    @field_validator("logo_url")
    @classmethod
    def _validate_logo(cls, value: Optional[str]) -> Optional[str]:
        if value:  # "" clears the logo
            validate_safe_url(value)
        return value

    @field_validator("website")
    @classmethod
    def _validate_website(cls, value: Optional[str]) -> Optional[str]:
        if value and not value.startswith(("http://", "https://")):
            raise ValueError("Website must start with http:// or https://")
        return value


def _serialize(institute: dict) -> InstituteOut:
    return InstituteOut(
        id=str(institute["_id"]),
        name=institute["name"],
        code=institute["code"],
        logo_url=institute.get("logo_url", ""),
        address=institute.get("address", ""),
        phone=institute.get("phone", ""),
        email=institute.get("email", ""),
        website=institute.get("website", ""),
        description=institute.get("description", ""),
        academic=AcademicConfig(**institute.get("academic", {})),
        status=institute.get("status", "active"),
        created_at=institute.get("created_at"),
    )


@router.get("", response_model=InstituteOut)
async def get_my_institute(current_user: dict = Depends(get_current_user)):
    """Any signed-in member can read their institute's profile (name, logo, academic setup)."""
    institute = await institutes_collection.find_one({"_id": ObjectId(current_user["institute_id"])})
    if not institute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institute not found")
    return _serialize(institute)


@router.patch("", response_model=InstituteOut)
async def update_my_institute(
    payload: InstituteUpdateRequest,
    current_user: dict = Depends(require_role("admin")),
):
    update_fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    result = await institutes_collection.find_one_and_update(
        {"_id": ObjectId(current_user["institute_id"])},
        {"$set": update_fields},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institute not found")

    await log_action(
        institute_id=current_user["institute_id"], actor_id=current_user["user_id"],
        action="institute.updated", entity_type="institute", entity_id=current_user["institute_id"],
        details={"fields": sorted(update_fields.keys())},
    )
    return _serialize(result)
