from pathlib import Path
from anime_assistant.core.memory import MemoryStore


def test_memory_ring_buffer(tmp_path: Path):
    store = MemoryStore(tmp_path / "memory.json")
    for i in range(25):
        store.append("user", f"msg {i}")
    assert len(store.get_messages()) == 20
    assert store.get_messages()[0]["content"] == "msg 5"


def test_memory_clear(tmp_path: Path):
    store = MemoryStore(tmp_path / "memory.json")
    store.append("user", "hello")
    store.clear()
    assert store.get_messages() == []
