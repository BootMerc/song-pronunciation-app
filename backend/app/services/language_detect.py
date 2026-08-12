"""Script-based language detection for routing lyrics to the right transliterator.

The question this app actually needs answered isn't "what language is
this" in the general sense — it's "which transliteration module should
handle this line", and that's a script question, not a statistical one.
Counting Unicode code points is dependency-free and more reliable here
than a general-purpose language-ID model, which is tuned for longer,
more conventional prose than short, repetitive song lyrics.

Codes below match espeak-ng's own language codes wherever a script maps
to an espeak-fallback language (see transliteration/espeak_fallback.py)
— lets the router pass the detected code straight through with no
separate lookup table.

Known limitations:
- Japanese written entirely in Kanji with no Hiragana or Katakana is
  indistinguishable from Chinese by script alone (rare in real lyrics,
  see docstring below for the mitigation already in place).
- Devanagari is shared by Hindi, Nepali, and Marathi — all route to "hi"
  and the same IAST-based transliteration, which is a reasonable
  approximation across that family but isn't language-specific tuning.
- Arabic-derived scripts (Arabic, Urdu, Persian, Sindhi) overlap
  significantly in Unicode — only Arabic is disambiguated (via its own
  script range); Urdu/Persian/Sindhi text mostly falls into the same
  bucket and gets Arabic phonology applied, which is imprecise for those
  languages specifically. Not fixed here — genuine script-level
  disambiguation between these needs more than Unicode ranges.
"""

_SCRIPT_RANGES: dict[str, list[tuple[int, int]]] = {
    "ja": [(0x3040, 0x309F), (0x30A0, 0x30FF)],  # Hiragana, Katakana
    "zh": [(0x4E00, 0x9FFF)],  # CJK Unified Ideographs
    "ko": [(0xAC00, 0xD7A3)],  # Hangul Syllables
    "ru": [(0x0400, 0x04FF)],  # Cyrillic
    "el": [(0x0370, 0x03FF)],  # Greek
    "hi": [(0x0900, 0x097F)],  # Devanagari (Hindi, Nepali, Marathi)
    "ar": [(0x0600, 0x06FF)],  # Arabic
    "he": [(0x0590, 0x05FF)],  # Hebrew
    # Added after a real bug report: a Punjabi song (Gurmukhi script)
    # wasn't recognized at all, silently fell through to the "already
    # English" passthrough, and came back completely unchanged.
    "pa": [(0x0A00, 0x0A7F)],  # Gurmukhi (Punjabi)
    "bn": [(0x0980, 0x09FF)],  # Bengali
    "gu": [(0x0A80, 0x0AFF)],  # Gujarati
    "or": [(0x0B00, 0x0B7F)],  # Odia
    "ta": [(0x0B80, 0x0BFF)],  # Tamil
    "te": [(0x0C00, 0x0C7F)],  # Telugu
    "kn": [(0x0C80, 0x0CFF)],  # Kannada
    "ml": [(0x0D00, 0x0D7F)],  # Malayalam
    "si": [(0x0D80, 0x0DFF)],  # Sinhala
    "th": [(0x0E00, 0x0E7F)],  # Thai
    "my": [(0x1000, 0x109F)],  # Myanmar (Burmese)
    "hy": [(0x0530, 0x058F)],  # Armenian
    "ka": [(0x10A0, 0x10FF)],  # Georgian
    "am": [(0x1200, 0x137F)],  # Amharic (Ethiopic)
}


def detect_script(text: str) -> str:
    """Return a language code for the dominant non-Latin script in `text`.

    Returns "en" if no recognized non-Latin script is present — i.e. the
    text is already in Latin script and needs no transliteration.
    """
    counts = {code: 0 for code in _SCRIPT_RANGES}

    for char in text:
        codepoint = ord(char)
        for code, ranges in _SCRIPT_RANGES.items():
            if any(start <= codepoint <= end for start, end in ranges):
                counts[code] += 1
                break  # ranges don't overlap; a char matches at most one

    if counts["ja"] > 0:
        return "ja"  # kana presence beats kanji-only "zh" match, see docstring

    remaining = {code: n for code, n in counts.items() if code != "ja"}
    best_code, best_count = max(remaining.items(), key=lambda kv: kv[1])
    return best_code if best_count > 0 else "en"
