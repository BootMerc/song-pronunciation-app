from fastapi import APIRouter, HTTPException

from app.models.schemas import SongResolveRequest, SongResolveResponse, YouTubeUrlRequest
from app.services.song_resolver import InvalidYouTubeURLError, resolve_song, resolve_song_from_url

router = APIRouter()


@router.post("/songs/resolve", response_model=SongResolveResponse)
async def resolve(request: SongResolveRequest) -> SongResolveResponse:
    return await resolve_song(request.title, request.artist)


@router.post("/songs/from-url", response_model=SongResolveResponse)
async def resolve_from_url(request: YouTubeUrlRequest) -> SongResolveResponse:
    try:
        return await resolve_song_from_url(request.url)
    except InvalidYouTubeURLError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
