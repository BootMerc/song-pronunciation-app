"""Guesses (title, artist) from a YouTube video's title and channel name.

Inherently best-effort — YouTube has no structured "artist" field, only
a free-text title and a channel name. This exists so pasting a link can
skip straight to a lyrics lookup in the common case ("Artist - Title"
titles), while staying wrong often enough that the guess must stay
visible and editable, never presented as certain.
"""

import re

_NOISE = re.compile(
    r"""
    \s*[\(\[]
    (?:official\s*(?:music\s*)?video|official\s*audio|official\s*lyric\s*video|
       official|lyric\s*video|lyrics?|audio|visualizer|hd|4k|remastered)
    [\)\]]\s*
    |
    \s*(?:official\s*(?:music\s*)?video|official\s*audio|official\s*lyric\s*video|
        lyric\s*video|MV)\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)
_PIPE_SUFFIX = re.compile(r"\s*\|\s*official.*$", re.IGNORECASE)
_SEPARATORS = (" - ", " – ", " — ", " : ")
_CHANNEL_SUFFIX = re.compile(
    r"\s*-?\s*(?:official|vevo|music|records|topic)\s*$", re.IGNORECASE
)
# Japanese titles commonly use corner brackets instead of a dash:
# "ArtistName「Song Title」suffix"
_CORNER_BRACKETS = re.compile(r"^(.*?)「(.+?)」")


def guess_title_artist(video_title: str, channel_title: str) -> tuple[str, str]:
    """Returns (guessed_title, guessed_artist)."""
    cleaned = _NOISE.sub("", _PIPE_SUFFIX.sub("", video_title)).strip()

    bracket_match = _CORNER_BRACKETS.match(cleaned)
    if bracket_match:
        artist_part, title_part = bracket_match.groups()
        artist_part = artist_part.strip()
        if artist_part:
            return title_part.strip(), artist_part

    for sep in _SEPARATORS:
        if sep in cleaned:
            left, right = cleaned.split(sep, 1)
            left, right = left.strip(), right.strip()
            if left and right:
                return right, left  # convention: "Artist - Title"

    # No separator found — fall back to the channel name as the artist
    # guess, stripping common channel-branding suffixes.
    artist_guess = _CHANNEL_SUFFIX.sub("", channel_title).strip()
    return cleaned, artist_guess or channel_title
