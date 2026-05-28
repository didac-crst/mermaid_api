from fastapi import APIRouter, Request

from src.response.errors import MermaidParseError
from src.validation.schemas import ValidateRequest

router = APIRouter()


@router.post("/validate")
async def validate(payload: ValidateRequest, request: Request) -> dict:
    """Check Mermaid syntax and return diagram metadata without rendering."""
    result = await request.app.state.renderer.validate(payload.code)
    if result.get("valid"):
        return {"valid": True, "diagramType": result.get("diagramType", "unknown")}
    raise MermaidParseError(result.get("message", "Invalid Mermaid syntax")).to_http_exception()
