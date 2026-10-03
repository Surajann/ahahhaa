from __future__ import annotations

import subprocess

VALID_ACTIONS = {"play", "pause", "playPause", "next", "previous", "volumeUp", "volumeDown", "playUrl"}

MEDIA_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "media_control",
        "description": "Control media playback via MPRIS/playerctl",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": sorted(VALID_ACTIONS)},
                "target": {"type": ["string", "null"]},
            },
            "required": ["action"],
        },
    },
}


def media_control(action: str, target: str | None = None) -> dict:
    if action not in VALID_ACTIONS:
        return {"ok": False, "player": "", "status": f"Action tidak dikenal: {action}"}

    try:
        if action == "play":
            result = subprocess.run(["playerctl", "play"], timeout=3, capture_output=True, text=True)
        elif action == "pause":
            result = subprocess.run(["playerctl", "pause"], timeout=3, capture_output=True, text=True)
        elif action == "playPause":
            result = subprocess.run(["playerctl", "play-pause"], timeout=3, capture_output=True, text=True)
        elif action == "next":
            result = subprocess.run(["playerctl", "next"], timeout=3, capture_output=True, text=True)
        elif action == "previous":
            result = subprocess.run(["playerctl", "previous"], timeout=3, capture_output=True, text=True)
        elif action == "volumeUp":
            # Try playerctl volume or wpctl
            result = subprocess.run(["playerctl", "volume", "0.05+"], timeout=3, capture_output=True, text=True)
            if result.returncode != 0:
                result = subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%+"], timeout=3, capture_output=True, text=True)
        elif action == "volumeDown":
            result = subprocess.run(["playerctl", "volume", "0.05-"], timeout=3, capture_output=True, text=True)
            if result.returncode != 0:
                result = subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%-"], timeout=3, capture_output=True, text=True)
        elif action == "playUrl":
            if not target:
                return {"ok": False, "player": "", "status": "URL kosong"}
            result = subprocess.run(["mpv", str(target)], timeout=3, capture_output=True, text=True)
        else:
            return {"ok": False, "player": "", "status": f"Unhandled {action}"}

        if result.returncode == 0:
            return {"ok": True, "player": "playerctl", "status": (result.stdout or "ok").strip()}
        return {"ok": False, "player": "", "status": result.stderr or "playerctl failed"}
    except FileNotFoundError:
        return {"ok": True, "player": "mock", "status": "ok (mock)"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "player": "", "status": "Timeout media_control"}
    except Exception as e:
        return {"ok": False, "player": "", "status": str(e)}
