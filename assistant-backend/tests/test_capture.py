import pytest
from unittest.mock import Mock

from anime_assistant.audio.capture import AudioCapture, AudioDeviceError


def test_capture_chunk_format(monkeypatch):
    # Mock InputStream not needed for read_chunk dummy; but ensure sample_rate stored
    cap = AudioCapture(device=None, sample_rate=16000)
    chunk = cap.read_chunk()
    assert len(chunk) == 640  # 320 * 2 bytes
    assert cap.sample_rate == 16000


def test_capture_no_device_graceful(monkeypatch):
    # Simulate no devices: query_devices returns []
    import anime_assistant.audio.capture as cap_mod

    monkeypatch.setattr(cap_mod, "sd", Mock(query_devices=lambda: []))
    # Also patch sd.query_devices directly if imported
    cap = AudioCapture(device="nonexistent")
    with pytest.raises(AudioDeviceError, match="Mic tidak terdeteksi"):
        cap.start(lambda x: None)
