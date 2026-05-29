"""Shared Playwright Chromium lifecycle for render requests."""

from __future__ import annotations

import asyncio

from playwright.async_api import Browser, Playwright, async_playwright


class BrowserManager:
    """Lazy-start a single Chromium browser reused across requests."""

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._lock = asyncio.Lock()

    async def get_browser(self) -> Browser:
        async with self._lock:
            if self._browser:
                return self._browser

            playwright = await async_playwright().start()
            try:
                browser = await playwright.chromium.launch(headless=True)
            except Exception:
                await playwright.stop()
                raise

            self._playwright = playwright
            self._browser = browser
            return self._browser

    async def close(self) -> None:
        async with self._lock:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            self._browser = None
            self._playwright = None
