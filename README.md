# Anime Assistant — Live2D Overlay (Full Cloud + Wake Lokal)

**Spec:** `docs/superpowers/specs/2026-10-03-anime-assistant-live2d-design.md`  
**Plan:** `docs/superpowers/plans/2026-10-03-anime-assistant-live2d.md`

Arch **B**: VAD + wake word lokal (~50MB, no stream before wake) + STT/LLM/TTS cloud.  
Stack: Python FastAPI + WebSocket backend (16kHz mono, state machine IDLE→LISTENING→THINKING→SPEAKING) ↔ Tauri overlay (Vite+PixiJS+Cubism wasm, gtk-layer-shell bottom-right `380×520`, viseme lip-sync, bubble).

## Quick start

```bash
./scripts/install.sh
# edit ~/.config/anime-assistant/config.toml (chmod 600) — fill api_keys
systemctl --user enable --now anime-assistant
curl http://127.0.0.1:8765/health  # {"status":"ok"}
```

## Manual E2E (Hyprland/Wayland, Intel UHD G4)

```bash
systemctl --user start anime-assistant
curl http://127.0.0.1:8765/health
# 1. Wake "Halo Castorice" from 1m → bubble LISTENING <300ms
# 2. "Halo Cyrene, kyou wa nani suru?" → STT final ID+JP correct
# 3. Lip-sync mouth moves, blink 3-5s, happy expression
# 4. Overlay bottom-right 380×520, drag/resize, click-through IDLE>5s, Super+Space PTT, Super+Shift+A settings
# 5. "Buka Firefox" → hyprctl exec, "next lagu" → playerctl next, "cari info Honkai" → Tavily summary
# 6. Barge-in during SPEAKING → LISTENING again
# 7. Benchmark: VRAM <300MB, RSS <350MB, first audio <2s
```

## Project layout

- `assistant-backend/` — FastAPI + providers (stt/llm/tts) + tools (hyprland/media/search) + orchestrator
- `assistant-overlay/` — Tauri + Vite + PixiJS Live2D + WS client + bubble
- `systemd/anime-assistant.service` — --user service
- `scripts/install.sh`, `scripts/anime-assistant` — installer + launcher

## Config

`~/.config/anime-assistant/config.toml` (chmod 600), models at `~/.config/anime-assistant/models/<name>/`, state `~/.local/state/anime-assistant/memory.json`, logs `~/.local/state/anime-assistant/logs/backend.log`.
