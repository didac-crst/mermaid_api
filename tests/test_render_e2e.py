from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.main import app

MERMAID_SCRIPT = (
    Path(__file__).resolve().parents[1] / "vendor" / "mermaid" / "dist" / "mermaid.min.js"
)
INVALID_FLOWCHART = "flowchart TD\n    A[Start --> B[Missing closing bracket]"
VALID_FLOWCHART = "flowchart TD\nA-->B"
# Mermaid's built-in error diagram uses a fixed viewBox size.
ERROR_DIAGRAM_VIEWBOX = b'viewBox="0 0 2412 512"'
ERROR_DIAGRAM_MESSAGE = b"Syntax error in text"


def _playwright_chromium_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            return Path(playwright.chromium.executable_path).exists()
    except Exception:
        return False


pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not MERMAID_SCRIPT.exists(),
        reason="vendor/mermaid not installed; run ./scripts/install_mermaid.sh",
    ),
    pytest.mark.skipif(
        not _playwright_chromium_available(),
        reason="Playwright Chromium not installed; run playwright install chromium",
    ),
]


@pytest.fixture(scope="module")
def e2e_client() -> TestClient:
    with TestClient(app) as client:
        yield client


def test_render_invalid_syntax_returns_json_error(e2e_client: TestClient):
    response = e2e_client.post(
        "/render",
        json={"code": INVALID_FLOWCHART, "format": "svg"},
    )

    assert response.status_code == 400
    assert "application/json" in response.headers["content-type"]
    body = response.json()
    assert body["detail"]["error"]["code"] == "MERMAID_PARSE_ERROR"
    assert ERROR_DIAGRAM_VIEWBOX not in response.content
    assert ERROR_DIAGRAM_MESSAGE not in response.content


def test_render_invalid_syntax_png_returns_json_error(e2e_client: TestClient):
    response = e2e_client.post(
        "/render",
        json={"code": INVALID_FLOWCHART, "format": "png"},
    )

    assert response.status_code == 400
    assert "application/json" in response.headers["content-type"]
    assert response.json()["detail"]["error"]["code"] == "MERMAID_PARSE_ERROR"


def test_render_valid_flowchart_returns_svg(e2e_client: TestClient):
    response = e2e_client.post(
        "/render",
        json={"code": VALID_FLOWCHART, "format": "svg"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.content.startswith(b"<svg")
    assert ERROR_DIAGRAM_VIEWBOX not in response.content
    assert ERROR_DIAGRAM_MESSAGE not in response.content
