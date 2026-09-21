from typing import Dict, Optional, Set
from fastapi import WebSocket


class ConnectionManager:
    """Tracks active WebSocket connections per user, for chat, presence, and notifications.

    Each user is also mapped to their institute so that presence and any
    other broadcast can be limited to one tenant. There is deliberately no
    platform-wide broadcast: it would leak activity across institutes.
    """

    def __init__(self):
        # user_id -> set of active websocket connections (supports multiple tabs/devices)
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # user_id -> institute_id of that user
        self.user_institute: Dict[str, Optional[str]] = {}

    async def connect(self, user_id: str, websocket: WebSocket, institute_id: Optional[str] = None):
        await websocket.accept()
        self.active_connections.setdefault(user_id, set()).add(websocket)
        self.user_institute[user_id] = institute_id

    def disconnect(self, user_id: str, websocket: WebSocket):
        connections = self.active_connections.get(user_id)
        if connections and websocket in connections:
            connections.remove(websocket)
            if not connections:
                del self.active_connections[user_id]
                self.user_institute.pop(user_id, None)

    def is_online(self, user_id: str) -> bool:
        return user_id in self.active_connections

    def online_user_ids(self, institute_id: Optional[str]) -> list[str]:
        """Online users of ONE institute (never all tenants)."""
        return [uid for uid in self.active_connections if self.user_institute.get(uid) == institute_id]

    async def send_to_user(self, user_id: str, message: dict):
        for connection in self.active_connections.get(user_id, set()):
            await connection.send_json(message)

    async def broadcast_to_institute(self, institute_id: Optional[str], message: dict, exclude_user_id: Optional[str] = None):
        for user_id in self.online_user_ids(institute_id):
            if user_id == exclude_user_id:
                continue
            for connection in self.active_connections.get(user_id, set()):
                await connection.send_json(message)


manager = ConnectionManager()
