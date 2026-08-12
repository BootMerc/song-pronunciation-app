"""Korean romanization via korean-romanizer (Revised Romanization of Korean)."""

from korean_romanizer.romanizer import Romanizer


def romanize(line: str) -> str:
    return Romanizer(line).romanize()
