from __future__ import annotations

import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from anime_assistant.core.orchestrator import Orchestrator
from anime_assistant.core.config import Config

logger = logging.getLogger(__name__)


def _build_llm(config: Config):
    try:
        from anime_assistant.providers.llm import OpenAILLM

        api_key = getattr(getattr(config, "api_keys", None), "openai", "") or ""
        model = getattr(getattr(config, "llm", None), "model", "oc/muse-spark-1.2-contributor-free")
        base_url = getattr(getattr(config, "llm", None), "base_url", "http://localhost:20128/v1")
        if not api_key:
            return None
        return OpenAILLM(api_key=api_key, model=model, base_url=base_url)
    except Exception:
        return None


def _build_tts(config: Config):
    # Try OpenAI TTS first, fallback to gTTS local (no key needed)
    try:
        from anime_assistant.providers.tts import OpenAITTS, GTTSTTS

        voice = getattr(getattr(config, "tts", None), "voice_id", "alloy") or "alloy"
        api_key = getattr(getattr(config, "api_keys", None), "openai", "") or ""
        if api_key and getattr(getattr(config, "tts", None), "provider", "openai") in ("openai", "gtts"):
            # OpenAITTS will fallback to gTTS internally if cloud fails
            return OpenAITTS(api_key=api_key, voice=voice)
        # No key or provider gtts → direct gTTS
        return GTTSTTS(lang="id")
    except Exception:
        return None


def create_app(config: Config | None = None) -> FastAPI:
    if config is None:
        config = Config()
    app = FastAPI()
    llm = _build_llm(config)
    tts = _build_tts(config)
    orchestrator = Orchestrator(config=config, memory=None, llm=llm, tts=tts)

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
                # Mic→STT path: {transcript, text} or {command:"transcript", text} → LLM→TTS
                txt: str | None = None
                if isinstance(data, dict):
                    if "transcript" in data and isinstance(data["transcript"], str) and data["transcript"].strip():
                        txt = data["transcript"].strip()
                    elif data.get("type") in ("stt.final", "transcript.final", "stt_final", "final") and isinstance(data.get("text"), str) and str(data.get("text")).strip():
                        txt = str(data.get("text")).strip()
                    elif isinstance(data.get("text"), str) and str(data.get("text")).strip():
                        # plain {text:"..."} from overlay fallback input
                        txt = str(data["text"]).strip()
                if txt:
                    logger.info("stt final: %s", txt[:200])
                    # ensure we are in LISTENING or THINKING; barge-in if SPEAKING
                    if orchestrator.state == "SPEAKING":
                        await orchestrator.barge_in()
                    elif orchestrator.state == "IDLE":
                        await orchestrator._set_state("LISTENING")
                    await orchestrator.on_stt_final(txt)
                    continue
                command = data.get("command") if isinstance(data, dict) else None
                if command == "startListening":
                    await orchestrator.on_wake(data.get("word", "manual"))
                    # orchestrator already emitted state via _set_state
                elif command == "stopListening":
                    await orchestrator.handle_timeout()
                elif command in ("transcript", "stt_final", "sendText"):
                    t = str(data.get("text", "") or data.get("transcript", "")).strip()
                    if t:
                        if orchestrator.state == "SPEAKING":
                            await orchestrator.barge_in()
                        elif orchestrator.state == "IDLE":
                            await orchestrator._set_state("LISTENING")
                        await orchestrator.on_stt_final(t)
                    continue
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
