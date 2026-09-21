from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from bson import ObjectId

from app.core.security import authenticate_token
from app.core.database import messages_collection, conversations_collection, users_collection
from app.websocket.manager import manager
from app.services.notifications import create_notification

router = APIRouter()


@router.websocket("/ws/chat/{conversation_id}")
async def chat_websocket(websocket: WebSocket, conversation_id: str, token: str = Query(...)):
    try:
        user = await authenticate_token(token)
    except Exception:
        await websocket.close(code=4401)
        return

    user_id = user["user_id"]
    role = user["role"]
    institute_id = user["institute_id"]
    if not institute_id:
        await websocket.close(code=4403)
        return

    try:
        # Scoped to the caller's institute: a conversation id from another
        # tenant is indistinguishable from one that doesn't exist.
        conversation = await conversations_collection.find_one(
            {"_id": ObjectId(conversation_id), "institute_id": institute_id}
        )
    except Exception:
        await websocket.close(code=4400)
        return

    if not conversation or user_id not in conversation.get("participant_ids", []):
        await websocket.close(code=4403)
        return

    await manager.connect(user_id, websocket, institute_id)
    try:
        while True:
            data = await websocket.receive_json()
            content = (data.get("content") or "").strip()
            if not content:
                continue

            sender = await users_collection.find_one({"_id": ObjectId(user_id)})
            now = datetime.now(timezone.utc)
            message = {
                "institute_id": institute_id,
                "conversation_id": conversation_id,
                "sender_id": user_id,
                "sender_name": sender["name"] if sender else "Unknown",
                "sender_role": role,
                "content": content,
                "created_at": now,
            }
            result = await messages_collection.insert_one(message)

            await conversations_collection.update_one(
                {"_id": ObjectId(conversation_id), "institute_id": institute_id},
                {"$set": {"last_message_at": now, "last_message_preview": content[:120]}},
            )

            out = {
                "type": "message",
                "id": str(result.inserted_id),
                "conversation_id": conversation_id,
                "sender_id": user_id,
                "sender_name": message["sender_name"],
                "sender_role": role,
                "content": content,
                "created_at": now.isoformat(),
            }
            for participant_id in conversation["participant_ids"]:
                await manager.send_to_user(participant_id, out)

            recipient_id = next((p for p in conversation["participant_ids"] if p != user_id), None)
            if recipient_id:
                recipient = await users_collection.find_one({"_id": ObjectId(recipient_id)})
                if recipient:
                    await create_notification(
                        user_id=recipient_id,
                        type="message",
                        title=f"New message from {message['sender_name']}",
                        message=content[:120],
                        link=f"/{recipient['role']}/chat",
                        institute_id=institute_id,
                    )
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
