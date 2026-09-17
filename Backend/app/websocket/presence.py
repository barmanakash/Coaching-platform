from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.security import decode_access_token
from app.websocket.manager import manager

router = APIRouter()


@router.websocket("/ws/presence")
async def presence_websocket(websocket: WebSocket, token: str = Query(...)):
    try:
        payload = decode_access_token(token)
    except Exception:
        await websocket.close(code=4401)
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4401)
        return

    await manager.connect(user_id, websocket)

    # Send the new connection a full snapshot of who's already online,
    # since it only just started listening for presence deltas.
    await websocket.send_json({
        "type": "online_users",
        "user_ids": list(manager.active_connections.keys()),
    })
    await manager.broadcast({"type": "presence", "user_id": user_id, "online": True}, exclude_user_id=user_id)

    try:
        while True:
            await websocket.receive_text()  # keep-alive; content is ignored
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
        if not manager.is_online(user_id):
            await manager.broadcast({"type": "presence", "user_id": user_id, "online": False})
