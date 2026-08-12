"""Thin async client for LRCLIB — a free, open, no-auth synced-lyrics database.

https://lrclib.net/docs
"""

import httpx
from pydantic import BaseModel

LRCLIB_SEARCH_URL = "https://lrclib.net/api/search"
USER_AGENT = "song-pronunciation-app/0.1 (personal project)"


class LRCLIBError(Exception):
    """Raised for network failures or unexpected LRCLIB API responses."""


class LyricsResult(BaseModel):
    track_name: str
    artist_name: str
    plain_lyrics: str | None = None
    synced_lyrics: str | None = None
    instrumental: bool = False

    @property
    def has_synced_lyrics(self) -> bool:
        return bool(self.synced_lyrics)


async def fetch_lyrics(track_name: str, artist_name: str) -> LyricsResult | None:
    """Search LRCLIB for lyrics matching this song.

    Returns None if no match is found — an expected outcome that should
    trigger the manual-paste fallback in the UI, not an error state.
    """
    params = {"track_name": track_name, "artist_name": artist_name}
    headers = {"User-Agent": USER_AGENT}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                LRCLIB_SEARCH_URL, params=params, headers=headers
            )
    except httpx.RequestError as exc:
        raise LRCLIBError(f"Could not reach LRCLIB: {exc}") from exc

    if response.status_code != 200:
        raise LRCLIBError(
            f"LRCLIB returned HTTP {response.status_code}: {response.text}"
        )

    results = response.json()
    if not results:
        return None

    match = _best_match(results, artist_name)
    return LyricsResult(
        track_name=match["trackName"],
        artist_name=match["artistName"],
        plain_lyrics=match.get("plainLyrics") or None,
        synced_lyrics=match.get("syncedLyrics") or None,
        instrumental=match.get("instrumental", False),
    )


def _best_match(results: list[dict], wanted_artist: str) -> dict:
    """Prefer a result whose artist matches exactly; else take LRCLIB's top hit."""
    wanted = wanted_artist.strip().casefold()
    for result in results:
        if result.get("artistName", "").strip().casefold() == wanted:
            return result
    return results[0]
