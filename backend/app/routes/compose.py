from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.message import rephrase_message

router = APIRouter(prefix="/api/compose", tags=["compose"])


class PreviewRequest(BaseModel):
    base_message: str
    variant_count: int = 3


class PreviewResponse(BaseModel):
    base_message: str
    variants: list[str]


@router.post("/preview", response_model=PreviewResponse)
async def preview_message(data: PreviewRequest):
    if not data.base_message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if data.variant_count < 1 or data.variant_count > 10:
        raise HTTPException(status_code=400, detail="Variant count must be 1-10")

    try:
        variants = await rephrase_message(data.base_message, data.variant_count)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI rephrase failed: {e}")

    return PreviewResponse(base_message=data.base_message, variants=variants)
