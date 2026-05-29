from unittest.mock import AsyncMock, patch

import pytest

from src.render.browser import BrowserManager


@pytest.mark.asyncio
async def test_launch_failure_stops_playwright() -> None:
    manager = BrowserManager()
    mock_playwright = AsyncMock()
    mock_playwright.chromium.launch = AsyncMock(side_effect=RuntimeError("launch failed"))

    with patch("src.render.browser.async_playwright") as mock_async_playwright:
        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright)
        with pytest.raises(RuntimeError, match="launch failed"):
            await manager.get_browser()

    mock_playwright.stop.assert_awaited_once()
    assert manager._playwright is None
    assert manager._browser is None
