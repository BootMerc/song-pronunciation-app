"""Mandarin romanization via pypinyin (tone-marked pinyin, phrase-dictionary
disambiguation for polyphonic characters, e.g. 长城 -> "cháng chéng" not
"zhǎng chéng").

pypinyin tokenizes per-character, including punctuation and any
already-Latin text passed through unchanged, so the naive space-joined
output needs cleanup: it otherwise leaves double spaces around existing
whitespace and a stray space before punctuation.
"""

import re

from pypinyin import Style, pinyin

_SPACE_BEFORE_PUNCTUATION = re.compile(r"\s+([,.!?;:、。！？；：])")
_MULTIPLE_SPACES = re.compile(r"\s+")


def romanize(line: str) -> str:
    syllables = pinyin(line, style=Style.TONE, heteronym=False)
    text = " ".join(chunk[0] for chunk in syllables)
    text = _MULTIPLE_SPACES.sub(" ", text)
    text = _SPACE_BEFORE_PUNCTUATION.sub(r"\1", text)
    return text.strip()
