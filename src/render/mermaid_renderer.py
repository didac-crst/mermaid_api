from __future__ import annotations

import asyncio
import json
from pathlib import Path

from playwright.async_api import Error as PlaywrightError

from src.render.browser import BrowserManager
from src.response.errors import MermaidParseError, MermaidRenderError, MermaidRenderTimeoutError
from src.validation.schemas import RenderRequest

DEFAULT_TIMEOUT_MS = 10_000
ENGINE_VERSION = "11.11.0"


class MermaidRenderer:
    def __init__(self, browser_manager: BrowserManager, mermaid_module_path: Path, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> None:
        self._browser_manager = browser_manager
        self._mermaid_module_path = mermaid_module_path
        self._timeout_ms = timeout_ms

    async def validate(self, code: str, theme: str = "default") -> dict[str, str]:
        browser = await self._browser_manager.get_browser()
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await page.set_content(self._render_html(theme))
            await page.wait_for_function("window.__mermaidReady === true", timeout=self._timeout_ms)
            return await page.evaluate(
                """
                async ({ code }) => {
                  try {
                    const result = await window.__mermaid.parse(code);
                    return { valid: true, diagramType: result.diagramType || "unknown" };
                  } catch (error) {
                    return { valid: false, message: String(error?.message || error) };
                  }
                }
                """,
                {"code": code},
            )
        except PlaywrightError as error:
            raise MermaidRenderError("Failed to validate diagram") from error
        finally:
            await context.close()

    async def render(self, request: RenderRequest) -> tuple[bytes, str]:
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
            await page.set_content(self._render_html(request.theme))
            await page.wait_for_function("window.__mermaidReady === true", timeout=self._timeout_ms)

            parsed = await page.evaluate(
                """
                async ({ code }) => {
                  try {
                    const parsed = await window.__mermaid.parse(code);
                    return { valid: true, diagramType: parsed.diagramType || "unknown" };
                  } catch (error) {
                    return { valid: false, message: String(error?.message || error) };
                  }
                }
                """,
                {"code": request.code},
            )
            if not parsed["valid"]:
                raise MermaidParseError(parsed["message"])

            rendered = await page.evaluate(
                """
                async ({ code }) => {
                  const id = `mermaid-${Date.now()}`;
                  const result = await window.__mermaid.render(id, code);
                  const container = document.getElementById("diagram");
                  container.innerHTML = result.svg;
                  const svg = container.querySelector("svg");
                  const rect = svg.getBoundingClientRect();
                  return {
                    svg: result.svg,
                    width: Math.ceil(rect.width),
                    height: Math.ceil(rect.height)
                  };
                }
                """,
                {"code": request.code},
            )

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

    def _render_html(self, theme: str) -> str:
        module_url = self._mermaid_module_path.resolve().as_uri()
        return f"""
<!doctype html>
<html>
  <body style="margin:0;padding:0;">
    <div id="diagram"></div>
    <script type="module">
      import mermaid from "{module_url}";
      mermaid.initialize({{
        startOnLoad: false,
        securityLevel: "strict",
        theme: {json.dumps(theme)}
      }});
      window.__mermaid = mermaid;
      window.__mermaidReady = true;
    </script>
  </body>
</html>
"""
