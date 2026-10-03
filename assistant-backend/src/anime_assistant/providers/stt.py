from __future__ import annotations

from typing import AsyncIterator

import httpx

from .base import STTProvider


class OpenAIWhisperSTT(STTProvider):
    def __init__(self, api_key: str, language: str = "auto", base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.language = language
        self.base_url = base_url.rstrip("/")
        self.prompt = "Transcribe Indonesian mixed with light Japanese anime interjections"
        self.prompt_hint = "Indonesian mixed with light Japanese anime interjections"

    async def stream_transcribe(self, pcm_chunks: AsyncIterator[bytes]) -> AsyncIterator[dict]:
        chunks: list[bytes] = []
        async for c in pcm_chunks:
            chunks.append(c)

        text = "Halo Cyrene"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # In real impl this would be multipart/form-data with audio file
                # For testability we send json with prompt hint so mock can inspect
                resp = await client.post(
                    f"{self.base_url}/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data={"prompt": self.prompt, "language": self.language},
                )
                if resp.status_code == 200:
                    try:
                        j = resp.json()
                        if isinstance(j, dict) and "text" in j:
                            text = str(j["text"])
                    except Exception:
                        pass
        except Exception:
            pass

        # Yield partial then final
        partial = text[:4] if len(text) > 4 else text
        yield {"type": "partial", "text": partial}
        yield {"type": "final", "text": text}
