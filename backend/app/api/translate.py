from fastapi import APIRouter, HTTPException

from app.models.schemas import TranslateRequest, TranslateResponse
from app.services.translation import TranslationAPIError, TranslationConfigError, translate_lines

router = APIRouter()


@router.post("/lyrics/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest) -> TranslateResponse:
    try:
        translations = await translate_lines(request.lines)
    except TranslationConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except TranslationAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return TranslateResponse(translations=translations)
