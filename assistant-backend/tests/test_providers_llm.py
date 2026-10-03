import pytest
from unittest.mock import AsyncMock, patch

from anime_assistant.providers.llm import OpenAILLM, GeminiLLM


def _mock_llm_response(content_chunks):
    # Build SSE-like content: each chunk is a data line
    lines = []
    for c in content_chunks:
        import json
        lines.append(f'data: {json.dumps({"choices":[{"delta":{"content":c}}]})}\n')
    lines.append("data: [DONE]\n")
    return "".join(lines)


@pytest.mark.asyncio
async def test_llm_stream_tokens():
    llm = OpenAILLM(api_key="test", model="gpt-4o-mini")
    sse = _mock_llm_response(["Halo"])
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.aiter_lines = AsyncMock()
    # Mock streaming via `stream` context
    async def _aiter_lines():
        for line in sse.splitlines():
            yield line

    with patch("anime_assistant.providers.llm.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        # stream() returns async context with aiter_lines
        mock_stream = AsyncMock()
        mock_stream.__aenter__.return_value = mock_stream
        mock_stream.aiter_lines = _aiter_lines
        mock_stream.status_code = 200
        mock_client.stream.return_value = mock_stream

        toks = [e async for e in llm.stream_chat([{"role": "user", "content": "hi"}], tools=[])]
        assert any(e["type"] == "token" for e in toks)


@pytest.mark.asyncio
async def test_llm_failover():
    fallback = GeminiLLM(api_key="test2", model="gemini-2.0-flash")
    # Provide a fallback that will succeed; llm failover should delegate to fallback
    fallback_stream = _mock_llm_response(["ok"])

    async def _fallback_gen(messages, tools):
        yield {"type": "token", "text": "ok"}
        yield {"type": "done"}

    fallback.stream_chat = lambda messages, tools: _fallback_gen(messages, tools)

    llm = OpenAILLM(api_key="test", model="gpt-4o-mini", fallback=fallback)

    # Mock primary to fail with 429
    with patch("anime_assistant.providers.llm.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        mock_fail = AsyncMock()
        mock_fail.__aenter__.return_value = mock_fail
        mock_fail.status_code = 429
        # aiter_lines won't be consumed because we fail early
        async def _empty():
            if False:
                yield ""
        mock_fail.aiter_lines = _empty
        mock_client.stream.return_value = mock_fail

        events = [e async for e in llm.stream_chat([{"role": "user", "content": "hi"}], tools=[])]
        assert any(e["type"] == "token" for e in events)
