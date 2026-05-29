from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.main import app as production_app
from src.response.errors import MermaidParseError, MermaidRenderTimeoutError
from src.routes.health import router as health_router
from src.routes.render import router as render_router
from src.routes.validate import router as validate_router


class StubRenderer:
    async def validate(self, code: str, theme: str = "default") -> dict[str, Any]:
        if "invalid" in code:
            return {"valid": False, "message": "Unexpected token"}
        return {"valid": True, "diagramType": "flowchart-v2"}

    async def render(self, payload):
        if "timeout" in payload.code:
            raise MermaidRenderTimeoutError()
        if "invalid" in payload.code:
            raise MermaidParseError("Unexpected token")
        if payload.format == "svg":
            return b"<svg><rect width='10' height='10' /></svg>", "image/svg+xml"
        if payload.format in {"jpg", "jpeg"}:
            return b"\xff\xd8\xff\xe0fakejpeg", "image/jpeg"
        return b"\x89PNG\r\n\x1afakepng", "image/png"


@pytest.fixture
def app() -> FastAPI:
    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        app.state.renderer = StubRenderer()
        yield

    test_app = FastAPI(lifespan=test_lifespan)
    test_app.include_router(health_router)
    test_app.include_router(validate_router)
    test_app.include_router(render_router)
    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def production_lifespan_app() -> FastAPI:
    return production_app
