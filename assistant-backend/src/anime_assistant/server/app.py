from __future__ import annotations

import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from anime_assistant.core.orchestrator import Orchestrator
from anime_assistant.core.config import Config

logger = logging.getLogger(__name__)


def create_app(config: Config | None = None) -> FastAPI:
    if config is None:
        config = Config()
    app = FastAPI()
    orchestrator = Orchestrator(config=config, memory=None)

    # Startup validation for empty api_keys (C5) — log only, orchestrator will bubble on wake
    if not orchestrator._has_api_keys():
        logger.warning("api_keys kosong — isi ~/.config/anime-assistant/config.toml ne~")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/config")
    def get_config():
        return {"llm": {"model": config.llm.model}, "avatar": {"mode": config.avatar.mode}}

    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket):
        await websocket.accept()

        async def _emit(event: dict):
            try:
                await websocket.send_json(event)
            except Exception as e:
                logger.debug("ws send failed: %s", e)

        orchestrator.emit = _emit  # type: ignore[assignment]
        try:
            while True:
                try:
                    data = await websocket.receive_json()
                except WebSocketDisconnect:
                    # C6: WS drop mid-SPEAKING -> cancel and go IDLE
                    try:
                        await orchestrator.cancel_speaking()
                    except Exception:
                        pass
                    break
                except Exception:
                    break
                command = data.get("command") if isinstance(data, dict) else None
                if command == "startListening":
                    await orchestrator.on_wake(data.get("word", "manual"))
                    # orchestrator already emitted state via _set_state
                elif command == "stopListening":
                    await orchestrator.handle_timeout()
                elif command == "cancel":
                    await orchestrator.cancel_speaking()
                    if orchestrator.state != "IDLE":
                        orchestrator.state = "IDLE"
                        await websocket.send_json({"type": "state", "state": "IDLE"})
                    else:
                        await websocket.send_json({"type": "state", "state": orchestrator.state})
                    continue
                elif command == "setAvatar":
                    await _emit({"type": "state", "state": orchestrator.state, "avatar": data.get("avatar")})
                    continue
                elif command == "reloadConfig":
                    await _emit({"type": "state", "state": orchestrator.state})
                    continue
                elif command == "clearMemory":
                    await _emit({"type": "state", "state": orchestrator.state})
                    continue
                else:
                    # Unknown command — echo state
                    await _emit({"type": "state", "state": orchestrator.state})
                    continue
                # For commands that changed state via orchestrator, the state was already emitted.
                # Send an extra state echo for TestClient expectations if needed (no double if already sent)
                # We rely on orchestrator's emit for state, but ensure at least one state message
                # If orchestrator emitted state, the client already received it; we don't duplicate.
        finally:
            orchestrator.emit = lambda e: None  # type: ignore[assignment]

    return app
