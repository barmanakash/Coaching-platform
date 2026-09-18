from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from bson import ObjectId

from app.core.security import decode_access_token
from app.core.database import classes_collection, enrollments_collection, users_collection

router = APIRouter()


class MeetingRoomManager:
    """Tracks who's in each live-class meeting room, for WebRTC signaling
    relay. This is a mesh-call signaling server only — it never touches
    audio/video itself, just forwards offers/answers/ICE candidates."""

    def __init__(self):
        self.rooms: dict[str, dict[str, WebSocket]] = {}

    async def join(self, meeting_id: str, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.rooms.setdefault(meeting_id, {})[user_id] = websocket

    def leave(self, meeting_id: str, user_id: str):
        room = self.rooms.get(meeting_id)
        if room and user_id in room:
            del room[user_id]
            if not room:
                del self.rooms[meeting_id]

    def participant_ids(self, meeting_id: str) -> list[str]:
        return list(self.rooms.get(meeting_id, {}).keys())

    async def send_to(self, meeting_id: str, user_id: str, message: dict):
        ws = self.rooms.get(meeting_id, {}).get(user_id)
        if ws:
            await ws.send_json(message)

    async def broadcast(self, meeting_id: str, message: dict, exclude_user_id: Optional[str] = None):
        for uid, ws in self.rooms.get(meeting_id, {}).items():
            if uid != exclude_user_id:
                await ws.send_json(message)


meeting_manager = MeetingRoomManager()


@router.websocket("/ws/meeting/{meeting_id}")
async def meeting_websocket(websocket: WebSocket, meeting_id: str, token: str = Query(...)):
    try:
        payload = decode_access_token(token)
    except Exception:
        await websocket.close(code=4401)
        return

    user_id = payload.get("sub")
    role = payload.get("role")
    if not user_id:
        await websocket.close(code=4401)
        return

    if not ObjectId.is_valid(meeting_id):
        await websocket.close(code=4400)
        return
    cls = await classes_collection.find_one({"_id": ObjectId(meeting_id)})
    if not cls:
        await websocket.close(code=4404)
        return

    allowed = False
    if role == "admin":
        allowed = True
    elif role == "teacher" and cls["teacher_id"] == user_id:
        allowed = True
    elif role == "student":
        enrollment = await enrollments_collection.find_one(
            {"course_id": cls["course_id"], "student_id": user_id}
        )
        allowed = enrollment is not None

    if not allowed or cls.get("status") != "live":
        await websocket.close(code=4403)
        return

    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    name = user["name"] if user else "Unknown"

    # The new joiner learns who's already here, and will initiate an
    # offer to each of them (avoids both sides racing to offer at once).
    existing_participants = meeting_manager.participant_ids(meeting_id)
    await meeting_manager.join(meeting_id, user_id, websocket)
    await websocket.send_json({"type": "existing-peers", "peers": existing_participants})

    await meeting_manager.broadcast(meeting_id, {
        "type": "peer-joined", "user_id": user_id, "name": name, "role": role,
    }, exclude_user_id=user_id)

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "signal":
                target = data.get("to")
                if target:
                    await meeting_manager.send_to(meeting_id, target, {
                        "type": "signal", "from": user_id, "name": name, "signal": data.get("signal"),
                    })
    except WebSocketDisconnect:
        meeting_manager.leave(meeting_id, user_id)
        await meeting_manager.broadcast(meeting_id, {"type": "peer-left", "user_id": user_id})
