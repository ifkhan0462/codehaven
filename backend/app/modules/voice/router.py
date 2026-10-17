from fastapi import APIRouter

router = APIRouter(prefix="/voice", tags=["voice"])


@router.get("/status")
async def voice_status() -> dict[str, str]:
    return {"status": "not_implemented", "message": "Voice input module coming in Phase 5."}
