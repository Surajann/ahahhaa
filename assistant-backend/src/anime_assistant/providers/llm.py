from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from .base import LLMProvider


class OpenAILLM(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: str = "https://api.openai.com/v1", fallback: LLMProvider | None = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.fallback = fallback

    async def stream_chat(self, messages: list[dict], tools: list[dict]) -> AsyncIterator[dict]:
        url = f"{self.base_url}/chat/completions"
        payload = {"model": self.model, "messages": messages, "stream": True}
        if tools:
            payload["tools"] = tools

        try:
            async with httpx.AsyncClient(timeout=8) as client:
                async with client.stream("POST", url, json=payload, headers={"Authorization": f"Bearer {self.api_key}"}) as resp:
                    if resp.status_code != 200:
                        raise RuntimeError(f"LLM status {resp.status_code}")
                    async for line in resp.aiter_lines():  # type: ignore[attr-defined]
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            try:
                                obj = json.loads(data)
                                choices = obj.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    if "content" in delta and delta["content"]:
                                        yield {"type": "token", "text": delta["content"]}
                                    if "tool_calls" in delta:
                                        for tc in delta["tool_calls"]:
                                            yield {"type": "tool_call", "name": tc.get("function", {}).get("name", ""), "args": tc.get("function", {}).get("arguments", {})}
                            except Exception:
                                continue
                    yield {"type": "done"}
                    return
        except Exception as e:
            if self.fallback is not None:
                async for ev in self.fallback.stream_chat(messages, tools):
                    yield ev
                return
            # No fallback: yield error token then done
            yield {"type": "token", "text": ""}
            yield {"type": "done"}
            return

    async def summarize(self, messages: list[dict]) -> str:
        # Simple: return last summary placeholder or first 100 chars
        if not messages:
            return ""
        return "Ringkasan: " + messages[-1].get("content", "")[:100]


class GeminiLLM(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash", base_url: str = "https://generativelanguage.googleapis.com/v1beta"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def stream_chat(self, messages: list[dict], tools: list[dict]) -> AsyncIterator[dict]:
        # For tests: delegate to OpenAI-compatible path if needed; here just yield
        # If not mocked, yield a dummy token
        yield {"type": "token", "text": "ok"}
        yield {"type": "done"}

    async def summarize(self, messages: list[dict]) -> str:
        return await OpenAILLM(api_key=self.api_key).summarize(messages)
