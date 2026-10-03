from __future__ import annotations

import asyncio
from typing import Callable

from anime_assistant.core.config import Config

STATES = {"IDLE", "LISTENING", "THINKING", "SPEAKING"}


class Orchestrator:
    def __init__(self, config: Config, stt=None, llm=None, tts=None, memory=None):
        self.config = config
        self.stt = stt
        self.llm = llm
        self.tts = tts
        self.memory = memory
        self.state: str = "IDLE"
        self.emit: Callable[[dict], None] = lambda e: None
        self._tts_cancelled = False

    def _set_state(self, new_state: str) -> None:
        self.state = new_state
        try:
            self.emit({"type": "state", "state": new_state})
        except Exception:
            pass

    async def on_wake(self, word: str) -> None:
        self._set_state("LISTENING")
        self._tts_cancelled = False

    async def on_pcm(self, chunk: bytes) -> None:
        pass

    async def on_silence(self) -> None:
        if self.state == "LISTENING":
            # Could trigger STT final handling externally
            pass

    async def on_stt_final(self, text: str) -> None:
        if self.memory is not None:
            try:
                self.memory.append("user", text)
            except Exception:
                pass
        try:
            self.emit({"type": "transcript.final", "text": text})
        except Exception:
            pass
        self._set_state("THINKING")

    async def on_llm_done(self) -> None:
        self._set_state("SPEAKING")

    async def on_tts_done(self) -> None:
        self._set_state("IDLE")

    async def handle_timeout(self) -> None:
        if self.state == "LISTENING":
            self._set_state("IDLE")

    async def barge_in(self) -> None:
        if self.state == "SPEAKING":
            self._tts_cancelled = True
            self._set_state("LISTENING")

    async def cancel_speaking(self) -> None:
        self._tts_cancelled = True
        self._set_state("IDLE")
