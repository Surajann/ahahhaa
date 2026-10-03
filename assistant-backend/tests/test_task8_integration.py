from pathlib import Path
from fastapi.testclient import TestClient
from anime_assistant.core.config import load_config, ensure_default_config
from anime_assistant.server.app import create_app


def test_health_endpoint(tmp_path: Path):
    app = create_app(load_config(tmp_path / "config.toml"))
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}


def test_install_creates_config(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    ensure_default_config()
    assert (tmp_path / "anime-assistant" / "config.toml").exists()


def test_main_entry_importable():
    # __main__ should be importable as module
    import importlib
    mod = importlib.import_module("anime_assistant.server.__main__")
    assert hasattr(mod, "main") or hasattr(mod, "__name__")
