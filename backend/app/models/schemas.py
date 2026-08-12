"""API-facing request/response contracts — what /songs/resolve and
/lyrics/manual actually accept and return. Distinct from the internal
service-level models (YouTubeVideoResult, LyricsResult,
TransliterationResult), which stay close to the code that produces them.
"""

from pydantic import BaseModel, Field, field_validator

from app.services.youtube_client import YouTubeVideoResult


class LyricLine(BaseModel):
    original: str
    romanized: str
    friendly: str
    language: str
    timestamp_ms: int | None = None
    supported: bool = True  # False if this line's language has no transliteration module yet


class SongResolveRequest(BaseModel):
    title: str = Field(min_length=1)
    artist: str = Field(min_length=1)

    @field_validator("title", "artist")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class SongResolveResponse(BaseModel):
    video: YouTubeVideoResult | None = None
    video_error: str | None = None
    lyrics_found: bool
    instrumental: bool = False
    synced: bool = False
    lines: list[LyricLine] = []
    lyrics_error: str | None = None
    # Only set when resolved from a YouTube URL — the title/artist were
    # guessed from video metadata, not typed by the user, so the frontend
    # needs to show (and let the user correct) what was guessed.
    guessed_title: str | None = None
    guessed_artist: str | None = None


class YouTubeUrlRequest(BaseModel):
    url: str = Field(min_length=1)

    @field_validator("url")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class ManualLyricsRequest(BaseModel):
    lyrics: str = ""


class ManualLyricsResponse(BaseModel):
    lines: list[LyricLine]


class TranslateRequest(BaseModel):
    lines: list[str] = Field(min_length=1)


class TranslateResponse(BaseModel):
    translations: list[str]
