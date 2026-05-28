"""Playwright-backed Mermaid validation and rendering."""

from __future__ import annotations

import asyncio
from pathlib import Path

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page

from src.render.browser import BrowserManager
from src.response.errors import MermaidParseError, MermaidRenderError, MermaidRenderTimeoutError
from src.validation.schemas import RenderRequest

DEFAULT_TIMEOUT_MS = 10_000
ENGINE_VERSION = "11.15.0"

_PARSE_DIAGRAM_JS = """
async ({ code }) => {
  try {
    const result = await window.__mermaid.parse(code);
    if (result?.diagramType === "error") {
      return { valid: false, message: "Invalid Mermaid syntax" };
    }
    return { valid: true, diagramType: result.diagramType || "unknown" };
  } catch (error) {
    return { valid: false, message: String(error?.message || error) };
  }
}
"""

_RENDER_DIAGRAM_JS = """
async ({ code }) => {
  try {
    const id = `mermaid-${Date.now()}`;
    const result = await window.__mermaid.render(id, code);
    const container = document.getElementById("diagram");
    container.innerHTML = result.svg;
    const svg = container.querySelector("svg");
    if (!svg) {
      return { error: true, message: "Mermaid did not produce SVG output" };
    }
    if (svg.querySelector(".error-icon, .error-text")) {
      const parts = [...svg.querySelectorAll(".error-text")]
        .map((node) => node.textContent?.trim())
        .filter(Boolean);
      const message =
        parts.find((text) => !/^mermaid version\\s/i.test(text)) ||
        parts[0] ||
        "Mermaid render error";
      return { error: true, message };
    }
    const rect = svg.getBoundingClientRect();
    return {
      error: false,
      svg: result.svg,
      width: Math.ceil(rect.width),
      height: Math.ceil(rect.height),
    };
  } catch (error) {
    return { error: true, message: String(error?.message || error) };
  }
}
"""


def _raise_on_browser_error(result: dict) -> None:
    """Map browser-side render failures to API parse errors."""
    if result.get("error"):
        raise MermaidParseError(result.get("message") or "Invalid Mermaid syntax")


class MermaidRenderer:
    """Validate and render Mermaid diagrams inside isolated Playwright pages."""

    def __init__(self, browser_manager: BrowserManager, mermaid_script_path: Path, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> None:
        self._browser_manager = browser_manager
        self._mermaid_script_path = mermaid_script_path
        self._timeout_ms = timeout_ms

    async def validate(self, code: str, theme: str = "default") -> dict[str, str | bool]:
        """Return ``{valid, diagramType}`` or ``{valid: false, message}`` without rasterizing."""
        browser = await self._browser_manager.get_browser()
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await self._prepare_page(page=page, theme=theme)
            return await page.evaluate(_PARSE_DIAGRAM_JS, {"code": code})
        except PlaywrightError as error:
            raise MermaidRenderError("Failed to validate diagram") from error
        finally:
            await context.close()

    async def render(self, request: RenderRequest) -> tuple[bytes, str]:
        """Render a diagram and return ``(body, media_type)``."""
        try:
            return await asyncio.wait_for(self._render_impl(request), timeout=self._timeout_ms / 1000)
        except asyncio.TimeoutError as error:
            raise MermaidRenderTimeoutError() from error

    async def _render_impl(self, request: RenderRequest) -> tuple[bytes, str]:
        browser = await self._browser_manager.get_browser()
        context = await browser.new_context(
            viewport={"width": request.width, "height": request.height},
            device_scale_factor=request.scale,
        )
        page = await context.new_page()

        try:
            await self._prepare_page(page=page, theme=request.theme)

            parsed = await page.evaluate(_PARSE_DIAGRAM_JS, {"code": request.code})
            if not parsed["valid"]:
                raise MermaidParseError(parsed["message"])

            rendered = await page.evaluate(_RENDER_DIAGRAM_JS, {"code": request.code})
            _raise_on_browser_error(rendered)

            if request.format == "svg":
                return rendered["svg"].encode("utf-8"), "image/svg+xml"

            element = page.locator("#diagram svg")
            screenshot = await element.screenshot(
                type="jpeg" if request.format in {"jpg", "jpeg"} else "png",
                omit_background=request.transparent and request.format == "png",
            )
            content_type = "image/jpeg" if request.format in {"jpg", "jpeg"} else "image/png"
            return screenshot, content_type
        except MermaidParseError:
            raise
        except PlaywrightError as error:
            raise MermaidRenderError("Failed to render diagram") from error
        finally:
            await context.close()

    async def _prepare_page(self, page: Page, theme: str) -> None:
        await page.set_content(self._render_html())
        await page.add_script_tag(path=str(self._mermaid_script_path.resolve()))
        await page.evaluate(
            """
            ({ theme }) => {
              mermaid.initialize({
                startOnLoad: false,
                securityLevel: "strict",
                theme
              });
              window.__mermaid = mermaid;
              window.__mermaidReady = true;
            }
            """,
            {"theme": theme},
        )
        await page.wait_for_function("window.__mermaidReady === true", timeout=self._timeout_ms)

    def _render_html(self) -> str:
        return """
<!doctype html>
<html>
  <body style="margin:0;padding:0;">
    <div id="diagram"></div>
  </body>
</html>
"""
