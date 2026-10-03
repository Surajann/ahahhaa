from __future__ import annotations

import json
from pathlib import Path


class MemoryStore:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self._messages: list[dict] = []
        self._summary: str = ""
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self._messages = []
            self._summary = ""
            return
        try:
            data = json.loads(self.path.read_text())
            self._messages = data.get("messages", [])
            self._summary = data.get("summary", "")
            # enforce ring buffer on load
            if len(self._messages) > 20:
                self._messages = self._messages[-20:]
        except Exception:
            self._messages = []
            self._summary = ""

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"messages": self._messages, "summary": self._summary}
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def append(self, role: str, content: str) -> None:
        self._messages.append({"role": role, "content": content})
        if len(self._messages) > 20:
            self._messages = self._messages[-20:]
        self.save()

    def get_messages(self) -> list[dict]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages = []
        self._summary = ""
        self.save()

    async def summarize_if_needed(self, llm_client=None) -> None:
        if len(self._messages) >= 15 and llm_client is not None:
            try:
                summary = await llm_client.summarize(self._messages)
                self._summary = summary
                self.save()
            except Exception:
                pass
