from datetime import datetime, timezone
from typing import Optional

from app.core.database import notifications_collection
from app.websocket.manager import manager


async def create_notification(user_id: str, type: str, title: str, message: str, link: Optional[str] = None) -> dict:
    """Persists a notification and pushes it live if the user has any
    socket open (chat and/or presence both register under the same
    user_id, so this reaches whichever is connected)."""
    doc = {
        "user_id": user_id,
        "type": type,
        "title": title,
        "message": message,
        "link": link,
        "read": False,
        "created_at": datetime.now(timezone.utc),
    }
    result = await notifications_collection.insert_one(doc)
    doc["_id"] = result.inserted_id

    await manager.send_to_user(user_id, {
        "type": "notification",
        "id": str(doc["_id"]),
        "notification_type": type,
        "title": title,
        "message": message,
        "link": link,
        "created_at": doc["created_at"].isoformat(),
    })
    return doc
