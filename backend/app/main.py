from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import manual, resolve, translate
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    description="Pronunciation and romanization for non-English song lyrics.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resolve.router)
app.include_router(manual.router)
app.include_router(translate.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Liveness check used by Docker and local dev to confirm the API is up."""
    return {"status": "ok", "env": settings.app_env}
