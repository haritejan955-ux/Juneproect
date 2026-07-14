from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.db.session import SessionLocal
from app.rag.dependency import get_interaction_retriever

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
async def ready(response: Response) -> dict[str, object]:
    checks = {"database": False, "interaction_index": False}

    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass

    try:
        get_interaction_retriever()
        checks["interaction_index"] = True
    except Exception:
        pass

    is_ready = all(checks.values())
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ready" if is_ready else "not_ready", "checks": checks}
