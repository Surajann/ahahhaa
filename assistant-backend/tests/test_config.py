from pathlib import Path
from anime_assistant.core.config import load_config


def test_config_load_defaults(tmp_path: Path):
    cfg = load_config(tmp_path / "nonexistent.toml")
    assert cfg.llm.model in ("gpt-4o-mini", "gemini-2.0-flash", "oc/muse-spark-1.2-contributor-free")
    assert cfg.avatar.mode in ("live2d", "static")


def test_config_empty_keys_fallback(tmp_path: Path):
    p = tmp_path / "config.toml"
    p.write_text('[api_keys]\nopenai=""\n')
    cfg = load_config(p)
    assert cfg.api_keys.openai == ""
