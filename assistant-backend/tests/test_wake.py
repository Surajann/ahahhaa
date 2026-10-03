from unittest.mock import Mock
from anime_assistant.audio.wake import WakeDetector
from anime_assistant.core.config import Config


def _mock_config(threshold=0.5):
    cfg = Config()
    cfg.wake.threshold = threshold
    cfg.wake.words = ["Halo Castorice", "Ne, Cyrene"]
    return cfg


def test_wake_gate_no_wake_returns_false():
    det = WakeDetector(config=_mock_config(threshold=0.5), on_wake=lambda w: None)
    # Silence PCM (zeros) — VAD should gate, no wake
    assert det.process_pcm(b"\x00" * 640) is False
    assert det.is_speech(b"\x00" * 640) is False


def test_wake_trigger(monkeypatch):
    cfg = _mock_config()
    calls = []
    det = WakeDetector(config=cfg, on_wake=lambda w: calls.append(w))
    # Mock internal _infer to return 0.9 for wake word
    monkeypatch.setattr(det, "_infer", lambda chunk: 0.9)
    # Need speech chunk so VAD passes or mock is_speech
    monkeypatch.setattr(det, "is_speech", lambda chunk: True)
    assert det.process_pcm(b"\x01" * 640) is True
    assert len(calls) == 1
