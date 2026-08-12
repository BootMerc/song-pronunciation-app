"""Converts IPA (espeak-ng's output for Arabic and 10 other languages
with no dedicated romanization system — see transliteration/router.py)
into an English-friendly phonetic respelling.

The symbol table below was built from actually inspecting espeak-ng's
real output, not from IPA theory — it caught real surprises, e.g. the
Arabic "emphatic s/t" sounds (ص/ط) come through as a *dental* diacritic
(U+032A) rather than the pharyngealization mark (ˤ) IPA references would
suggest, and "emphatic d" (ض) uses ˤ after all. Both are handled because
both were actually observed. Same approach for the Indic-language
symbols added later: aspiration (ʰ) and nasalization (combining tilde)
both modify the preceding sound rather than standing alone, so both are
handled as "append a suffix to whatever came before", not as their own
segment — aspirated consonants read as e.g. "kh"/"ph", the conventional
way English already represents them (Bhagavad Gita, Dharma, etc.), and
nasalized vowels get a trailing "n" for the same reason (informal but
learnable, similar to how French nasal vowels are sometimes respelled).

Sounds with no English equivalent (ʔ, ʕ, ħ, χ, ɣ, q) get a distinct
marker rather than being mapped to the nearest-but-wrong English letter,
per the "don't produce misleading pronunciations" requirement — see the
legend this module exports for what each marker means.
"""

import unicodedata

LEGEND = {
    "'": "a catch in the throat (glottal stop or 'ayn — both simplified to this)",
    "H": "a breathy H, further back in the throat than English h",
    "KH": "like the 'ch' in Scottish 'loch' or German 'Bach'",
    "GH": "a softer, voiced version of KH — no real English equivalent",
    "Q": "like K, but further back — deeper in the throat",
}

# Multi-character IPA sequences, matched before single characters.
_DIGRAPHS = {
    "dʒ": "j",   # جميل -> jameel
    "tʃ": "ch",
    "aː": "aa",
    "iː": "ee",
    "uː": "oo",
}

_SINGLES = {
    # plain consonants
    "b": "b", "d": "d", "f": "f", "h": "h", "k": "k", "l": "l",
    "m": "m", "n": "n", "p": "p", "r": "r", "s": "s", "t": "t",
    "v": "v", "w": "w", "z": "z",
    "j": "y",       # IPA j = English y sound
    "c": "ch",      # voiceless palatal stop, common in Indic scripts
    "θ": "th",      # voiceless th, as in "think"
    "ð": "th",      # voiced th, as in "this" — English spells both the same way
    "ʃ": "sh",
    "ʒ": "zh",
    "ɟ": "j",       # voiced palatal stop (aspirated version -> "jh", via the ʰ modifier)
    "ɡ": "g",       # script-g — a typographic IPA variant, same /g/ sound as plain g
    "ɳ": "n",       # retroflex nasal — English has no retroflex series, simplified to n
    "ɹ": "r",       # alveolar approximant — actually the standard English r sound
    "ɾ": "r",       # alveolar tap (Spanish-style single r) — still reads fine as "r"
    # no English equivalent — see LEGEND
    "ʔ": "'",
    "ʕ": "'",
    "ħ": "H",
    "χ": "KH",
    "ɣ": "GH",
    "q": "Q",
    # plain vowels
    "a": "a", "e": "e", "i": "i", "o": "o", "u": "u",
    "ɐ": "u",       # near-open central — "uh"-ish, collapsed with ə/ʌ below
    "ɔ": "o",       # open o, as in "law" — collapsed with plain o
    "ə": "u",       # schwa
    "ɛ": "e",       # open e, as in "bed" — collapsed with plain e
    "ɪ": "i",       # near-close near-front — "ih", collapsed with plain i
    "ʊ": "oo",      # near-close near-back — the "book" vowel
    "ʌ": "u",       # open-mid back — "uh" as in "cup"
}

# Modifier characters that alter the previously-emitted chunk rather than
# producing output of their own.
_CAPITALIZE_PREVIOUS = {"ˤ"}          # pharyngealization -> signal "different" via caps
_DUPLICATE_PREVIOUS = {"ː"}           # length mark after a consonant = gemination, e.g. abːka
_APPEND_TO_PREVIOUS = {
    "ʰ": "h",                          # aspiration -> kh/ph/th/chh, the conventional spelling
    "\u0303": "n",                     # combining tilde: nasalized vowel -> trailing n
}
_IGNORED = {"̪", "ˈ", "ˌ"}             # dental diacritic, stress marks — no friendly-spelling effect


def respell(ipa: str) -> str:
    # Normalize to decomposed form first: combining marks like the
    # nasalization tilde can arrive either as their own codepoint (what
    # espeak-ng actually produces) or pre-composed into a single
    # character (e.g. ũ as one codepoint instead of u + combining
    # tilde) — found via a test string that looked identical either way
    # but broke the character-by-character scan. Normalizing up front
    # means the rest of this function doesn't need to care which form
    # showed up.
    ipa = unicodedata.normalize("NFD", ipa)

    tokens: list[str] = []
    i = 0
    while i < len(ipa):
        two = ipa[i : i + 2]
        if two in _DIGRAPHS:
            tokens.append(_DIGRAPHS[two])
            i += 2
            continue

        char = ipa[i]

        if char in _CAPITALIZE_PREVIOUS:
            if tokens:
                tokens[-1] = tokens[-1].upper()
            i += 1
            continue

        if char in _DUPLICATE_PREVIOUS:
            if tokens:
                tokens.append(tokens[-1])
            i += 1
            continue

        if char in _APPEND_TO_PREVIOUS:
            if tokens:
                tokens.append(_APPEND_TO_PREVIOUS[char])
            i += 1
            continue

        if char in _IGNORED:
            i += 1
            continue

        if char == " ":
            tokens.append(" ")
            i += 1
            continue

        tokens.append(_SINGLES.get(char, char))  # unmapped chars pass through, visibly
        i += 1

    return "".join(tokens)
