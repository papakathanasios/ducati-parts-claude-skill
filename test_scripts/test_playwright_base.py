from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.adapters.base import AdapterHealthCheck
from src.core.types import RawListing, SearchFilters


class TestPlaywrightAdapter(PlaywrightBaseAdapter):
    source_name = "test_pw"
    language = "en"
    country = "GB"
    currency = "GBP"
    base_url = "https://example.com"

    async def _extract_listings(self, page, query):
        return [RawListing(source_id="pw1", source=self.source_name, title="Test part",
            description="Good", price=20.0, currency=self.currency, shipping_price=None,
            seller_country=self.country, condition_label="Good", photos=[],
            listing_url="https://example.com/1")]

    def _build_search_url(self, query):
        return f"{self.base_url}/search?q={query}"


def test_playwright_adapter_has_required_attrs():
    adapter = TestPlaywrightAdapter()
    assert adapter.source_name == "test_pw"
    assert adapter.base_url == "https://example.com"

def test_playwright_adapter_builds_search_url():
    adapter = TestPlaywrightAdapter()
    url = adapter._build_search_url("clutch lever")
    assert "clutch lever" in url
    assert "example.com" in url
