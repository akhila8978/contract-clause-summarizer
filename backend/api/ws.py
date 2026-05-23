from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.ws_manager import ws_manager

router = APIRouter()


@router.websocket("/ws/progress/{session_id}")
async def progress(ws: WebSocket, session_id: str):
    await ws_manager.connect(session_id, ws)
    try:
        while True:
            # we just keep the socket open; clients ignore inbound msgs
            await ws.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(session_id)
    except Exception:
        await ws_manager.disconnect(session_id)
