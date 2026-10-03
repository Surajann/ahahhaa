from __future__ import annotations

import re

_VALID = {"happy", "thinking", "confused", "idle"}

_TAG_RE = re.compile(r"\s*\[(\w+)\]\s*$", re.IGNORECASE)


def parse_expression(text: str) -> tuple[str, str]:
    """Return (cleaned_text, expression). Strips trailing [tag] if valid."""
    m = _TAG_RE.search(text)
    if m:
        tag = m.group(1).lower()
        if tag in _VALID:
            cleaned = text[: m.start()].rstrip()
            return cleaned, tag
        # unknown tag still strip? spec says only valid tags trigger; strip unknown too to avoid leaking?
        # Keep behavior: strip only valid, otherwise idle
    return text, "idle"
