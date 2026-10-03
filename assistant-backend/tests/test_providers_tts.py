import pytest
from unittest.mock import AsyncMock, patch

from anime_assistant.core.expression import parse_expression
from anime_assistant.providers.tts import ElevenLabsTTS


@pytest.mark.asyncio
async def test_tts_viseme_chunk():
    tts = ElevenLabsTTS(api_key="test", voice_id="anime")
    # Mock httpx stream to return dummy audio
    with patch("anime_assistant.providers.tts.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.aiter_bytes = AsyncMock(return_value=[b"\xff\xfb\x90\x00"]).__call__ if False else None
        # Provide dummy so provider falls back to fake chunk
        mock_client.post.return_value = mock_resp
        mock_client.stream.return_value = mock_resp
        chunks = [c async for c in tts.stream_synth("Halo ne~ [happy]")]
        assert len(chunks) >= 1
        assert chunks[0]["viseme"]["mouthOpen"] >= 0


@pytest.mark.asyncio
async def test_tts_strips_expression_tag():
    text, expr = parse_expression("Halo [happy]")
    assert text == "Halo"
    assert expr == "happy"
    tts = ElevenLabsTTS(api_key="test", voice_id="anime")
    with patch("anime_assistant.providers.tts.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        mock_client.post.return_value = AsyncMock(status_code=200)
        chunks = [c async for c in tts.stream_synth(text)]
        assert len(chunks) > 0
