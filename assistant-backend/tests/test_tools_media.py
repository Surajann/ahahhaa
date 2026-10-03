from unittest.mock import Mock
from anime_assistant.tools.media import media_control


def test_media_next(monkeypatch):
    monkeypatch.setattr("subprocess.run", lambda *a, **k: Mock(returncode=0, stdout="playing"))
    res = media_control("next", None)
    assert res["ok"] is True


def test_media_invalid_action():
    res = media_control("explode", None)
    assert res["ok"] is False


def test_media_pause(monkeypatch):
    monkeypatch.setattr("subprocess.run", lambda *a, **k: Mock(returncode=0, stdout="paused"))
    res = media_control("pause", None)
    assert res["ok"] is True
