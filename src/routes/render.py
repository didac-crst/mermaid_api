from fastapi import APIRouter, Request, Response

from src.response.errors import MermaidApiError
from src.validation.schemas import RenderRequest

router = APIRouter()


@router.post("/render", response_model=None)
async def render(payload: RenderRequest, request: Request) -> Response:
    """Return an image on success or raise JSON ``detail.error`` on failure."""
    try:
        body, content_type = await request.app.state.renderer.render(payload)
    except MermaidApiError as error:
        raise error.to_http_exception() from error

    return Response(
        content=body,
        media_type=content_type,
        headers={"Cache-Control": "no-store"},
    )
