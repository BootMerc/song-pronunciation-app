"""Parses LRC-format synced lyrics (as returned by LRCLIB) into
(timestamp_ms, line_text) pairs.

LRC files mix timed lyric lines ([00:12.34]text) with metadata tags
([ar:Artist], [ti:Title], [length:03:45]) that use the same bracket
syntax but hold letters instead of a digit-colon-digit timestamp — the
regex naturally skips those without special-casing them.
"""

import re

_LRC_LINE = re.compile(r"^\[(\d+):(\d+(?:\.\d+)?)\](.*)$")


def parse_lrc(lrc_text: str) -> list[tuple[int | None, str]]:
    lines: list[tuple[int | None, str]] = []
    for raw_line in lrc_text.splitlines():
        match = _LRC_LINE.match(raw_line.strip())
        if match is None:
            continue  # metadata tag or malformed line — skip
        minutes, seconds, text = match.groups()
        timestamp_ms = int((int(minutes) * 60 + float(seconds)) * 1000)
        lines.append((timestamp_ms, text.strip()))
    return lines
