from fastapi import APIRouter

from app.models.schemas import ManualLyricsRequest, ManualLyricsResponse
from app.services.lyrics_processor import process_plain_lyrics

router = APIRouter()


@router.post("/lyrics/manual", response_model=ManualLyricsResponse)
async def manual_lyrics(request: ManualLyricsRequest) -> ManualLyricsResponse:
    return ManualLyricsResponse(lines=process_plain_lyrics(request.lyrics))
