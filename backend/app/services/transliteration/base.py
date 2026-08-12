from typing import Literal

from pydantic import BaseModel


class TransliterationResult(BaseModel):
    original: str
    romanized: str
    language: str
    kind: Literal["romanization", "ipa"] = "romanization"


class UnsupportedLanguageError(Exception):
    """Raised when the router has no transliteration module for a detected language yet."""
