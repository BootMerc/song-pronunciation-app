"""Japanese romanization via cutlet (Hepburn system, MeCab-based tokenization).

use_foreign_spelling is explicitly disabled: cutlet's default reconstructs
the original English word for loanwords (コンピューター -> "Computer"),
which is wrong for a pronunciation app — someone singing along needs the
actual sung phonetics ("Konpyuutaa"), not the English source word.

_HONORIFIC_FIXES works around a real dictionary gap in unidic-lite (the
bundled dictionary; the full unidic dictionary would likely fix this too,
but its data download is blocked from this project's build environment):
お母さん/お父さん/お兄さん/お姉さん (mother/father/older brother/older
sister, addressed politely) get read with each kanji's standalone
reading (haha/chichi/ani/ane) instead of the correct compound reading
(kaa/tou/nii/nee) — e.g. お母さん comes back "Ohahasan" instead of
"Okaasan". Substituting the equivalent hiragana spelling before
romanizing sidesteps the ambiguity entirely, since hiragana has only one
reading. These four are common enough in song lyrics (family/love
themes) to be worth a targeted fix rather than a documented caveat.
"""

import cutlet

_katsu = cutlet.Cutlet()  # built once; MeCab tagger init is the expensive part
_katsu.use_foreign_spelling = False

_HONORIFIC_FIXES = {
    "お母さん": "おかあさん",
    "お父さん": "おとうさん",
    "お兄さん": "おにいさん",
    "お姉さん": "おねえさん",
}


def romanize(line: str) -> str:
    for kanji_form, kana_form in _HONORIFIC_FIXES.items():
        line = line.replace(kanji_form, kana_form)
    return _katsu.romaji(line)

