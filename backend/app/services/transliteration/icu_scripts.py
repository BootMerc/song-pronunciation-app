"""Russian and Greek romanization via ICU's standard CLDR transliteration
rules (PyICU bindings). One module for both since they're the same
mechanism applied to two different script transforms.

Needs the system ICU library to build — see the Dockerfile.

Note on Greek specifically: ICU's "Greek-Latin" transform follows the
classical/scholarly convention for digraphs (ευ -> "eu"), not modern
spoken pronunciation (which is "ev"/"ef" depending on what follows). It
was chosen over the pure-Python `transliterate` package because that one
doesn't handle Greek digraphs at all (σου came back as "soy" instead of
"sou" — genuinely wrong, not just a different convention). Getting from
this standard romanization to how it's actually sung is exactly what the
respelling step (Step 4) is for.
"""

import icu

_TRANSFORMS = {
    "ru": icu.Transliterator.createInstance("Russian-Latin/BGN"),
    "el": icu.Transliterator.createInstance("Greek-Latin"),
}


def romanize_ru(line: str) -> str:
    return _TRANSFORMS["ru"].transliterate(line)


def romanize_el(line: str) -> str:
    return _TRANSFORMS["el"].transliterate(line)
