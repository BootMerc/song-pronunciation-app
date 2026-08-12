"""Orchestrates a full song lookup: YouTube (for playback) and LRCLIB
(for lyrics) run concurrently via asyncio.gather, and each one's failure
is handled independently — a YouTube quota error doesn't prevent lyrics
from coming back, and an LRCLIB miss doesn't prevent the video from
showing. Transient errors (quota, network) are never cached, so a bad
result doesn't get stuck for the full 30-day TTL; "no lyrics exist for
this song" is treated as a stable, cacheable fact.

Also handles resolving from a pasted YouTube URL: fetches real video
metadata cheaply (1 quota unit via videos.list, vs. 100 for a search),
then guesses a title/artist from it to feed the same lyrics pipeline —
inherently best-effort, so the guess travels with the response for the
frontend to show and let the user correct.

Note: search history is tracked client-side (localStorage), not here —
see frontend/src/lib/history.js. Render's free tier has no persistent
disk, so server-side SQLite history would reset far too often (every
15-minute idle spin-down) to be useful once actually deployed.
"""

import asyncio

from app.models.schemas import SongResolveResponse
from app.services import cache, lrclib_client, youtube_client
from app.services.lyrics_processor import process_plain_lyrics, process_synced_lyrics
from app.services.title_guess import guess_title_artist
from app.services.youtube_url import extract_video_id


class InvalidYouTubeURLError(Exception):
    """Raised when a pasted URL isn't a recognizable YouTube link."""


def _build_lyrics_response(
    video, video_error, video_had_error, lyrics_outcome, lyrics_had_error
) -> SongResolveResponse:
    if lyrics_had_error:
        return SongResolveResponse(
            video=video, video_error=video_error,
            lyrics_found=False, lyrics_error=str(lyrics_outcome),
        )
    if lyrics_outcome is None:
        return SongResolveResponse(video=video, video_error=video_error, lyrics_found=False)
    if lyrics_outcome.instrumental:
        return SongResolveResponse(
            video=video, video_error=video_error, lyrics_found=True, instrumental=True,
        )
    if lyrics_outcome.has_synced_lyrics:
        return SongResolveResponse(
            video=video, video_error=video_error, lyrics_found=True, synced=True,
            lines=process_synced_lyrics(lyrics_outcome.synced_lyrics),
        )
    if lyrics_outcome.plain_lyrics:
        return SongResolveResponse(
            video=video, video_error=video_error, lyrics_found=True, synced=False,
            lines=process_plain_lyrics(lyrics_outcome.plain_lyrics),
        )
    return SongResolveResponse(video=video, video_error=video_error, lyrics_found=False)


async def resolve_song(title: str, artist: str) -> SongResolveResponse:
    cache_key = cache.make_key(title, artist)
    cached = await asyncio.to_thread(cache.get, cache_key)
    if cached is not None:
        return SongResolveResponse.model_validate(cached)

    video_outcome, lyrics_outcome = await asyncio.gather(
        youtube_client.search_video(title, artist),
        lrclib_client.fetch_lyrics(title, artist),
        return_exceptions=True,
    )

    video_had_error = isinstance(video_outcome, Exception)
    video_error = str(video_outcome) if video_had_error else None
    video = None if video_had_error else video_outcome
    lyrics_had_error = isinstance(lyrics_outcome, Exception)

    response = _build_lyrics_response(
        video, video_error, video_had_error, lyrics_outcome, lyrics_had_error
    )

    if not video_had_error and not lyrics_had_error:
        await asyncio.to_thread(cache.set, cache_key, response.model_dump())

    return response


async def resolve_song_from_url(url: str) -> SongResolveResponse:
    video_id = extract_video_id(url)
    if video_id is None:
        raise InvalidYouTubeURLError(
            "That doesn't look like a YouTube link — expected something like "
            "youtube.com/watch?v=... or youtu.be/..."
        )

    try:
        video = await youtube_client.get_video_by_id(video_id)
    except youtube_client.YouTubeAPIError as exc:
        raise InvalidYouTubeURLError(f"Couldn't look up that video: {exc}") from exc

    if video is None:
        raise InvalidYouTubeURLError(
            "Couldn't find that video — it may be private, deleted, or region-locked."
        )

    guessed_title, guessed_artist = guess_title_artist(video.title, video.channel_title)

    cache_key = cache.make_key(guessed_title, guessed_artist)
    cached = await asyncio.to_thread(cache.get, cache_key)
    if cached is not None:
        response = SongResolveResponse.model_validate(cached)
        response.guessed_title = guessed_title
        response.guessed_artist = guessed_artist
        return response

    lyrics_outcome = await lrclib_client.fetch_lyrics(guessed_title, guessed_artist)
    lyrics_had_error = isinstance(lyrics_outcome, Exception)

    response = _build_lyrics_response(
        video, None, False, lyrics_outcome, lyrics_had_error
    )
    response.guessed_title = guessed_title
    response.guessed_artist = guessed_artist

    if not lyrics_had_error:
        await asyncio.to_thread(cache.set, cache_key, response.model_dump())

    return response
