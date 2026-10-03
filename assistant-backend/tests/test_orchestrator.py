import pytest
from anime_assistant.core.config import Config
from anime_assistant.core.memory import MemoryStore
from anime_assistant.core.orchestrator import Orchestrator


def _mock_config():
    return Config()


def _mock_stt():
    return None


def _mock_llm():
    return None


def _mock_tts():
    return None


def _mock_memory(tmp_path=None):
    # Use in-memory-friendly MemoryStore or mock
    if tmp_path:
        return MemoryStore(tmp_path / "memory.json")
    # simple mock with append
    class M:
        def append(self, role, content):
            pass
        def get_messages(self):
            return []
    return M()


@pytest.mark.asyncio
async def test_orchestrator_state_transitions(tmp_path):
    mem = _mock_memory(tmp_path)
    orch = Orchestrator(config=_mock_config(), stt=_mock_stt(), llm=_mock_llm(), tts=_mock_tts(), memory=mem)
    events = []
    orch.emit = lambda e: events.append(e)
    await orch.on_wake("Halo Castorice")
    assert orch.state == "LISTENING"
    await orch.on_stt_final("Halo, buka Firefox ne?")
    assert orch.state == "THINKING"
    await orch.on_llm_done()
    assert orch.state == "SPEAKING"
    await orch.on_tts_done()
    assert orch.state == "IDLE"


@pytest.mark.asyncio
async def test_barge_in_from_speaking(tmp_path):
    mem = _mock_memory(tmp_path)
    orch = Orchestrator(config=_mock_config(), stt=_mock_stt(), llm=_mock_llm(), tts=_mock_tts(), memory=mem)
    orch.state = "SPEAKING"
    await orch.barge_in()
    assert orch.state == "LISTENING"


@pytest.mark.asyncio
async def test_orchestrator_timeout(tmp_path):
    mem = _mock_memory(tmp_path)
    orch = Orchestrator(config=_mock_config(), stt=_mock_stt(), llm=_mock_llm(), tts=_mock_tts(), memory=mem)
    orch.state = "LISTENING"
    await orch.handle_timeout()
    assert orch.state == "IDLE"
