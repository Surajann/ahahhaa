# Anime Assistant — Live2D Overlay (Full Cloud + Wake Lokal)

Spec: `docs/superpowers/specs/2026-10-03-anime-assistant-live2d-design.md`
Plan: `docs/superpowers/plans/2026-10-03-anime-assistant-live2d.md`

Arch `B`: VAD + wake word lokal (~50MB, no stream before wake) + STT/LLM/TTS cloud.

## Quick start

```bash
./scripts/install.sh
# edit ~/.config/anime-assistant/config.toml (chmod 600) — fill api_keys
systemctl --user start anime-assistant
curl http://127.0.0.1:8765/health
```
