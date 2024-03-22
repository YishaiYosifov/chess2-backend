from fastapi import WebSocket, APIRouter

from app import deps

router = APIRouter()


@router.websocket("/ws")
async def connect_websocket(
    websocket: WebSocket,
    user: deps.WSUnauthedUserDep,
    ws_server: deps.WSServerDep,
):
    await ws_server.connect_websocket(websocket, user.user_id)
