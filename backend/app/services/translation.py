"""Translates lyric lines to English via the Anthropic API — server-side
only. This must never be called from the browser: exposing an API key
in frontend code means anyone can pull it out of the network tab and
spend money on it. The special no-key-needed way of calling this API
only works inside Claude.ai's own artifact sandbox, not in a real
standalone deployed app like this one.

Optional feature: everything else in this app works with no
ANTHROPIC_API_KEY set at all. This is the one part of the pipeline with
a real, non-zero cost, which is why it's a button the user clicks
(translate this song) rather than something that runs automatically on
every search.
"""

import json
import re

import httpx

from app.config import settings

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"  # short, well-defined text task — cheapest tier fits


class TranslationConfigError(Exception):
    """Raised when translation is requested without an API key configured."""


class TranslationAPIError(Exception):
    """Raised for network failures, API errors, or a response that doesn't
    parse into exactly as many translations as lines were sent — a
    misaligned translation (wrong line next to wrong text) would be
    worse than no translation, so this fails loudly rather than guessing.
    """


_CODE_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


async def translate_lines(lines: list[str]) -> list[str]:
    if not settings.anthropic_api_key:
        raise TranslationConfigError(
            "ANTHROPIC_API_KEY is not set. Get one from console.anthropic.com "
            "and add it to backend/.env — translation is optional and everything "
            "else works without it."
        )

    # Blank lines (instrumental gaps) are handled deterministically here
    # rather than trusting the model to follow a "return empty for blank
    # input" instruction — removes any ambiguity about alignment.
    non_blank_indices = [i for i, line in enumerate(lines) if line.strip()]
    non_blank_lines = [lines[i] for i in non_blank_indices]

    if not non_blank_lines:
        return ["" for _ in lines]

    numbered = "\n".join(f"{i + 1}. {line}" for i, line in enumerate(non_blank_lines))
    prompt = (
        "Translate each of these song lyric lines into natural, idiomatic "
        "English. Return ONLY a JSON array of exactly "
        f"{len(non_blank_lines)} strings, one translation per line, in the "
        "same order as the input — no markdown formatting, no explanation, "
        "nothing before or after the array.\n\n"
        f"{numbered}"
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                ANTHROPIC_API_URL,
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": MODEL,
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
    except httpx.RequestError as exc:
        raise TranslationAPIError(f"Could not reach the translation API: {exc}") from exc

    if response.status_code != 200:
        raise TranslationAPIError(
            f"Translation API returned HTTP {response.status_code}: {response.text}"
        )

    body = response.json()
    text_blocks = [block["text"] for block in body.get("content", []) if block.get("type") == "text"]
    raw_text = "".join(text_blocks).strip()
    cleaned = _CODE_FENCE.sub("", raw_text).strip()

    try:
        translations = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise TranslationAPIError(
            f"Translation response wasn't valid JSON: {cleaned[:200]}"
        ) from exc

    if not isinstance(translations, list) or len(translations) != len(non_blank_lines):
        raise TranslationAPIError(
            f"Expected {len(non_blank_lines)} translations, got "
            f"{len(translations) if isinstance(translations, list) else type(translations).__name__}"
        )

    # Reinsert blanks at their original positions to restore full alignment
    # with the caller's original `lines` list.
    result = ["" for _ in lines]
    for source_index, translation in zip(non_blank_indices, translations):
        result[source_index] = translation
    return result
