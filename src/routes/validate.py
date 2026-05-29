from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.response.errors import MermaidParseError
from src.validation.schemas import ValidateRequest

router = APIRouter()
MAX_VALIDATE_INPUT_PREVIEW_CHARS = 2048


@router.post("/validate")
async def validate(payload: ValidateRequest, request: Request) -> dict:
    """Check Mermaid syntax and return diagram metadata without rendering."""
    result = await request.app.state.renderer.validate(payload.code)
    if result.get("valid"):
        return {"valid": True, "diagramType": result.get("diagramType", "unknown")}

    include_input = request.headers.get("X-Include-Input", "").lower() == "true"
    parse_error = MermaidParseError(result.get("message", "Invalid Mermaid syntax"))
    content = {
        "valid": False,
        "error": {
            "code": parse_error.code,
            "message": parse_error.message,
        },
    }
    if include_input:
        preview = payload.code[:MAX_VALIDATE_INPUT_PREVIEW_CHARS]
        content["originalSyntaxPreview"] = preview
        content["originalSyntaxTruncated"] = len(payload.code) > MAX_VALIDATE_INPUT_PREVIEW_CHARS

    return JSONResponse(
        status_code=parse_error.status_code,
        content=content,
    )
