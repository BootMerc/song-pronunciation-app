"""Manual smoke test for the YouTube + LRCLIB clients.

This is NOT the test suite (that's Phase 6, with mocked responses). This
script hits the real APIs so you can confirm your YouTube API key works
and see what an actual lookup returns end to end.

Usage (from the backend/ directory, with .env configured):
    python -m scripts.smoke_test "Bohemian Rhapsody" "Queen"
"""

import asyncio
import sys

from app.services import lrclib_client, youtube_client


async def main(title: str, artist: str) -> None:
    print(f"Looking up: {title} - {artist}\n")

    print("YouTube:")
    try:
        video = await youtube_client.search_video(title, artist)
        if video:
            print(f"  {video.title} ({video.channel_title})")
            print(f"  {video.watch_url}")
        else:
            print("  No match found.")
    except youtube_client.YouTubeConfigError as exc:
        print(f"  Not configured: {exc}")
    except youtube_client.YouTubeAPIError as exc:
        print(f"  API error: {exc}")

    print("\nLRCLIB:")
    try:
        lyrics = await lrclib_client.fetch_lyrics(title, artist)
        if lyrics:
            kind = "synced" if lyrics.has_synced_lyrics else "plain only"
            text = lyrics.synced_lyrics or lyrics.plain_lyrics or ""
            print(f"  Found ({kind}), {len(text.splitlines())} lines")
        else:
            print("  No lyrics found - manual paste would kick in here.")
    except lrclib_client.LRCLIBError as exc:
        print(f"  API error: {exc}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('Usage: python -m scripts.smoke_test "<title>" "<artist>"')
        raise SystemExit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
