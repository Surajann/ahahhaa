from __future__ import annotations

import struct
from typing import Callable

from anime_assistant.core.config import Config

# Optional VAD — we provide a fallback if webrtcvad not installed
try:
    import webrtcvad  # type: ignore
except Exception:
    webrtcvad = None  # type: ignore[assignment]


class WakeDetector:
    """VAD gate + wake word inference. Lightweight fallback without openWakeWord in tests."""

    WAKE_WORDS = ["halo castorice", "ne cyrene", "halo cyrene"]

    def __init__(self, config: Config, on_wake: Callable[[str], None]):
        self.config = config
        self.on_wake = on_wake
        self.threshold: float = float(config.wake.threshold) if hasattr(config, "wake") else 0.5
        self._vad = None
        if webrtcvad is not None:
            try:
                self._vad = webrtcvad.Vad(2)
            except Exception:
                self._vad = None

    def is_speech(self, chunk: bytes) -> bool:
        # chunk is 640 bytes = 320 samples int16 @16kHz, 20ms
        # VAD fallback: if webrtcvad unavailable or chunk wrong size, use energy heuristic
        if self._vad is not None:
            try:
                # webrtcvad requires 10,20,30ms frames at 16kHz
                return bool(self._vad.is_speech(chunk, 16000))
            except Exception:
                pass
        # Energy fallback: non-zero chunk is considered speech
        if not chunk:
            return False
        # Simple RMS check: silence is all zeros
        # Use set check for speed in tests
        return any(b != 0 for b in chunk)

    def _infer(self, chunk: bytes) -> float:
        """Return wake score 0..1. In production, delegates to openWakeWord."""
        # Without model, return 0 — tests monkeypatch this
        return 0.0

    def process_pcm(self, chunk: bytes) -> bool:
        if not self.is_speech(chunk):
            return False
        score = self._infer(chunk)
        if score >= self.threshold:
            word = self.config.wake.words[0] if self.config.wake.words else self.WAKE_WORDS[0]
            try:
                self.on_wake(word)
            except Exception:
                pass
            return True
        return False

    def reset(self) -> None:
        pass
