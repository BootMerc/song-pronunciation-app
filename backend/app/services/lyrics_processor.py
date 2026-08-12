"""Turns raw lyrics text (from LRCLIB or pasted by hand) into a list of
fully processed LyricLine entries — the shared pipeline behind both
/songs/resolve and /lyrics/manual.

A line in an unsupported language (e.g. Hebrew) doesn't fail the whole
request — it comes back with supported=False and the original text
standing in for romanized/friendly, so the rest of the song's lines still
render normally and the frontend can flag just that one line.
"""

from app.models.schemas import LyricLine
from app.services.language_detect import detect_script
from app.services.lrc_parser import parse_lrc
from app.services.respelling.router import respell_result
from app.services.transliteration.base import UnsupportedLanguageError
from app.services.transliteration.router import transliterate_line


def _process_line(original: str, timestamp_ms: int | None) -> LyricLine:
    try:
        result = transliterate_line(original)
        return LyricLine(
            original=original,
            romanized=result.romanized,
            friendly=respell_result(result),
            language=result.language,
            timestamp_ms=timestamp_ms,
            supported=True,
        )
    except UnsupportedLanguageError:
        return LyricLine(
            original=original,
            romanized=original,
            friendly=original,
            language=detect_script(original),
            timestamp_ms=timestamp_ms,
            supported=False,
        )


def process_synced_lyrics(lrc_text: str) -> list[LyricLine]:
    return [_process_line(text, ts) for ts, text in parse_lrc(lrc_text)]


def process_plain_lyrics(plain_text: str) -> list[LyricLine]:
    return [_process_line(line, None) for line in plain_text.splitlines()]
