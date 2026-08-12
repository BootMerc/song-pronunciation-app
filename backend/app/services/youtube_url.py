"""Extracts a YouTube video ID from a pasted URL, covering the common
formats people actually paste: full watch URLs, youtu.be short links,
embed URLs, shorts, and the music.youtube.com / no-cookie domains.
"""

import re
from urllib.parse import parse_qs, urlparse

_VALID_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")

_WATCH_HOSTS = {
    "youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com",
    "youtube-nocookie.com", "www.youtube-nocookie.com",
}


def extract_video_id(url: str) -> str | None:
    url = url.strip()
    if not url:
        return None

    # urlparse needs a scheme to parse hostname correctly; people often
    # paste links without "https://".
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = f"https://{url}"

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()

    if host == "youtu.be":
        candidate = parsed.path.lstrip("/")
        return candidate if _VALID_ID.match(candidate) else None

    if host in _WATCH_HOSTS:
        if parsed.path == "/watch":
            candidate = parse_qs(parsed.query).get("v", [None])[0]
            return candidate if candidate and _VALID_ID.match(candidate) else None
        for prefix in ("/embed/", "/shorts/", "/live/"):
            if parsed.path.startswith(prefix):
                candidate = parsed.path[len(prefix):].split("/")[0]
                return candidate if _VALID_ID.match(candidate) else None

    return None
