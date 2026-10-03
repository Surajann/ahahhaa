#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
echo "== Anime Assistant install =="
echo "-- Checking system deps --"
for cmd in uv python3 node npm; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd" >&2; exit 1
  fi
done
for opt in playerctl hyprctl pipewire; do
  if ! command -v "$opt" >/dev/null 2>&1; then
    echo "Optional missing: $opt — run pacman -S $opt if needed"
  fi
done
echo "-- Backend deps --"
uv --directory "$DIR" pip install -e ".[dev, audio]" 2>&1 | tail -n 5 || uv --directory "$DIR" pip install -e "." 2>&1 | tail -n 5
echo "-- Overlay deps --"
npm --prefix "$DIR/assistant-overlay" install
echo "-- Config --"
XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
mkdir -p "$XDG_CONFIG_HOME/anime-assistant/models"
mkdir -p "$HOME/.local/state/anime-assistant/logs"
mkdir -p "$HOME/.cache/anime-assistant"
uv --directory "$DIR" run python -c "from anime_assistant.core.config import ensure_default_config; print(ensure_default_config())"
echo "-- Systemd --"
if systemctl --user daemon-reload 2>&1 | head -1; then
  echo "Run: systemctl --user enable --now anime-assistant (after filling api_keys in ~/.config/anime-assistant/config.toml)"
fi
echo "-- Done: edit ~/.config/anime-assistant/config.toml (chmod 600) then systemctl --user start anime-assistant --"
