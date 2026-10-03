from __future__ import annotations

import os
from pathlib import Path

import uvicorn

from anime_assistant.core.config import load_config, ensure_default_config
from anime_assistant.server.app import create_app


def main() -> None:
    config_path = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "anime-assistant" / "config.toml"
    ensure_default_config(config_path)
    config = load_config(config_path)
    app = create_app(config)
    uvicorn.run(app, host="127.0.0.1", port=8765)


if __name__ == "__main__":
    main()
