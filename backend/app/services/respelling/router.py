"""Single entry point for respelling: dispatches to from_ipa or
from_romanized based on what kind of text the transliteration step
produced (see transliteration/base.py's TransliterationResult.kind).
"""

from app.services.respelling import from_ipa, from_romanized
from app.services.transliteration.base import TransliterationResult


def respell_result(result: TransliterationResult) -> str:
    if result.language == "en":
        return result.romanized  # already English, nothing to respell

    if result.kind == "ipa":
        return from_ipa.respell(result.romanized)

    return from_romanized.respell(result.romanized, result.language)
