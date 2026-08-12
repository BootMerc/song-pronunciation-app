"""Hindi romanization via indic-transliteration, using IAST (the standard
scholarly romanization for Devanagari — the same system used for Sanskrit).
"""

from indic_transliteration import sanscript


def romanize(line: str) -> str:
    return sanscript.transliterate(line, sanscript.DEVANAGARI, sanscript.IAST)
