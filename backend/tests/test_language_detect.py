from app.services.language_detect import detect_script


def test_japanese_detected_via_kana():
    assert detect_script("愛してる") == "ja"


def test_japanese_kana_wins_over_kanji_when_both_present():
    # 愛してる has both kanji (愛) and kana (してる) — kana presence
    # should decide it's Japanese, not fall through to the Chinese branch.
    assert detect_script("私は猫が好きです") == "ja"


def test_chinese_detected_via_bare_kanji_no_kana():
    assert detect_script("我爱你") == "zh"


def test_korean():
    assert detect_script("나는 너를 사랑해") == "ko"


def test_russian():
    assert detect_script("Я тебя люблю") == "ru"


def test_greek():
    assert detect_script("Σ'αγαπώ") == "el"


def test_hindi():
    assert detect_script("मैं तुमसे प्यार करता हूँ") == "hi"


def test_arabic():
    assert detect_script("أحبك") == "ar"


def test_hebrew_detected_as_script_even_though_unsupported_downstream():
    # detect_script only identifies the script; whether there's a
    # transliteration module for it is the router's concern, not this
    # function's — see test_transliteration.py for the actual rejection.
    assert detect_script("אני אוהב אותך") == "he"


def test_punjabi_gurmukhi():
    # Regression: this script was entirely missing from the detection
    # table — silently fell through to "en" and came back unchanged.
    assert detect_script("ਪਿਆਰ") == "pa"


def test_bengali():
    assert detect_script("নমস্কার") == "bn"


def test_tamil():
    assert detect_script("வணக்கம்") == "ta"


def test_thai_and_myanmar_are_still_detected_as_scripts():
    # These have no romanizer wired up (see test_transliteration.py) but
    # should still be correctly identified, not misdetected as English —
    # the router is what refuses to guess at pronunciation, not this.
    assert detect_script("สวัสดี") == "th"
    assert detect_script("မင်္ဂလာပါ") == "my"


def test_english_passthrough():
    assert detect_script("Hello world") == "en"


def test_empty_string_is_english():
    assert detect_script("") == "en"


def test_punctuation_and_numbers_only_is_english():
    assert detect_script("123 !?.,") == "en"


def test_latin_with_diacritics_still_english():
    # French/Spanish/etc. accented Latin text has no dedicated script
    # bucket — falls through to "en" (no transliteration needed, it's
    # already Latin script).
    assert detect_script("café à la carte") == "en"


def test_mixed_foreign_scripts_picks_the_dominant_one():
    # Contrived, but the function needs a defined behavior for it:
    # whichever script has more characters wins.
    assert detect_script("aaa Привет Привет") == "ru"
