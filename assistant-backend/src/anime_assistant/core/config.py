from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib  # py 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


@dataclass
class ApiKeys:
    openai: str = ""
    gemini: str = ""
    elevenlabs: str = ""
    tavily: str = ""


@dataclass
class LlmConfig:
    provider: str = "openai"
    model: str = "oc/muse-spark-1.2-contributor-free"
    base_url: str = "http://localhost:20128/v1"
    fallback: str = ""


@dataclass
class SttConfig:
    provider: str = "openai"


@dataclass
class TtsConfig:
    provider: str = "elevenlabs"
    voice_id: str = "anime"
    speed: float = 1.0


@dataclass
class WakeConfig:
    words: list[str] = field(default_factory=lambda: ["Halo Castorice", "Ne, Cyrene", "Halo Cyrene"])
    threshold: float = 0.5


@dataclass
class AvatarConfig:
    name: str = "Castorice"
    path: str = ""
    mode: str = "live2d"  # live2d | static


@dataclass
class OverlayConfig:
    position: str = "bottom-right"
    size: str = "380x520"
    margin: int = 24


@dataclass
class AudioConfig:
    inputDevice: str = ""


@dataclass
class Config:
    api_keys: ApiKeys = field(default_factory=ApiKeys)
    llm: LlmConfig = field(default_factory=LlmConfig)
    stt: SttConfig = field(default_factory=SttConfig)
    tts: TtsConfig = field(default_factory=TtsConfig)
    wake: WakeConfig = field(default_factory=WakeConfig)
    avatar: AvatarConfig = field(default_factory=AvatarConfig)
    overlay: OverlayConfig = field(default_factory=OverlayConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)


def _parse_config_dict(data: dict) -> Config:
    cfg = Config()
    if "api_keys" in data:
        d = data["api_keys"]
        cfg.api_keys.openai = str(d.get("openai", cfg.api_keys.openai))
        cfg.api_keys.gemini = str(d.get("gemini", cfg.api_keys.gemini))
        cfg.api_keys.elevenlabs = str(d.get("elevenlabs", cfg.api_keys.elevenlabs))
        cfg.api_keys.tavily = str(d.get("tavily", cfg.api_keys.tavily))
    if "llm" in data:
        d = data["llm"]
        cfg.llm.provider = str(d.get("provider", cfg.llm.provider))
        cfg.llm.model = str(d.get("model", cfg.llm.model))
        if "base_url" in d:
            cfg.llm.base_url = str(d.get("base_url", cfg.llm.base_url))
        cfg.llm.fallback = str(d.get("fallback", cfg.llm.fallback))
    if "stt" in data:
        d = data["stt"]
        cfg.stt.provider = str(d.get("provider", cfg.stt.provider))
    if "tts" in data:
        d = data["tts"]
        cfg.tts.provider = str(d.get("provider", cfg.tts.provider))
        cfg.tts.voice_id = str(d.get("voice_id", cfg.tts.voice_id))
        # speed may be numeric
        if "speed" in d:
            try:
                cfg.tts.speed = float(d["speed"])
            except (TypeError, ValueError):
                pass
    if "wake" in data:
        d = data["wake"]
        if "words" in d and isinstance(d["words"], list):
            cfg.wake.words = [str(w) for w in d["words"]]
        if "threshold" in d:
            try:
                cfg.wake.threshold = float(d["threshold"])
            except (TypeError, ValueError):
                pass
    if "avatar" in data:
        d = data["avatar"]
        cfg.avatar.name = str(d.get("name", cfg.avatar.name))
        cfg.avatar.path = str(d.get("path", cfg.avatar.path))
        mode = str(d.get("mode", cfg.avatar.mode))
        if mode in ("live2d", "static"):
            cfg.avatar.mode = mode
    if "overlay" in data:
        d = data["overlay"]
        cfg.overlay.position = str(d.get("position", cfg.overlay.position))
        cfg.overlay.size = str(d.get("size", cfg.overlay.size))
        if "margin" in d:
            try:
                cfg.overlay.margin = int(d["margin"])
            except (TypeError, ValueError):
                pass
    if "audio" in data:
        d = data["audio"]
        cfg.audio.inputDevice = str(d.get("inputDevice", cfg.audio.inputDevice))
    return cfg


def load_config(path: Path | str) -> Config:
    """Read TOML at path, return defaults if missing/invalid."""
    p = Path(path)
    if not p.exists():
        return Config()
    try:
        with p.open("rb") as f:
            data = tomllib.load(f)
        if not isinstance(data, dict):
            return Config()
        return _parse_config_dict(data)
    except Exception:
        return Config()


def ensure_default_config(path: Path | str | None = None) -> Path:
    """Create default config.toml with chmod 600 if not exists. Returns path."""
    if path is None:
        base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
        path = base / "anime-assistant" / "config.toml"
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        cfg = Config()
        # minimal TOML
        content = (
            '# Anime Assistant config — fill api_keys\n'
            '[api_keys]\n'
            'openai = ""\n'
            'gemini = ""\n'
            'elevenlabs = ""\n'
            'tavily = ""\n'
            '\n'
            '[llm]\n'
            f'provider = "{cfg.llm.provider}"\n'
            f'model = "{cfg.llm.model}"\n'
            f'base_url = "{cfg.llm.base_url}"\n'
            f'fallback = "{cfg.llm.fallback}"\n'
            '\n'
            '[stt]\n'
            f'provider = "{cfg.stt.provider}"\n'
            '\n'
            '[tts]\n'
            f'provider = "{cfg.tts.provider}"\n'
            f'voice_id = "{cfg.tts.voice_id}"\n'
            f'speed = {cfg.tts.speed}\n'
            '\n'
            '[wake]\n'
            f'words = {cfg.wake.words!r}\n'
            f'threshold = {cfg.wake.threshold}\n'
            '\n'
            '[avatar]\n'
            f'name = "{cfg.avatar.name}"\n'
            f'path = "{cfg.avatar.path}"\n'
            f'mode = "{cfg.avatar.mode}"\n'
            '\n'
            '[overlay]\n'
            f'position = "{cfg.overlay.position}"\n'
            f'size = "{cfg.overlay.size}"\n'
            f'margin = {cfg.overlay.margin}\n'
            '\n'
            '[audio]\n'
            f'inputDevice = "{cfg.audio.inputDevice}"\n'
        )
        p.write_text(content)
        try:
            p.chmod(0o600)
        except Exception:
            pass
    return p


def reload_config(path: Path | str) -> Config:
    return load_config(path)
