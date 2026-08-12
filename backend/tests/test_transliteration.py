import pytest

from app.services.transliteration.base import UnsupportedLanguageError
from app.services.transliteration.router import transliterate_line


def test_japanese_matches_spec_example():
    result = transliterate_line("愛してる")
    assert result.language == "ja"
    assert result.romanized == "Aishiteru"
    assert result.kind == "romanization"


def test_japanese_loanword_uses_phonetic_not_english_spelling():
    # Regression test for a real bug: cutlet's default reconstructs the
    # English source word ("Computer") instead of the sung phonetics
    # ("Konpyuutaa") — actively misleading for a pronunciation app.
    result = transliterate_line("コンピューター")
    assert result.romanized == "Konpyuutaa"
    assert "Computer" not in result.romanized


def test_japanese_honorific_kinship_terms_use_correct_reading():
    # Regression test: unidic-lite's dictionary gives these the wrong
    # (standalone-kanji) reading without the targeted hiragana fix.
    assert transliterate_line("お母さん").romanized == "Okaasan"
    assert transliterate_line("お父さん").romanized == "Otousan"
    assert transliterate_line("お兄さん").romanized == "Oniisan"
    assert transliterate_line("お姉さん").romanized == "Oneesan"


def test_chinese():
    result = transliterate_line("我爱你")
    assert result.language == "zh"
    assert result.romanized == "wǒ ài nǐ"


def test_chinese_polyphonic_character_disambiguated():
    # 长 alone can be cháng or zhǎng; in 长城 it must resolve to cháng.
    assert transliterate_line("长城").romanized == "cháng chéng"


def test_korean():
    result = transliterate_line("나는 너를 사랑해")
    assert result.language == "ko"
    assert result.romanized == "naneun neoreul saranghae"


def test_russian():
    result = transliterate_line("Я тебя люблю")
    assert result.language == "ru"
    assert result.romanized == "YA tebya lyublyu"


def test_greek_digraph_handled_correctly():
    # The alternative pure-Python `transliterate` package got this
    # specific case wrong (σου -> "soy" instead of "sou") — this is why
    # PyICU was chosen instead. See icu_scripts.py.
    result = transliterate_line("Σ'αγαπώ")
    assert result.language == "el"
    assert "soy" not in result.romanized.lower()


def test_hindi():
    result = transliterate_line("मैं तुमसे प्यार करता हूँ")
    assert result.language == "hi"
    assert result.romanized == "maiṃ tumase pyāra karatā hū~"


def test_arabic_is_ipa_not_romanization():
    result = transliterate_line("أحبك")
    assert result.language == "ar"
    assert result.kind == "ipa"
    assert result.romanized == "ʔaħabːka"


def test_english_passthrough_identity():
    result = transliterate_line("Hello world")
    assert result.language == "en"
    assert result.romanized == "Hello world"
    assert result.kind == "romanization"


def test_hebrew_raises_rather_than_producing_wrong_output():
    # Deliberate: espeak-ng's Hebrew voice gives outright wrong output
    # for common words (not just missing vowels, which would be
    # expected) — see espeak_fallback.py's docstring. Router must
    # refuse, not silently mangle.
    with pytest.raises(UnsupportedLanguageError):
        transliterate_line("אני אוהב אותך")


def test_punjabi_no_longer_falls_through_as_unchanged_english():
    # Regression test for a real bug report: Gurmukhi script wasn't in
    # the detection table at all, so it silently matched the "already
    # English" fallback and came back completely unchanged — looked
    # exactly like nothing had happened.
    result = transliterate_line("ਪਿਆਰ")
    assert result.language == "pa"
    assert result.romanized != result.original
    assert result.romanized == "pɪaɾ"


def test_bengali():
    result = transliterate_line("নমস্কার")
    assert result.language == "bn"
    assert result.romanized == "nɔmɔʃkaɾ"


def test_tamil_retroflex_consonant():
    result = transliterate_line("வணக்கம்")
    assert result.language == "ta"
    assert "ɳ" in result.romanized  # retroflex n, a real Tamil phoneme


def test_georgian():
    result = transliterate_line("გამარჯობა")
    assert result.language == "ka"
    assert result.romanized == "ɡamardʒoba"


def test_thai_excluded_despite_having_a_script_range():
    # Thai script IS detected (language_detect.py knows it), but no
    # romanizer is wired up: espeak-ng leaks raw tone-number digits into
    # what should be IPA (e.g. "sa5wmsaɜds"), confirmed against the raw
    # CLI directly, not a phonemizer bug. Same principle as Hebrew.
    with pytest.raises(UnsupportedLanguageError):
        transliterate_line("สวัสดี")


def test_myanmar_excluded_despite_having_a_script_range():
    # Same situation as Thai — output barely resembles the input.
    with pytest.raises(UnsupportedLanguageError):
        transliterate_line("မင်္ဂလာပါ")


def test_empty_line_does_not_crash():
    result = transliterate_line("")
    assert result.romanized == ""
