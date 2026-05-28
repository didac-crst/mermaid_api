from fastapi import APIRouter

from src.render.mermaid_renderer import ENGINE_VERSION

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness check with pinned Mermaid engine version."""
    return {
        "status": "ok",
        "engine": "mermaid",
        "engineVersion": ENGINE_VERSION,
    }
