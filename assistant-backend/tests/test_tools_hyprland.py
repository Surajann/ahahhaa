from unittest.mock import Mock
from anime_assistant.tools.hyprland import hyprland_control


def test_hyprland_whitelist_allows_firefox(monkeypatch):
    monkeypatch.setattr("subprocess.run", lambda *a, **k: Mock(returncode=0, stdout="ok"))
    res = hyprland_control("exec", {"command": "firefox"})
    assert res["ok"] is True


def test_hyprland_injection_blocked():
    res = hyprland_control("exec", {"command": "firefox; rm -rf /"})
    assert res["ok"] is False
    msg = res["message"].lower()
    assert "tidak diizinkan" in msg or "not allowed" in msg


def test_hyprland_workspace_bounds():
    res = hyprland_control("workspace", {"id": 99})
    assert res["ok"] is False
