from __future__ import annotations

from fastapi import WebSocket


class WSManager:
    def __init__(self) -> None:
        self.connections: dict[int, set[WebSocket]] = {}

    async def connect(self, table_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self.connections.setdefault(table_id, set()).add(ws)

    def disconnect(self, table_id: int, ws: WebSocket) -> None:
        bucket = self.connections.get(table_id)
        if not bucket:
            return
        bucket.discard(ws)

    async def broadcast(self, table_id: int, payload: dict) -> None:
        for ws in list(self.connections.get(table_id, set())):
            await ws.send_json(payload)


ws_manager = WSManager()
