from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables or a .env file.

    Kept intentionally small right now — fields get added in later steps
    alongside the code that actually consumes them (e.g. YOUTUBE_API_KEY
    lands with the YouTube client), rather than declared speculatively.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Song Pronunciation API"
    app_env: str = "development"
    cors_origins: list[str] = ["http://localhost:5173"]
    youtube_api_key: str = ""
    anthropic_api_key: str = ""


settings = Settings()
