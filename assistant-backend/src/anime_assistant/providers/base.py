from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator


class STTProvider(ABC):
    @abstractmethod
    async def stream_transcribe(self, pcm_chunks: AsyncIterator[bytes]) -> AsyncIterator[dict]:
        raise NotImplementedError
        yield {}  # type: ignore[misc]


class LLMProvider(ABC):
    @abstractmethod
    async def stream_chat(self, messages: list[dict], tools: list[dict]) -> AsyncIterator[dict]:
        raise NotImplementedError
        yield {}  # type: ignore[misc]

    async def summarize(self, messages: list[dict]) -> str:
        return ""


class TTSProvider(ABC):
    @abstractmethod
    async def stream_synth(self, text: str) -> AsyncIterator[dict]:
        raise NotImplementedError
        yield {}  # type: ignore[misc]
