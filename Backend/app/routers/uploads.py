import os
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel

from app.core.security import get_current_user
from app.core.storage import get_storage, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES, FileTooLargeError
from app.core.logging_config import logger

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

    max_size = MAX_FILE_SIZE_BYTES[resource_type]
    storage = get_storage()

    try:
        # max_size is enforced WHILE streaming to disk, not after the full
        # upload completes, so an oversized/malicious upload can't fill
        # disk space before being rejected.
        # Files live under a per-institute folder so tenants' uploads stay separated on disk
        # (and can later be access-controlled or quota'd per institute).
        subfolder = f"{current_user['institute_id']}/{resource_type}"
        url, size = await storage.save(file, subfolder=subfolder, max_size_bytes=max_size)
    except FileTooLargeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large: exceeds the {max_size // (1024 * 1024)}MB limit for {resource_type}",
        )

    logger.info(f"File uploaded by user {current_user['user_id']}: {resource_type}, {size} bytes")
    return UploadResponse(url=url, filename=file.filename, size=size, resource_type=resource_type)
