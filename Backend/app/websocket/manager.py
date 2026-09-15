from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    """Tracks active WebSocket connections per user, for chat, presence, and notifications."""

    def __init__(self):
        # user_id -> set of active websocket connections (supports multiple tabs/devices)
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        connections = self.active_connections.get(user_id)
        if connections and websocket in connections:
            connections.remove(websocket)
            if not connections:
                del self.active_connections[user_id]

    def is_online(self, user_id: str) -> bool:
        return user_id in self.active_connections

    async def send_to_user(self, user_id: str, message: dict):
        for connection in self.active_connections.get(user_id, set()):
            await connection.send_json(message)

    async def broadcast(self, message: dict, exclude_user_id: str = None):
        for user_id, connections in self.active_connections.items():
            if user_id == exclude_user_id:
                continue
            for connection in connections:
                await connection.send_json(message)


manager = ConnectionManager()
