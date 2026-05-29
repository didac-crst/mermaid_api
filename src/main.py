"""FastAPI application entrypoint for the Mermaid Render API."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from src.render.browser import BrowserManager
from src.render.mermaid_renderer import MermaidRenderer
from src.routes.health import router as health_router
from src.routes.render import router as render_router
from src.routes.validate import router as validate_router


def _resolve_mermaid_script_path() -> Path:
    root = Path(__file__).resolve().parents[1]
    return root / "vendor" / "mermaid" / "dist" / "mermaid.min.js"


def _ensure_mermaid_runtime(path: Path) -> None:
    if path.is_file():
        return
    raise RuntimeError(
        f"Mermaid runtime not found at {path}. "
        "Run ./scripts/install_mermaid.sh (or rebuild the Docker image)."
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    mermaid_script_path = _resolve_mermaid_script_path()
    _ensure_mermaid_runtime(mermaid_script_path)

    manager = BrowserManager()
    renderer = MermaidRenderer(
        browser_manager=manager,
        mermaid_script_path=mermaid_script_path,
    )
    app.state.browser_manager = manager
    app.state.renderer = renderer
    yield
    await manager.close()


app = FastAPI(title="Mermaid Render API", lifespan=lifespan)
app.include_router(health_router)
app.include_router(validate_router)
app.include_router(render_router)
