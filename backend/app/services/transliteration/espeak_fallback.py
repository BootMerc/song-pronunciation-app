"""Generic espeak-ng-backed IPA fallback, for any language with no
dedicated deterministic transliteration module.

Started as arabic.py (Arabic only) and got generalized after finding
espeak-ng actually has 132 voices installed — Arabic was never a special
case, just the first one wired up. See router.py for which language
codes route here and why (mostly: languages whose everyday script omits
enough phonetic information — short vowels, tone, etc — that there's no
standard "romanization system" to fall back on the way there is for
Japanese/Chinese/Korean, so IPA via a real phonetic engine is the best
available option).

Quality varies by language and hasn't been checked with the same depth
for all of them — Arabic and Hebrew got real linguistic scrutiny (see
Hebrew's exclusion below); the other 14 were checked for "does this look
like plausible phonetic output, not obviously garbled" rather than
verified against known-correct pronunciations the way Japanese/Chinese/
Korean/Russian/Greek/Hindi were. If a language here gives clearly wrong
output for common words the way Hebrew did, it should come out of
router.py's mapping, the same way Hebrew was kept out.
"""

from phonemizer import phonemize


def romanize(line: str, espeak_language: str) -> str:
    if not line.strip():
        return ""
    return phonemize(line, language=espeak_language, backend="espeak", strip=True)
