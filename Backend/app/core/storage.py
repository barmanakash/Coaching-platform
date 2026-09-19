"""
File storage abstraction (PRD section 28).

Kept behind an interface so the backing provider can be swapped later
(e.g. S3, Cloudinary, Azure Blob) without touching the routers that use
it. For local development, LocalDiskStorage writes to Backend/media/
and serves files back via the /media static mount in main.py.
"""

import os
import uuid
from abc import ABC, abstractmethod

from fastapi import UploadFile

MEDIA_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "media")

# Per-type validation (PRD section 27: file validation and size restrictions)
ALLOWED_EXTENSIONS = {
    "pdf": {".pdf"},
    "image": {".jpg", ".jpeg", ".png", ".gif", ".webp"},
    "video": {".mp4", ".mov", ".webm", ".mkv"},
    "document": {".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt"},
}
MAX_FILE_SIZE_BYTES = {
    "pdf": 25 * 1024 * 1024,       # 25 MB
    "image": 10 * 1024 * 1024,     # 10 MB
    "video": 500 * 1024 * 1024,    # 500 MB
    "document": 25 * 1024 * 1024,  # 25 MB
}


class FileTooLargeError(Exception):
    def __init__(self, max_size_bytes: int):
        self.max_size_bytes = max_size_bytes
        super().__init__(f"File exceeds the {max_size_bytes // (1024 * 1024)}MB limit")


class StorageBackend(ABC):
    @abstractmethod
    async def save(self, file: UploadFile, subfolder: str, max_size_bytes: int) -> tuple[str, int]:
        """Persists the file and returns (public_url, size_in_bytes).
        Raises FileTooLargeError if the stream exceeds max_size_bytes,
        without ever buffering more than that much data on disk."""

    @abstractmethod
    def delete(self, url: str) -> None:
        """Best-effort delete given a URL previously returned by save()."""


class LocalDiskStorage(StorageBackend):
    def __init__(self, media_root: str = MEDIA_ROOT):
        self.media_root = media_root
        os.makedirs(self.media_root, exist_ok=True)

    async def save(self, file: UploadFile, subfolder: str, max_size_bytes: int) -> tuple[str, int]:
        folder = os.path.join(self.media_root, subfolder)
        os.makedirs(folder, exist_ok=True)

        ext = os.path.splitext(file.filename or "")[1].lower()
        stored_name = f"{uuid.uuid4().hex}{ext}"
        path = os.path.join(folder, stored_name)

        size = 0
        try:
            with open(path, "wb") as out_file:
                while chunk := await file.read(1024 * 1024):  # 1MB chunks
                    size += len(chunk)
                    if size > max_size_bytes:
                        raise FileTooLargeError(max_size_bytes)
                    out_file.write(chunk)
        except FileTooLargeError:
            if os.path.isfile(path):
                os.remove(path)
            raise

        return f"/media/{subfolder}/{stored_name}", size

    def delete(self, url: str) -> None:
        if not url.startswith("/media/"):
            return
        path = os.path.join(self.media_root, url[len("/media/"):])
        if os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass


_storage_backend: StorageBackend = LocalDiskStorage()


def get_storage() -> StorageBackend:
    return _storage_backend
