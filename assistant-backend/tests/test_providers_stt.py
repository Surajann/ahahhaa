import pytest
from unittest.mock import AsyncMock, patch

from anime_assistant.providers.stt import OpenAIWhisperSTT


def _async_iter(chunks):
    async def gen():
        for c in chunks:
            yield c
    return gen()


@pytest.mark.asyncio
async def test_stt_partial_and_final():
    provider = OpenAIWhisperSTT(api_key="test", language="auto")
    # Mock httpx post to return final text
    mock_resp = AsyncMock()
    mock_resp.json.return_value = {"text": "Halo Cyrene"}
    mock_resp.status_code = 200
    with patch("anime_assistant.providers.stt.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_resp
        chunks = [b"\x00" * 640, b"\x01" * 640]
        events = [e async for e in provider.stream_transcribe(_async_iter(chunks))]
        assert any(e["type"] == "partial" and "Halo" in e["text"] for e in events)
        assert any(e["type"] == "final" for e in events)


@pytest.mark.asyncio
async def test_stt_code_switch_prompt():
    provider = OpenAIWhisperSTT(api_key="test")
    # Verify prompt hint contains bilingual hint
    prompt = getattr(provider, "prompt", "") or getattr(provider, "_prompt", "")
    # also check attribute `prompt_hint`
    combined = prompt + getattr(provider, "prompt_hint", "") + str(provider.__dict__)
    assert "Indonesian mixed with light Japanese" in combined
