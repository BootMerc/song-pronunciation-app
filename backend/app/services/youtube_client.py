"""Thin async client for the one YouTube Data API v3 call this app needs.

Search only, no OAuth, no uploads, no write access. A search.list call
costs 100 quota units against the free 10,000/day budget — about 100
song lookups a day per API key.
"""

import httpx
from pydantic import BaseModel

from app.config import settings

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


class YouTubeConfigError(Exception):
    """Raised when the app is asked to call YouTube without a configured API key."""


class YouTubeAPIError(Exception):
    """Raised for network failures or non-quota API errors talking to YouTube."""


class YouTubeQuotaExceededError(YouTubeAPIError):
    """Raised specifically when YouTube reports the daily quota is exhausted."""


class YouTubeVideoResult(BaseModel):
    video_id: str
    title: str
    channel_title: str
    thumbnail_url: str | None = None

    @property
    def watch_url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.video_id}"


def _raise_for_youtube_errors(response: httpx.Response) -> None:
    if response.status_code == 403:
        body = response.json()
        reason = body.get("error", {}).get("errors", [{}])[0].get("reason", "")
        if reason == "quotaExceeded":
            raise YouTubeQuotaExceededError(
                "YouTube's daily quota (10,000 units) is exhausted. "
                "It resets at midnight Pacific time."
            )
        raise YouTubeAPIError(f"YouTube rejected the request: {body}")

    if response.status_code != 200:
        raise YouTubeAPIError(
            f"YouTube returned HTTP {response.status_code}: {response.text}"
        )


def _video_result_from_snippet(video_id: str, snippet: dict) -> YouTubeVideoResult:
    thumbnails = snippet.get("thumbnails", {})
    thumbnail_url = thumbnails.get("high", thumbnails.get("default", {})).get("url")
    return YouTubeVideoResult(
        video_id=video_id,
        title=snippet["title"],
        channel_title=snippet["channelTitle"],
        thumbnail_url=thumbnail_url,
    )


async def search_video(title: str, artist: str) -> YouTubeVideoResult | None:
    """Search YouTube for a video matching this song and return the top result.

    Returns None if YouTube has no matching video — an expected outcome
    the caller should handle (e.g. ask the user to check the spelling),
    not an error.
    """
    if not settings.youtube_api_key:
        raise YouTubeConfigError(
            "YOUTUBE_API_KEY is not set. Get one from Google Cloud Console "
            "(enable 'YouTube Data API v3', then Credentials -> Create API "
            "Key) and add it to backend/.env."
        )

    params = {
        "part": "snippet",
        "q": f"{artist} {title}",
        "type": "video",
        "maxResults": 1,
        "key": settings.youtube_api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(YOUTUBE_SEARCH_URL, params=params)
    except httpx.RequestError as exc:
        raise YouTubeAPIError(f"Could not reach YouTube: {exc}") from exc

    _raise_for_youtube_errors(response)

    items = response.json().get("items", [])
    if not items:
        return None

    top = items[0]
    return _video_result_from_snippet(top["id"]["videoId"], top["snippet"])


async def get_video_by_id(video_id: str) -> YouTubeVideoResult | None:
    """Fetch a known video's metadata directly — 1 quota unit, vs. 100 for
    search_video. Used by the paste-a-YouTube-link input path, where we
    already have the video ID from the URL and don't need to search.

    Returns None if the video doesn't exist or isn't public (deleted,
    private, region-blocked) — an expected outcome, not an error.
    """
    if not settings.youtube_api_key:
        raise YouTubeConfigError(
            "YOUTUBE_API_KEY is not set. Get one from Google Cloud Console "
            "(enable 'YouTube Data API v3', then Credentials -> Create API "
            "Key) and add it to backend/.env."
        )

    params = {"part": "snippet", "id": video_id, "key": settings.youtube_api_key}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(YOUTUBE_VIDEOS_URL, params=params)
    except httpx.RequestError as exc:
        raise YouTubeAPIError(f"Could not reach YouTube: {exc}") from exc

    _raise_for_youtube_errors(response)

    items = response.json().get("items", [])
    if not items:
        return None

    top = items[0]
    # Note: videos.list nests the id directly (top["id"]), not under
    # id.videoId the way search.list does — a real, easy-to-miss
    # difference between the two endpoints' response shapes.
    return _video_result_from_snippet(top["id"], top["snippet"])
