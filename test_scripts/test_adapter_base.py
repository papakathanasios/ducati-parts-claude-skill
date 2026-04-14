import asyncio
from src.adapters.base import BaseAdapter, AdapterHealthCheck
from src.core.types import RawListing, SearchFilters


class FakeAdapter(BaseAdapter):
    source_name = "fake"
    language = "en"
    country = "GB"
    currency = "GBP"

    async def search(self, query: str, filters: SearchFilters) -> list[RawListing]:
        return [RawListing(
            source_id="1", source=self.source_name, title=f"Fake result for {query}",
            description="A fake listing", price=10.0, currency=self.currency,
            shipping_price=5.0, seller_country=self.country, condition_label="Good",
            photos=[], listing_url="https://fake.com/1",
        )]

    async def health_check(self) -> AdapterHealthCheck:
        return AdapterHealthCheck(healthy=True, message="OK")


class BrokenAdapter(BaseAdapter):
    source_name = "broken"
    language = "en"
    country = "US"
    currency = "USD"

    async def search(self, query: str, filters: SearchFilters) -> list[RawListing]:
        raise ConnectionError("Site is down")

    async def health_check(self) -> AdapterHealthCheck:
        return AdapterHealthCheck(healthy=False, message="Site unreachable")


def test_fake_adapter_search():
    adapter = FakeAdapter()
    results = asyncio.run(adapter.search("clutch lever", SearchFilters(query="clutch lever")))
    assert len(results) == 1
    assert results[0].source == "fake"
    assert "clutch lever" in results[0].title


def test_adapter_properties():
    adapter = FakeAdapter()
    assert adapter.source_name == "fake"
    assert adapter.language == "en"
    assert adapter.country == "GB"


def test_adapter_health_check():
    adapter = FakeAdapter()
    health = asyncio.run(adapter.health_check())
    assert health.healthy is True
    broken = BrokenAdapter()
    health = asyncio.run(broken.health_check())
    assert health.healthy is False
