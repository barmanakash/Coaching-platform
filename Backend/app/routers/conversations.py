from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.database import conversations_collection, messages_collection, users_collection
from app.core.security import get_current_user
from app.websocket.manager import manager

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def _oid(id_str: str, label: str = "id") -> ObjectId:
    try:
        return ObjectId(id_str)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {label}")


class ContactOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    online: bool


class StartConversationRequest(BaseModel):
    other_user_id: str


class ConversationOut(BaseModel):
    id: str
    other_user_id: str
    other_user_name: str
    other_user_role: str
    online: bool
    last_message_preview: Optional[str] = None
    last_message_at: Optional[datetime] = None


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    sender_name: str
    sender_role: str
    content: str
    created_at: datetime


@router.get("/contacts", response_model=list[ContactOut])
async def list_contacts(current_user: dict = Depends(get_current_user)):
    """Teacher <-> Student chat only, for now (mirrors the doubt system's scope).
    Course-based scoping (only chat with your assigned teacher/enrolled students)
    will tighten this once enrollment is built."""
    role = current_user["role"]
    if role == "student":
        target_role = "teacher"
    elif role == "teacher":
        target_role = "student"
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chat is available to teachers and students")

    users = await users_collection.find({"role": target_role, "status": "active"}).to_list(length=1000)
    return [
        ContactOut(
            id=str(u["_id"]), name=u["name"], email=u["email"], role=u["role"],
            online=manager.is_online(str(u["_id"])),
        )
        for u in users
    ]


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
async def start_conversation(payload: StartConversationRequest, current_user: dict = Depends(get_current_user)):
    me = current_user["user_id"]
    other = payload.other_user_id
    if me == other:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot start a conversation with yourself")

    other_user = await users_collection.find_one({"_id": _oid(other, "user id")})
    if not other_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    conv = await conversations_collection.find_one({
        "participant_ids": {"$all": [me, other]},
        "type": "direct",
    })
    if not conv:
        doc = {
            "participant_ids": [me, other],
            "type": "direct",
            "created_at": datetime.now(timezone.utc),
            "last_message_at": None,
            "last_message_preview": None,
        }
        result = await conversations_collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        conv = doc

    return ConversationOut(
        id=str(conv["_id"]),
        other_user_id=other,
        other_user_name=other_user["name"],
        other_user_role=other_user["role"],
        online=manager.is_online(other),
        last_message_preview=conv.get("last_message_preview"),
        last_message_at=conv.get("last_message_at"),
    )


@router.get("", response_model=list[ConversationOut])
async def list_conversations(current_user: dict = Depends(get_current_user)):
    me = current_user["user_id"]
    convs = await conversations_collection.find({"participant_ids": me}).sort("last_message_at", -1).to_list(length=200)

    out = []
    for c in convs:
        other_id = next((p for p in c["participant_ids"] if p != me), None)
        if not other_id:
            continue
        other_user = await users_collection.find_one({"_id": ObjectId(other_id)})
        if not other_user:
            continue
        out.append(ConversationOut(
            id=str(c["_id"]),
            other_user_id=other_id,
            other_user_name=other_user["name"],
            other_user_role=other_user["role"],
            online=manager.is_online(other_id),
            last_message_preview=c.get("last_message_preview"),
            last_message_at=c.get("last_message_at"),
        ))
    return out


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def get_messages(conversation_id: str, current_user: dict = Depends(get_current_user)):
    conv = await conversations_collection.find_one({"_id": _oid(conversation_id, "conversation id")})
    if not conv or current_user["user_id"] not in conv.get("participant_ids", []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot view this conversation")

    messages = await messages_collection.find({"conversation_id": conversation_id}).sort("created_at", 1).to_list(length=500)
    return [
        MessageOut(
            id=str(m["_id"]), conversation_id=conversation_id, sender_id=m["sender_id"],
            sender_name=m["sender_name"], sender_role=m["sender_role"],
            content=m["content"], created_at=m["created_at"],
        )
        for m in messages
    ]
