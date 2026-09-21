from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.security import authenticate_token
from app.websocket.manager import manager

router = APIRouter()


@router.websocket("/ws/presence")
async def presence_websocket(websocket: WebSocket, token: str = Query(...)):
    try:
        user = await authenticate_token(token)
    except Exception:
        await websocket.close(code=4401)
        return

    user_id = user["user_id"]
    institute_id = user["institute_id"]
    if not institute_id:  # platform admins have no institute to be "present" in
        await websocket.close(code=4403)
        return

    await manager.connect(user_id, websocket, institute_id)

    # Send the new connection a snapshot of who's already online IN ITS OWN
    # INSTITUTE, since it only just started listening for presence deltas.
    await websocket.send_json({
        "type": "online_users",
        "user_ids": manager.online_user_ids(institute_id),
    })
    await manager.broadcast_to_institute(
        institute_id, {"type": "presence", "user_id": user_id, "online": True}, exclude_user_id=user_id,
    )

    try:
        while True:
            await websocket.receive_text()  # keep-alive; content is ignored
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
        if not manager.is_online(user_id):
            await manager.broadcast_to_institute(
                institute_id, {"type": "presence", "user_id": user_id, "online": False},
            )
