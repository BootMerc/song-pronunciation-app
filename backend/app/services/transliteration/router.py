"""Dispatches a line of lyrics to the right transliteration module based on
its detected script.

Hebrew, Thai, and Myanmar are detected (language_detect.py knows their
scripts) but have no romanizer wired up here — espeak-ng's output for
all three is genuinely garbled for common words, not just imprecise
(Hebrew: wrong consonants/vowels on common words; Thai: raw tone-number
digits leaking into what should be IPA, e.g. "sa5wmsaɜds" for สวัสดี;
Myanmar: barely resembles the input at all, e.g. "mŋ ɡltspe" for
မင်္ဂလာပါ — confirmed against the raw espeak-ng CLI directly, not a
phonemizer wrapper bug). All three stay in the "unsupported" bucket
until there's a better option, rather than shipping confidently-wrong
pronunciation guidance.
"""

import functools
from collections.abc import Callable

from app.services.language_detect import detect_script
from app.services.transliteration import chinese, espeak_fallback, hindi, icu_scripts, japanese, korean
from app.services.transliteration.base import TransliterationResult, UnsupportedLanguageError

# Languages with no dedicated deterministic library — routed through the
# generic espeak-ng IPA fallback. Checked against real words for
# "plausible, not garbled" output before inclusion — see router history
# for the two (Thai, Myanmar) that failed that check and were removed.
_ESPEAK_FALLBACK_LANGUAGES = [
    "ar", "pa", "bn", "gu", "or", "ta", "te", "kn", "ml", "si", "hy", "ka", "am",
]

_ROMANIZERS: dict[str, Callable[[str], str]] = {
    "ja": japanese.romanize,
    "zh": chinese.romanize,
    "ko": korean.romanize,
    "ru": icu_scripts.romanize_ru,
    "el": icu_scripts.romanize_el,
    "hi": hindi.romanize,
    **{
        code: functools.partial(espeak_fallback.romanize, espeak_language=code)
        for code in _ESPEAK_FALLBACK_LANGUAGES
    },
}

_IPA_LANGUAGES = set(_ESPEAK_FALLBACK_LANGUAGES)  # these produce IPA, not a romanization system


def transliterate_line(line: str) -> TransliterationResult:
    language = detect_script(line)

    if language == "en":
        # Already Latin script — nothing to transliterate.
        return TransliterationResult(original=line, romanized=line, language="en")

    romanize = _ROMANIZERS.get(language)
    if romanize is None:
        raise UnsupportedLanguageError(f"No transliteration module for '{language}' yet.")

    return TransliterationResult(
        original=line,
        romanized=romanize(line),
        language=language,
        kind="ipa" if language in _IPA_LANGUAGES else "romanization",
    )
