import os
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel

from app.core.security import get_current_user
from app.core.storage import get_storage, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


class UploadResponse(BaseModel):
    url: str
    filename: str
    size: int
    resource_type: str


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    resource_type: Literal["pdf", "image", "video", "document"] = Form(...),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] not in ("teacher", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can upload course files")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS[resource_type]:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS[resource_type]))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{ext}' is not allowed for {resource_type}. Allowed: {allowed}",
        )

    storage = get_storage()
    url, size = await storage.save(file, subfolder=resource_type)

    max_size = MAX_FILE_SIZE_BYTES[resource_type]
    if size > max_size:
        storage.delete(url)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large: {size // (1024*1024)}MB exceeds the {max_size // (1024*1024)}MB limit for {resource_type}",
        )

    return UploadResponse(url=url, filename=file.filename, size=size, resource_type=resource_type)
