from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from anime_assistant.core.orchestrator import Orchestrator
from anime_assistant.core.config import Config


def create_app(config: Config | None = None) -> FastAPI:
    if config is None:
        config = Config()
    app = FastAPI()
    orchestrator = Orchestrator(config=config, memory=None)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/config")
    def get_config():
        return {"llm": {"model": config.llm.model}, "avatar": {"mode": config.avatar.mode}}

    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket):
        await websocket.accept()
        # Bind emit to websocket (best-effort)
        original_emit = orchestrator.emit

        def _emit(event: dict):
            try:
                import asyncio

                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(websocket.send_json(event))
                else:
                    pass
            except Exception:
                pass

        orchestrator.emit = _emit  # type: ignore[assignment]
        try:
            while True:
                try:
                    data = await websocket.receive_json()
                except WebSocketDisconnect:
                    break
                except Exception:
                    break
                command = data.get("command") if isinstance(data, dict) else None
                if command == "startListening":
                    await orchestrator.on_wake(data.get("word", "manual"))
                    await websocket.send_json({"type": "state", "state": orchestrator.state})
                elif command == "stopListening":
                    await orchestrator.handle_timeout()
                    await websocket.send_json({"type": "state", "state": orchestrator.state})
                elif command == "cancel":
                    await orchestrator.cancel_speaking()
                    # Guarantee IDLE after cancel
                    if orchestrator.state != "IDLE":
                        orchestrator.state = "IDLE"
                        await websocket.send_json({"type": "state", "state": "IDLE"})
                    else:
                        await websocket.send_json({"type": "state", "state": orchestrator.state})
                elif command == "setAvatar":
                    await websocket.send_json({"type": "state", "state": orchestrator.state, "avatar": data.get("avatar")})
                elif command == "reloadConfig":
                    await websocket.send_json({"type": "state", "state": orchestrator.state})
                elif command == "clearMemory":
                    await websocket.send_json({"type": "state", "state": orchestrator.state})
                else:
                    # Unknown command — echo state
                    await websocket.send_json({"type": "state", "state": orchestrator.state})
        finally:
            orchestrator.emit = original_emit  # type: ignore[assignment]

    return app
