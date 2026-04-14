import asyncio
from decimal import Decimal
from src.core.search import SearchOrchestrator
from src.core.types import RawListing, SearchFilters
from src.core.config import AppConfig, BikeConfig, ShippingConfig, SearchConfig, ConditionConfig, WatchConfig
from src.adapters.base import BaseAdapter, AdapterHealthCheck


class MockAdapter(BaseAdapter):
    source_name = "mock"
    language = "en"
    country = "BG"
    currency = "EUR"

    def __init__(self, results: list[RawListing]):
        self._results = results

    async def search(self, query: str, filters: SearchFilters) -> list[RawListing]:
        return self._results

    async def health_check(self) -> AdapterHealthCheck:
        return AdapterHealthCheck(healthy=True, message="OK")


class FailingAdapter(BaseAdapter):
    source_name = "failing"
    language = "en"
    country = "US"
    currency = "USD"

    async def search(self, query: str, filters: SearchFilters) -> list[RawListing]:
        raise ConnectionError("down")

    async def health_check(self) -> AdapterHealthCheck:
        return AdapterHealthCheck(healthy=False, message="down")


def _make_config() -> AppConfig:
    return AppConfig(
        bike=BikeConfig(default_model="Multistrada 1260 Enduro", year_range=[2019, 2021], also_compatible=["Multistrada 1260"]),
        shipping=ShippingConfig(destination_country="GR", destination_postal="15562", destination_city="Athens", shipping_ratio_warning=0.5),
        search=SearchConfig(default_tiers=[1, 2], max_results_per_source=50, currency_display="EUR"),
        condition=ConditionConfig(min_score="red", photo_required=False),
        watch=WatchConfig(check_interval_hours=4, stale_listing_days=30, notification="macos"),
        tiers={1: ["mock"], 2: [], 3: []},
    )


def test_orchestrator_collects_results_from_adapters():
    raw = RawListing(source_id="1", source="mock", title="Clutch lever Multistrada",
        description="Good condition", price=20.0, currency="EUR", shipping_price=8.0,
        seller_country="BG", condition_label="Good", photos=["https://example.com/p.jpg"],
        listing_url="https://mock.com/1")
    adapter = MockAdapter([raw])
    config = _make_config()
    orchestrator = SearchOrchestrator(config=config, adapters={"mock": adapter})
    filters = SearchFilters(query="clutch lever", tiers=[1])
    listings = asyncio.run(orchestrator.run(filters))
    assert len(listings) == 1
    assert listings[0].id == "mock_1"
    assert listings[0].part_price == Decimal("20.00")
    assert listings[0].seller_country == "BG"
    assert listings[0].is_eu is True


def test_orchestrator_excludes_bad_condition():
    raw = RawListing(source_id="2", source="mock", title="Broken lever for parts",
        description="Cracked, not usable", price=5.0, currency="EUR", shipping_price=3.0,
        seller_country="BG", condition_label="For parts", photos=[],
        listing_url="https://mock.com/2")
    adapter = MockAdapter([raw])
    config = _make_config()
    orchestrator = SearchOrchestrator(config=config, adapters={"mock": adapter})
    filters = SearchFilters(query="lever", tiers=[1])
    listings = asyncio.run(orchestrator.run(filters))
    assert len(listings) == 0


def test_orchestrator_filters_by_max_total_price():
    raw1 = RawListing(source_id="1", source="mock", title="Cheap lever", description="OK",
        price=10.0, currency="EUR", shipping_price=5.0, seller_country="BG",
        condition_label="Good", photos=[], listing_url="https://mock.com/1")
    raw2 = RawListing(source_id="2", source="mock", title="Expensive lever", description="OK",
        price=100.0, currency="EUR", shipping_price=20.0, seller_country="BG",
        condition_label="Good", photos=[], listing_url="https://mock.com/2")
    adapter = MockAdapter([raw1, raw2])
    config = _make_config()
    orchestrator = SearchOrchestrator(config=config, adapters={"mock": adapter})
    filters = SearchFilters(query="lever", tiers=[1], max_total_price=Decimal("50"))
    listings = asyncio.run(orchestrator.run(filters))
    assert len(listings) == 1
    assert listings[0].total_price == Decimal("15.00")


def test_orchestrator_handles_adapter_failure():
    adapter = FailingAdapter()
    config = _make_config()
    config.tiers[1] = ["failing"]
    orchestrator = SearchOrchestrator(config=config, adapters={"failing": adapter})
    filters = SearchFilters(query="lever", tiers=[1])
    listings = asyncio.run(orchestrator.run(filters))
    assert len(listings) == 0
    assert "failing" in orchestrator.last_errors


def test_dedup_removes_duplicate_listings():
    raw = RawListing(source_id="1", source="mock", title="Lever", description="Good",
        price=20.0, currency="EUR", shipping_price=8.0, seller_country="BG",
        condition_label="Good", photos=[], listing_url="https://mock.com/1")
    adapter = MockAdapter([raw, raw])
    config = _make_config()
    orchestrator = SearchOrchestrator(config=config, adapters={"mock": adapter})
    filters = SearchFilters(query="lever", tiers=[1])
    listings = asyncio.run(orchestrator.run(filters))
    assert len(listings) == 1
