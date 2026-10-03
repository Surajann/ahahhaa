from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import httpx

SEARCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web and return summary + sources",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "count": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
    },
}

CACHE_PATH = Path.home() / ".cache" / "anime-assistant" / "search.json"
CACHE_TTL = 600  # 10 minutes


def _load_cache() -> dict:
    try:
        if CACHE_PATH.exists():
            return json.loads(CACHE_PATH.read_text())
    except Exception:
        pass
    return {}


def _save_cache(data: dict) -> None:
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(data, ensure_ascii=False))
    except Exception:
        pass


def web_search(query: str, count: int = 5) -> dict:
    if not query or not query.strip():
        return {"ok": False, "summary": "", "sources": [], "message": "Query kosong"}
    q = query.strip()
    cache_key = hashlib.sha256(q.encode()).hexdigest()[:16]
    cache = _load_cache()
    now = time.time()
    if cache_key in cache:
        entry = cache[cache_key]
        if isinstance(entry, dict) and entry.get("expiresAt", 0) > now:
            return {"ok": True, "summary": entry.get("summary", ""), "sources": entry.get("sources", [])}

    # Tavily API — requires key from env or config; if missing, return mock-friendly result
    # In tests httpx.post is mocked
    api_key = os.environ.get("TAVILY_API_KEY", "") or os.environ.get("ANIME_TAVILY_KEY", "")
    # Allow call even without key when mocked; real call will fail gracefully
    try:
        resp = httpx.post(
            "https://api.tavily.com/search",
            json={"query": q, "search_depth": "basic", "max_results": count, "api_key": api_key},
            timeout=6,
        )
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", []) if isinstance(data, dict) else []
            sources = []
            for r in results[:count]:
                if isinstance(r, dict):
                    sources.append({"title": r.get("title", ""), "content": r.get("content", "")[:500], "url": r.get("url", "")})
            summary = sources[0]["content"] if sources else ""
            entry = {"summary": summary, "sources": sources, "expiresAt": now + CACHE_TTL}
            cache[cache_key] = entry
            _save_cache(cache)
            return {"ok": True, "summary": summary, "sources": sources}
        return {"ok": False, "summary": "", "sources": [], "message": f"Tavily status {resp.status_code}"}
    except Exception as e:
        return {"ok": False, "summary": "", "sources": [], "message": str(e)}
