from __future__ import annotations

import asyncio
import logging
from typing import Callable

from anime_assistant.core.config import Config

STATES = {"IDLE", "LISTENING", "THINKING", "SPEAKING"}

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, config: Config, stt=None, llm=None, tts=None, memory=None):
        self.config = config
        self.stt = stt
        self.llm = llm
        self.tts = tts
        self.memory = memory
        self.state: str = "IDLE"
        self.emit: Callable[[dict], object] = lambda e: None
        self._tts_cancelled = False
        self._timeout_task: asyncio.Task | None = None

    async def _set_state(self, new_state: str) -> None:
        self.state = new_state
        try:
            res = self.emit({"type": "state", "state": new_state})
            if asyncio.iscoroutine(res):
                await res
        except Exception as e:
            logger.debug("emit state failed: %s", e)

    async def _emit(self, event: dict) -> None:
        try:
            res = self.emit(event)
            if asyncio.iscoroutine(res):
                await res
        except Exception as e:
            logger.debug("emit failed: %s", e)

    async def _schedule_timeout(self, sec: float = 6.0) -> None:
        if self._timeout_task:
            self._timeout_task.cancel()
        async def _wait():
            try:
                await asyncio.sleep(sec)
                if self.state == "LISTENING":
                    await self.handle_timeout()
            except asyncio.CancelledError:
                pass
        self._timeout_task = asyncio.create_task(_wait())

    async def on_wake(self, word: str) -> None:
        # barge-in if speaking
        if self.state == "SPEAKING":
            await self.barge_in()
        else:
            await self._set_state("LISTENING")
            self._tts_cancelled = False
            await self._schedule_timeout(6.0)
            # emit error bubble if api keys missing
            if not self._has_api_keys():
                await self._emit({"type": "error", "bubble": "Isi api_keys di ~/.config/anime-assistant/config.toml ne~", "state": self.state})

    def _has_api_keys(self) -> bool:
        try:
            ak = self.config.api_keys
            return bool(ak.openai or ak.gemini or ak.elevenlabs or ak.tavily)
        except Exception:
            return False

    async def on_pcm(self, chunk: bytes) -> None:
        # forward to STT streaming if available and listening
        if self.state != "LISTENING" or not self.stt:
            return
        # no-op stub — real streaming in server layer
        pass

    async def on_silence(self) -> None:
        if self.state == "LISTENING":
            await self.handle_timeout()

    async def on_stt_final(self, text: str) -> None:
        if self._timeout_task:
            self._timeout_task.cancel()
            self._timeout_task = None
        if self.memory is not None:
            try:
                self.memory.append("user", text)
            except Exception:
                pass
        await self._emit({"type": "transcript.final", "text": text})
        await self._set_state("THINKING")
        # Kick LLM→TTS pipeline if providers are wired (C1)
        if self.llm:
            try:
                await self._run_llm_tts_pipeline(text)
            except Exception as e:
                logger.warning("llm/tts pipeline failed: %s", e)
                await self._emit({"type": "error", "bubble": f"Gomen, error ne~: {e}", "state": self.state})
                await self._set_state("IDLE")

    async def _run_llm_tts_pipeline(self, user_text: str) -> None:
        # Build messages from memory
        messages: list[dict] = []
        if self.memory:
            try:
                messages = self.memory.get_messages()[-20:]
            except Exception:
                messages = []
        if not messages:
            messages = [{"role": "user", "content": user_text}]
        # Minimal LLM streaming with optional tool dispatch (single round-trip)
        tools = []
        try:
            from anime_assistant.tools.hyprland import HYPR_TOOL_SCHEMA
            from anime_assistant.tools.media import MEDIA_TOOL_SCHEMA
            from anime_assistant.tools.search import SEARCH_TOOL_SCHEMA
            tools = [HYPR_TOOL_SCHEMA, MEDIA_TOOL_SCHEMA, SEARCH_TOOL_SCHEMA]
        except Exception:
            tools = []
        tool_calls: list[dict] = []
        llm_text = ""
        async for ev in self.llm.stream_chat(messages, tools):  # type: ignore[union-attr]
            if ev.get("type") == "token":
                llm_text += ev.get("text", "")
                await self._emit({"type": "llm.token", "text": ev.get("text", "")})
            elif ev.get("type") == "tool_call":
                tool_calls.append(ev)
        # Execute tool calls (single round-trip)
        if tool_calls and self.llm:
            for tc in tool_calls:
                name = tc.get("name", "")
                args = tc.get("args", {})
                if isinstance(args, str):
                    try:
                        import json as _json
                        args = _json.loads(args)
                    except Exception:
                        args = {}
                result = {"ok": False, "message": "unknown tool"}
                try:
                    if name == "hyprland_control":
                        from anime_assistant.tools.hyprland import hyprland_control
                        result = hyprland_control(args.get("action", ""), args.get("args", {}))
                    elif name == "media_control":
                        from anime_assistant.tools.media import media_control
                        result = media_control(args.get("action", ""), args.get("target"))
                    elif name == "web_search":
                        from anime_assistant.tools.search import web_search
                        # Pass config tavily key
                        tavily_key = getattr(self.config.api_keys, "tavily", "") if hasattr(self.config, "api_keys") else ""
                        result = web_search(args.get("query", ""), int(args.get("count", 5)), api_key=tavily_key or None)
                    await self._emit({"type": "tool.result", "name": name, "result": result})
                except Exception as e:
                    await self._emit({"type": "tool.result", "name": name, "result": {"ok": False, "message": str(e)}})
            # Append tool results to messages and get final summary token (simplified: append result text)
            messages.append({"role": "assistant", "content": llm_text})
            for tc in tool_calls:
                messages.append({"role": "tool", "content": str(tc)})
        # TTS
        if self.tts and llm_text.strip():
            from anime_assistant.core.expression import parse_expression
            cleaned, expr = parse_expression(llm_text)
            await self._emit({"type": "expression", "name": expr})
            await self._set_state("SPEAKING")
            async for chunk in self.tts.stream_synth(cleaned):  # type: ignore[union-attr]
                if self._tts_cancelled:
                    break
                # WS JSON can't carry bytes → base64
                import base64

                raw = chunk.get("audio")
                if isinstance(raw, (bytes, bytearray)):
                    b64 = base64.b64encode(bytes(raw)).decode()
                else:
                    b64 = raw
                # cap queue: only emit, overlay will queue cap 8
                await self._emit({"type": "tts.chunk", "audio": b64, "audioB64": b64, "viseme": chunk.get("viseme"), "durationMs": chunk.get("durationMs", 200), "mime": chunk.get("mime", "audio/wav")})
            await self.on_tts_done()
        else:
            # No TTS or empty text: go idle
            await self._set_state("IDLE")

    async def on_llm_done(self) -> None:
        await self._set_state("SPEAKING")

    async def on_tts_done(self) -> None:
        if self._timeout_task:
            self._timeout_task.cancel()
            self._timeout_task = None
        await self._set_state("IDLE")

    async def handle_timeout(self) -> None:
        if self.state == "LISTENING":
            if self._timeout_task:
                self._timeout_task.cancel()
                self._timeout_task = None
            await self._set_state("IDLE")

    async def barge_in(self) -> None:
        if self.state == "SPEAKING":
            self._tts_cancelled = True
            await self._set_state("LISTENING")
            await self._schedule_timeout(6.0)

    async def cancel_speaking(self) -> None:
        if self._timeout_task:
            self._timeout_task.cancel()
            self._timeout_task = None
        self._tts_cancelled = True
        await self._set_state("IDLE")

    async def handle_audio_device_error(self, msg: str) -> None:
        await self._emit({"type": "error", "bubble": msg, "state": "IDLE"})
        await self._set_state("IDLE")
