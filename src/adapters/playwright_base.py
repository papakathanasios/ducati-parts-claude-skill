import asyncio
from abc import abstractmethod
from playwright.async_api import async_playwright, Page, Browser
from src.adapters.base import BaseAdapter, AdapterHealthCheck
from src.core.types import RawListing, SearchFilters


class PlaywrightBaseAdapter(BaseAdapter):
    base_url: str
    _browser: Browser | None = None

    async def _get_browser(self) -> Browser:
        if self._browser is None or not self._browser.is_connected():
            pw = await async_playwright().start()
            self._browser = await pw.chromium.launch(headless=True)
        return self._browser

    async def search(self, query: str, filters: SearchFilters) -> list[RawListing]:
        browser = await self._get_browser()
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            locale=self.language)
        page = await context.new_page()
        try:
            url = self._build_search_url(query)
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            results = await self._extract_listings(page, query)
            return results
        finally:
            await context.close()

    async def health_check(self) -> AdapterHealthCheck:
        try:
            browser = await self._get_browser()
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(self.base_url, wait_until="domcontentloaded", timeout=15000)
            await context.close()
            return AdapterHealthCheck(healthy=True, message=f"{self.source_name} reachable")
        except Exception as e:
            return AdapterHealthCheck(healthy=False, message=str(e))

    @abstractmethod
    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]: ...

    @abstractmethod
    def _build_search_url(self, query: str) -> str: ...

    async def close(self) -> None:
        if self._browser and self._browser.is_connected():
            await self._browser.close()
