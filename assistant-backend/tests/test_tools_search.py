from unittest.mock import AsyncMock, Mock, patch
import httpx
from pathlib import Path
from anime_assistant.tools.search import web_search


def test_search_mocked(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("anime_assistant.tools.search.CACHE_PATH", tmp_path / "search.json")
    # Mock httpx.post to return results
    mock_resp = Mock(status_code=200)
    mock_resp.json.return_value = {"results": [{"title": "t", "content": "c", "url": "u"}]}

    with patch("anime_assistant.tools.search.httpx.post", return_value=mock_resp):
        r1 = web_search("Honkai Star Rail", count=5)
        assert "sources" in r1
        # second call should hit cache (no extra httpx request) — ensure same result even if mock would fail
        # Patch post to fail, cache should still return
        with patch("anime_assistant.tools.search.httpx.post", side_effect=RuntimeError("should be cached")):
            r2 = web_search("Honkai Star Rail", count=5)
            assert r2["sources"] == r1["sources"]


def test_search_empty_query():
    r = web_search("", count=5)
    assert r["ok"] is False
