from unittest.mock import patch

from app.services.respelling import from_ipa, from_romanized
from app.services.respelling.router import respell_result
from app.services.transliteration.router import transliterate_line


class TestFromIpa:
    def test_arabic_love_you(self):
        assert from_ipa.respell("ʔaħabːka") == "'aHabbka"

    def test_gemination_after_consonant_not_leaked_as_raw_ipa(self):
        # Regression: the length mark can follow a consonant (gemination)
        # rather than only a vowel — the first version of this function
        # leaked a literal "ː" character into the output for this case.
        result = from_ipa.respell("ʔaħabːka")
        assert "ː" not in result

    def test_no_english_equivalent_sounds_get_distinct_markers_not_silently_mapped(self):
        # ʕ (ayn) and ħ must not collapse into an unmarked regular letter
        # that would suggest an ordinary English sound.
        assert from_ipa.respell("ʕarabiːj") == "'arabeey"
        assert from_ipa.respell("mrħbaː") == "mrHbaa"

    def test_affricate_digraph(self):
        assert from_ipa.respell("dʒamiːl") == "jameel"

    def test_aspiration_appends_h_the_conventional_way(self):
        # ʰ modifies the preceding consonant rather than standing alone —
        # "kh"/"jh" etc. is how English already conventionally spells
        # aspirated Indic consonants (Bhagavad Gita, Dharma).
        assert from_ipa.respell("kʰ") == "kh"
        assert from_ipa.respell("ɟʰ") == "jh"

    def test_nasalization_appends_trailing_n(self):
        assert from_ipa.respell("tũ") == "tun"

    def test_retroflex_and_tap_consonants_simplified_to_plain_letters(self):
        assert from_ipa.respell("ɳ") == "n"
        assert from_ipa.respell("ɾ") == "r"
        assert from_ipa.respell("ɹ") == "r"

    def test_full_punjabi_line_from_the_bug_report(self):
        assert from_ipa.respell("nivɪã tũ kʊɟʰ cɪɾ pa ke ɾʌkʰ lɛ") == "nivian tun koojh chir pa ke rukh le"

    def test_empty_string(self):
        assert from_ipa.respell("") == ""


class TestFromRomanized:
    def test_chinese_initials_corrected(self):
        # q/x/c/z/zh don't sound like their English letters at all —
        # this is the core reason this layer exists for Chinese.
        assert from_romanized.respell("qǐng", "zh") == "ching"
        assert from_romanized.respell("xiè xie", "zh") == "shie shie"
        assert from_romanized.respell("zhōngguó", "zh") == "jongguo"

    def test_chinese_ch_sh_not_double_processed(self):
        # Regression: a naive char-by-char pass after the digraph pass
        # would re-match the 'c' inside an already-correct "ch".
        assert from_romanized.respell("chī fàn", "zh") == "chi fan"

    def test_chinese_tone_marks_stripped(self):
        assert "ǒ" not in from_romanized.respell("wǒ ài nǐ", "zh")

    def test_greek_voicing_fixed_ev_before_voiced(self):
        assert from_romanized.respell("aúrio", "el") == "avrio"

    def test_greek_voicing_fixed_ef_before_voiceless(self):
        assert from_romanized.respell("eucharistṓ", "el") == "efcharisto"

    def test_hindi_diacritics_flattened(self):
        result = from_romanized.respell("maiṃ tumase pyāra karatā hū~", "hi")
        assert result == "main tumase pyaara karataa hoon"

    def test_korean_eo_disambiguated(self):
        assert from_romanized.respell("neoreul", "ko") == "nuhreul"

    def test_korean_eu_left_alone(self):
        # No good English spelling exists for this vowel — deliberately
        # not "fixed" into something equally wrong.
        assert from_romanized.respell("eumak", "ko") == "eumak"

    def test_japanese_passthrough(self):
        assert from_romanized.respell("Aishiteru", "ja") == "Aishiteru"

    def test_russian_passthrough(self):
        assert from_romanized.respell("Privet mir", "ru") == "Privet mir"

    def test_unknown_language_passes_through_rather_than_guessing(self):
        assert from_romanized.respell("something", "xx") == "something"


class TestRespellResultRouter:
    def test_ipa_kind_dispatches_to_from_ipa_not_from_romanized(self):
        result = transliterate_line("أحبك")
        assert result.kind == "ipa"
        with patch(
            "app.services.respelling.router.from_ipa.respell",
            wraps=from_ipa.respell,
        ) as ipa_spy, patch(
            "app.services.respelling.router.from_romanized.respell",
            wraps=from_romanized.respell,
        ) as romanized_spy:
            respell_result(result)
            assert ipa_spy.called
            assert not romanized_spy.called

    def test_romanization_kind_dispatches_to_from_romanized_with_correct_language(self):
        result = transliterate_line("Σ'αγαπώ")
        assert result.kind == "romanization"
        with patch(
            "app.services.respelling.router.from_romanized.respell",
            wraps=from_romanized.respell,
        ) as romanized_spy:
            respell_result(result)
            romanized_spy.assert_called_once_with(result.romanized, "el")

    def test_english_passthrough_skips_respelling_entirely(self):
        result = transliterate_line("Hello world")
        assert respell_result(result) == "Hello world"
