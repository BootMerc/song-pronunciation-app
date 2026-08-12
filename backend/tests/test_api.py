"""Endpoint-level integration tests, through the real HTTP layer via
FastAPI's TestClient. /lyrics/manual is tested for real — no external
services involved. /songs/resolve and /songs/from-url mock
youtube_client/lrclib_client at the song_resolver level, since this
sandbox has no network access to the real APIs.
"""

from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.services.lrclib_client import LyricsResult
from app.services.youtube_client import YouTubeVideoResult

client = TestClient(app)

FAKE_VIDEO = YouTubeVideoResult(
    video_id="fJ9rUzIMcZQ",
    title="Queen - Bohemian Rhapsody (Official Video)",
    channel_title="Queen Official",
    thumbnail_url="https://example.com/thumb.jpg",
)
SYNCED_LYRICS = LyricsResult(
    track_name="Bohemian Rhapsody", artist_name="Queen",
    plain_lyrics="愛してる", synced_lyrics="[00:00.00] 愛してる",
)
INSTRUMENTAL = LyricsResult(
    track_name="Some Instrumental", artist_name="Someone",
    plain_lyrics="", synced_lyrics=None, instrumental=True,
)


def _mock_youtube_search(return_value=None, side_effect=None):
    kwargs = {"side_effect": side_effect} if side_effect else {"return_value": return_value}
    return patch("app.services.song_resolver.youtube_client.search_video", new=AsyncMock(**kwargs))


def _mock_lrclib(return_value=None, side_effect=None):
    kwargs = {"side_effect": side_effect} if side_effect else {"return_value": return_value}
    return patch("app.services.song_resolver.lrclib_client.fetch_lyrics", new=AsyncMock(**kwargs))


class TestSongsResolve:
    def test_happy_path_with_synced_lyrics(self):
        with _mock_youtube_search(FAKE_VIDEO), _mock_lrclib(SYNCED_LYRICS):
            resp = client.post("/songs/resolve", json={"title": "Bohemian Rhapsody", "artist": "Queen"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["video"]["video_id"] == "fJ9rUzIMcZQ"
        assert body["synced"] is True
        assert body["lines"][0]["romanized"] == "Aishiteru"

    def test_caching_avoids_a_second_external_call(self):
        with _mock_youtube_search(FAKE_VIDEO) as yt, _mock_lrclib(SYNCED_LYRICS) as lrc:
            client.post("/songs/resolve", json={"title": "Cached Song", "artist": "Cached Artist"})
            client.post("/songs/resolve", json={"title": "Cached Song", "artist": "Cached Artist"})
        assert yt.call_count == 1
        assert lrc.call_count == 1

    def test_video_failure_does_not_prevent_lyrics_from_returning(self):
        with _mock_youtube_search(side_effect=Exception("quota exceeded")), _mock_lrclib(SYNCED_LYRICS):
            resp = client.post("/songs/resolve", json={"title": "Partial Fail", "artist": "Test"})
        body = resp.json()
        assert resp.status_code == 200
        assert body["video"] is None
        assert "quota exceeded" in body["video_error"]
        assert body["lyrics_found"] is True

    def test_lyrics_not_found_returns_flag_not_an_error(self):
        with _mock_youtube_search(FAKE_VIDEO), _mock_lrclib(None):
            resp = client.post("/songs/resolve", json={"title": "Obscure Song", "artist": "Obscure Artist"})
        assert resp.status_code == 200
        assert resp.json()["lyrics_found"] is False
        assert resp.json()["lines"] == []

    def test_instrumental_track_flagged_with_no_lines(self):
        with _mock_youtube_search(FAKE_VIDEO), _mock_lrclib(INSTRUMENTAL):
            resp = client.post("/songs/resolve", json={"title": "Instrumental", "artist": "Someone"})
        body = resp.json()
        assert body["instrumental"] is True
        assert body["lines"] == []

    def test_blank_title_rejected_with_422(self):
        resp = client.post("/songs/resolve", json={"title": "   ", "artist": "Someone"})
        assert resp.status_code == 422

    def test_missing_field_rejected_with_422(self):
        resp = client.post("/songs/resolve", json={"title": "Only Title"})
        assert resp.status_code == 422

    def test_mixed_language_song_degrades_the_one_unsupported_line_only(self):
        mixed = LyricsResult(
            track_name="Mixed", artist_name="Mixed",
            plain_lyrics="愛してる\nאני אוהב אותך", synced_lyrics=None,
        )
        with _mock_youtube_search(None), _mock_lrclib(mixed):
            resp = client.post("/songs/resolve", json={"title": "Mixed", "artist": "Mixed"})
        lines = resp.json()["lines"]
        assert resp.status_code == 200
        assert lines[0]["supported"] is True
        assert lines[1]["supported"] is False


class TestSongsFromUrl:
    def test_invalid_url_rejected_with_422_not_500(self):
        resp = client.post("/songs/from-url", json={"url": "not a youtube link"})
        assert resp.status_code == 422
        assert "youtube" in resp.json()["detail"].lower()

    def test_valid_url_resolves_with_guessed_title_artist(self):
        with patch(
            "app.services.song_resolver.youtube_client.get_video_by_id",
            new=AsyncMock(return_value=FAKE_VIDEO),
        ), _mock_lrclib(SYNCED_LYRICS):
            resp = client.post("/songs/from-url", json={"url": "https://youtu.be/fJ9rUzIMcZQ"})
        body = resp.json()
        assert resp.status_code == 200
        assert body["guessed_title"] == "Bohemian Rhapsody"
        assert body["guessed_artist"] == "Queen"

    def test_video_not_found_rejected_with_422(self):
        with patch(
            "app.services.song_resolver.youtube_client.get_video_by_id",
            new=AsyncMock(return_value=None),
        ):
            resp = client.post("/songs/from-url", json={"url": "https://youtu.be/aaaaaaaaaaa"})
        assert resp.status_code == 422

    def test_blank_url_rejected(self):
        resp = client.post("/songs/from-url", json={"url": "   "})
        assert resp.status_code == 422


class TestLyricsManual:
    def test_real_multi_language_processing_no_mocking_needed(self):
        resp = client.post("/lyrics/manual", json={"lyrics": "愛してる\n我爱你"})
        assert resp.status_code == 200
        lines = resp.json()["lines"]
        assert lines[0]["romanized"] == "Aishiteru"
        assert lines[1]["romanized"] == "wǒ ài nǐ"

    def test_empty_lyrics_returns_empty_lines_not_an_error(self):
        resp = client.post("/lyrics/manual", json={"lyrics": ""})
        assert resp.status_code == 200
        assert resp.json()["lines"] == []

    def test_no_lines_have_timestamps(self):
        resp = client.post("/lyrics/manual", json={"lyrics": "Some lyrics here"})
        assert resp.json()["lines"][0]["timestamp_ms"] is None


class TestLyricsTranslate:
    def test_missing_api_key_returns_503_not_500(self):
        # Translation is optional — a deployment without ANTHROPIC_API_KEY
        # set should get a clear "not configured" response, not a crash.
        with patch("app.services.translation.settings.anthropic_api_key", ""):
            resp = client.post("/lyrics/translate", json={"lines": ["hello"]})
        assert resp.status_code == 503

    def test_happy_path(self):
        claude_response = {"content": [{"type": "text", "text": '["Hello", "World"]'}]}
        with patch("app.services.translation.settings.anthropic_api_key", "fake"), patch(
            "httpx.AsyncClient.post",
            new=AsyncMock(
                return_value=httpx.Response(
                    200, json=claude_response, request=httpx.Request("POST", "https://x.test")
                )
            ),
        ):
            resp = client.post("/lyrics/translate", json={"lines": ["こんにちは", "世界"]})
        assert resp.status_code == 200
        assert resp.json()["translations"] == ["Hello", "World"]

    def test_empty_lines_list_rejected_with_422(self):
        resp = client.post("/lyrics/translate", json={"lines": []})
        assert resp.status_code == 422
