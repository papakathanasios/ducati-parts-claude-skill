"""Moto-Breakers.co.uk adapter – UK motorcycle parts marketplace.

NOTE: As of April 2026, moto-breakers.co.uk is unreachable.
This adapter is kept disabled. Re-enable if the site comes back online.
"""

from urllib.parse import quote

from playwright.async_api import Page

from src.adapters.base import AdapterHealthCheck
from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class MotoBreakersAdapter(PlaywrightBaseAdapter):
    source_name = "moto_breakers"
    language = "en"
    country = "GB"
    currency = "GBP"
    base_url = "https://www.moto-breakers.co.uk"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/search?q={quote(query)}"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        # Site is unreachable as of April 2026
        return []

    async def health_check(self) -> AdapterHealthCheck:
        return AdapterHealthCheck(
            healthy=False,
            message="moto-breakers.co.uk is unreachable (site down since April 2026)",
        )
