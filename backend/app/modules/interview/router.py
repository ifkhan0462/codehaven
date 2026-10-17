from fastapi import APIRouter

router = APIRouter(prefix="/interview", tags=["interview"])


@router.get("/status")
async def interview_status() -> dict[str, str]:
    return {
        "status": "not_implemented",
        "message": "Interview prep module coming in Phase 6.",
    }
