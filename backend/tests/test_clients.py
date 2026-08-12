"""Tests for youtube_client and lrclib_client.

Both are mocked — this sandbox can't reach googleapis.com or lrclib.net.
Response shapes here match what was confirmed against the real APIs'
documentation during development (see backend/scripts/smoke_test.py for
live verification against the actual services).
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services import lrclib_client, youtube_client


def _response(status, body):
    return httpx.Response(status, json=body, request=httpx.Request("GET", "https://x.test"))


SEARCH_OK = {
    "items": [
        {
            "id": {"videoId": "fJ9rUzIMcZQ"},
            "snippet": {
                "title": "Queen - Bohemian Rhapsody",
                "channelTitle": "Queen Official",
                "thumbnails": {"high": {"url": "https://example.com/hq.jpg"}},
            },
        }
    ]
}
VIDEOS_OK = {
    "items": [
        {
            "id": "fJ9rUzIMcZQ",  # note: NOT nested under .videoId, unlike search.list
            "snippet": {
                "title": "Queen - Bohemian Rhapsody",
                "channelTitle": "Queen Official",
                "thumbnails": {"high": {"url": "https://example.com/hq.jpg"}},
            },
        }
    ]
}
QUOTA_EXCEEDED = {"error": {"errors": [{"reason": "quotaExceeded", "message": "quota exceeded"}]}}
LRCLIB_OK = [
    {
        "id": 1,
        "trackName": "Bohemian Rhapsody",
        "artistName": "Queen",
        "albumName": "A Night at the Opera",
        "duration": 355,
        "instrumental": False,
        "plainLyrics": "Is this the real life",
        "syncedLyrics": "[00:00.00] Is this the real life",
    }
]


class TestSearchVideo:
    async def test_happy_path(self):
        with patch.object(youtube_client.settings, "youtube_api_key", "fake"):
            with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_response(200, SEARCH_OK))):
                result = await youtube_client.search_video("Bohemian Rhapsody", "Queen")
        assert result.video_id == "fJ9rUzIMcZQ"
        assert result.watch_url == "https://www.youtube.com/watch?v=fJ9rUzIMcZQ"

    async def test_no_results_returns_none_not_an_error(self):
        with patch.object(youtube_client.settings, "youtube_api_key", "fake"):
            with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_response(200, {"items": []}))):
                assert await youtube_client.search_video("zzz", "zzz") is None

    async def test_quota_exceeded_raises_specific_error_type(self):
        with patch.object(youtube_client.settings, "youtube_api_key", "fake"):
            with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_response(403, QUOTA_EXCEEDED))):
                with pytest.raises(youtube_client.YouTubeQuotaExceededError):
                    await youtube_client.search_video("x", "y")

    async def test_missing_api_key_raises_config_error(self):
        with patch.object(youtube_client.settings, "youtube_api_key", ""):
            with pytest.raises(youtube_client.YouTubeConfigError):
                await youtube_client.search_video("x", "y")

    async def test_network_failure_wrapped_in_api_error(self):
        with patch.object(youtube_client.settings, "youtube_api_key", "fake"):
            with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=httpx.ConnectError("boom"))):
                with pytest.raises(youtube_client.YouTubeAPIError):
                    await youtube_client.search_video("x", "y")


class TestGetVideoById:
    async def test_happy_path_handles_non_nested_id_shape(self):
        # videos.list returns id as a plain string, not id.videoId —
        # a real, easy-to-miss difference from search.list's shape.
        with patch.object(youtube_client.settings, "youtube_api_key", "fake"):
            with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_response(200, VIDEOS_OK))):
                result = await youtube_client.get_video_by_id("fJ9rUzIMcZQ")
        assert result.video_id == "fJ9rUzIMcZQ"

    async def test_nonexistent_video_returns_none(self):
        with patch.object(youtube_client.settings, "youtube_api_key", "fake"):
            with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_response(200, {"items": []}))):
                assert await youtube_client.get_video_by_id("deleted123") is None


class TestFetchLyrics:
    async def test_happy_path(self):
        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_response(200, LRCLIB_OK))):
            result = await lrclib_client.fetch_lyrics("Bohemian Rhapsody", "Queen")
        assert result.has_synced_lyrics
        assert result.track_name == "Bohemian Rhapsody"

    async def test_no_results_returns_none(self):
        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_response(200, []))):
            assert await lrclib_client.fetch_lyrics("zzz", "zzz") is None

    async def test_prefers_exact_artist_match_over_first_result(self):
        multi_result = [
            {"id": 1, "trackName": "Song", "artistName": "Wrong Artist", "albumName": "",
             "duration": 100, "instrumental": False, "plainLyrics": "wrong", "syncedLyrics": None},
            {"id": 2, "trackName": "Song", "artistName": "Right Artist", "albumName": "",
             "duration": 100, "instrumental": False, "plainLyrics": "right", "syncedLyrics": None},
        ]
        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_response(200, multi_result))):
            result = await lrclib_client.fetch_lyrics("Song", "Right Artist")
        assert result.plain_lyrics == "right"

    async def test_server_error_raises(self):
        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_response(500, {}))):
            with pytest.raises(lrclib_client.LRCLIBError):
                await lrclib_client.fetch_lyrics("x", "y")
