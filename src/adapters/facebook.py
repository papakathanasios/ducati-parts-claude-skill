"""Facebook Marketplace adapter – EU-wide marketplace.

NOTE: Facebook Marketplace requires authentication to search.
This adapter is disabled by default. It can be enabled once
a login session cookie mechanism is implemented.
"""

from urllib.parse import quote

from playwright.async_api import Page

from src.adapters.base import AdapterHealthCheck
from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class FacebookMarketplaceAdapter(PlaywrightBaseAdapter):
    source_name = "facebook_marketplace"
    language = "en"
    country = "EU"
    currency = "EUR"
    base_url = "https://www.facebook.com"
    _requires_auth = True

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/marketplace/search/?query={quote(query)}"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        # Facebook requires login - return empty until auth is implemented
        return []

    async def health_check(self) -> AdapterHealthCheck:
        return AdapterHealthCheck(
            healthy=False,
            message="Facebook Marketplace requires authentication (not yet implemented)",
        )
