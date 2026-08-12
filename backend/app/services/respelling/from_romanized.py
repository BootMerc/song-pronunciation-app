"""Converts an already-romanized string (Hepburn romaji, Hanyu pinyin,
Revised Romanization, ICU Russian/Greek, or IAST) into an English-friendly
respelling. Every rule here exists because testing showed it was needed —
see Step 4 build notes for the actual before/after examples.

Effort is uneven across languages on purpose: Japanese Hepburn and Korean
Revised Romanization were already designed to be readable by English
speakers, so they need only small fixes. Pinyin's initials (q/x/c/z) and
ICU's classical Greek convention need real correction — without it,
they'd actively mislead rather than just be slightly awkward.
"""

import re
import unicodedata

# ---------------------------------------------------------------- Chinese
# pypinyin's tone marks and the ü umlaut are separate concerns: tones are
# stripped (singing follows the tune, not lexical tone — the tone-marked
# form is still available from the standard-romanization step for anyone
# who wants it), but ü must become "yu" rather than collapsing to plain
# "u", since lü and lu are genuinely different syllables.
_PINYIN_TONE_STRIP = {
    "ā": "a", "á": "a", "ǎ": "a", "à": "a",
    "ē": "e", "é": "e", "ě": "e", "è": "e",
    "ī": "i", "í": "i", "ǐ": "i", "ì": "i",
    "ō": "o", "ó": "o", "ǒ": "o", "ò": "o",
    "ū": "u", "ú": "u", "ǔ": "u", "ù": "u",
    "ǖ": "ü", "ǘ": "ü", "ǚ": "ü", "ǜ": "ü",
}
_PINYIN_DIGRAPHS = {"zh": "j", "ch": "ch", "sh": "sh"}
_PINYIN_SINGLES = {"q": "ch", "x": "sh", "c": "ts", "z": "dz", "ü": "yu"}


def _respell_chinese(romanized: str) -> str:
    text = "".join(_PINYIN_TONE_STRIP.get(ch, ch) for ch in romanized)
    result = []
    i = 0
    while i < len(text):
        two = text[i : i + 2]
        if two in _PINYIN_DIGRAPHS:
            result.append(_PINYIN_DIGRAPHS[two])
            i += 2
            continue
        result.append(_PINYIN_SINGLES.get(text[i], text[i]))
        i += 1
    return "".join(result)
    # Known gap: after j/q/x/y, a plain written "u" is pronounced ü (this
    # is a pinyin orthographic convention — no dots are written there
    # since j/q/x/y never combine with true "u" anyway). E.g. qù -> "chu"
    # here, though the vowel is really ü. Handling this correctly needs
    # syllable-aware parsing, not character substitution; documented as a
    # known limitation rather than solved.


# ------------------------------------------------------------------ Greek
# Two independent fixes: (1) ICU marks vowel length with macrons (η→ē,
# ω→ō) per Ancient Greek's now-lost length distinction — modern Greek
# doesn't have it, so it's just visual noise for this purpose. (2) ICU's
# αυ/ευ -> "au"/"eu" follows classical convention; modern speech is
# "av"/"ev" before a vowel or voiced consonant, "af"/"ef" before a
# voiceless one. Order matters: strip accents/macrons first, since the
# voicing check runs on plain ASCII letters.
_VOICELESS_LOOKAHEAD = r"(?:th|ch|ps|[kptfxs])"
_VOICING_PATTERN = re.compile(r"(au|eu)(?=" + _VOICELESS_LOOKAHEAD + r")", re.IGNORECASE)


def _strip_diacritics(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def _respell_greek(romanized: str) -> str:
    text = _strip_diacritics(romanized)
    text = _VOICING_PATTERN.sub(lambda m: "af" if m.group(1)[0] == "a" else "ef", text)
    text = re.sub(r"au", "av", text, flags=re.IGNORECASE)
    text = re.sub(r"eu", "ev", text, flags=re.IGNORECASE)
    return text


# ------------------------------------------------------------------ Hindi
# IAST diacritics aren't typable or obvious to someone without Sanskrit
# background; flatten to plain letters. Longest keys first so "r̥" isn't
# partially matched by some other single-character rule first.
_IAST_MAP = {
    "ā": "aa", "ī": "ee", "ū": "oo",
    "ṅ": "ng", "ñ": "ny", "ṇ": "n", "ṃ": "n", "~": "n",
    "ṭ": "t", "ḍ": "d", "ḥ": "h",
    "ś": "sh", "ṣ": "sh",
    "r̥": "ri",
}


def _respell_hindi(romanized: str) -> str:
    for old, new in sorted(_IAST_MAP.items(), key=lambda kv: -len(kv[0])):
        romanized = romanized.replace(old, new)
    return romanized


# ----------------------------------------------------------------- Korean
# "eo" is a single vowel (~ "uh" in but), not "e" then "o" — read
# literally it looks like it might be two syllables. "eu" (~ unrounded
# "oo") has no reasonable English spelling and is left as-is.
def _respell_korean(romanized: str) -> str:
    return re.sub(r"eo", "uh", romanized)


# -------------------------------------------------- Japanese / Russian
# Hepburn romaji and ICU's Russian/BGN system were both designed to be
# readable by English speakers already; no correction found to be needed
# during testing, so these pass through unchanged.
def _respell_japanese(romanized: str) -> str:
    return romanized


def _respell_russian(romanized: str) -> str:
    return romanized


_RESPELLERS = {
    "ja": _respell_japanese,
    "zh": _respell_chinese,
    "ko": _respell_korean,
    "ru": _respell_russian,
    "el": _respell_greek,
    "hi": _respell_hindi,
}


def respell(romanized: str, language: str) -> str:
    respeller = _RESPELLERS.get(language)
    if respeller is None:
        return romanized  # no rules for this language yet — pass through, don't guess
    return respeller(romanized)
