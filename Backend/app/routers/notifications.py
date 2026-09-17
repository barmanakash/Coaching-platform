from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.database import notifications_collection
from app.core.security import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationOut(BaseModel):
    id: str
    type: str
    title: str
    message: str
    link: Optional[str] = None
    read: bool
    created_at: datetime


def _serialize(n: dict) -> NotificationOut:
    return NotificationOut(
        id=str(n["_id"]), type=n["type"], title=n["title"], message=n["message"],
        link=n.get("link"), read=n.get("read", False), created_at=n["created_at"],
    )


@router.get("", response_model=list[NotificationOut])
async def list_notifications(current_user: dict = Depends(get_current_user)):
    notifications = await notifications_collection.find(
        {"user_id": current_user["user_id"]}
    ).sort("created_at", -1).to_list(length=100)
    return [_serialize(n) for n in notifications]


@router.get("/unread-count")
async def unread_count(current_user: dict = Depends(get_current_user)):
    count = await notifications_collection.count_documents(
        {"user_id": current_user["user_id"], "read": False}
    )
    return {"count": count}


@router.post("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    result = await notifications_collection.find_one_and_update(
        {"_id": ObjectId(notification_id), "user_id": current_user["user_id"]},
        {"$set": {"read": True}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return _serialize(result)


@router.post("/read-all")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    await notifications_collection.update_many(
        {"user_id": current_user["user_id"], "read": False},
        {"$set": {"read": True}},
    )
    return {"status": "ok"}
