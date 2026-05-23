from __future__ import annotations
import asyncio
import json
import logging
from typing import Dict
from fastapi import WebSocket

log = logging.getLogger("ws")


class WSManager:
    def __init__(self) -> None:
        self.active: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, session_id: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self.active[session_id] = ws
        log.info("ws connected: %s", session_id)

    async def disconnect(self, session_id: str) -> None:
        async with self._lock:
            self.active.pop(session_id, None)

    async def send(self, session_id: str, event: str, data: dict) -> None:
        ws = self.active.get(session_id)
        if not ws:
            return
        try:
            await ws.send_text(json.dumps({"event": event, "data": data}))
        except Exception as e:  # noqa: BLE001
            log.warning("ws send failed for %s: %s", session_id, e)


ws_manager = WSManager()
