from __future__ import annotations

from fastapi import WebSocket, WebSocketDisconnect


class WSHandler:
    """Simple WS handler for command dispatch — used by app.py internally."""

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    async def handle(self, websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_json()
                cmd = data.get("command") if isinstance(data, dict) else None
                if cmd == "startListening":
                    await self.orchestrator.on_wake(data.get("word", "manual"))
                await websocket.send_json({"type": "state", "state": self.orchestrator.state})
        except WebSocketDisconnect:
            pass
