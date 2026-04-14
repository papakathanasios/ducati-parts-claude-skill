import asyncio
import os
import tempfile
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from src.cli import run_search, run_watch_list
from src.core.config import (
    AppConfig,
    BikeConfig,
    ConditionConfig,
    SearchConfig,
    ShippingConfig,
    WatchConfig,
)
from src.core.types import (
    CompatibilityConfidence,
    ConditionScore,
    Listing,
    RawListing,
    SearchFilters,
)
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


def _make_config_path() -> str:
    """Return the path to the project's config.yaml."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "config", "config.yaml")


def test_run_search_output_contains_query(capsys, tmp_path):
    """run_search prints terminal output that contains the search query."""
    raw = RawListing(
        source_id="1",
        source="mock",
        title="Clutch lever Multistrada",
        description="Good condition",
        price=20.0,
        currency="EUR",
        shipping_price=8.0,
        seller_country="BG",
        condition_label="Good",
        photos=["https://example.com/p.jpg"],
        listing_url="https://mock.com/1",
    )
    adapter = MockAdapter([raw])
    reports_dir = str(tmp_path / "reports")
    config_path = _make_config_path()

    report_path = asyncio.run(
        run_search(
            query="clutch lever",
            config_path=config_path,
            reports_dir=reports_dir,
            adapters={"mock": adapter},
            sources=["mock"],
        )
    )

    captured = capsys.readouterr()
    assert "clutch lever" in captured.out
    assert report_path.endswith(".html")
    assert os.path.exists(report_path)


def test_run_search_no_results_contains_query(capsys, tmp_path):
    """run_search with no results still shows the query in output."""
    adapter = MockAdapter([])
    reports_dir = str(tmp_path / "reports")
    config_path = _make_config_path()

    report_path = asyncio.run(
        run_search(
            query="nonexistent part xyz",
            config_path=config_path,
            reports_dir=reports_dir,
            adapters={"mock": adapter},
            sources=["mock"],
        )
    )

    captured = capsys.readouterr()
    assert "nonexistent part xyz" in captured.out
    assert report_path.endswith(".html")


def test_run_search_shows_adapter_errors(capsys, tmp_path):
    """run_search prints adapter errors when an adapter fails."""

    class FailingAdapter(BaseAdapter):
        source_name = "failing"
        language = "en"
        country = "US"
        currency = "USD"

        async def search(self, query: str, filters: SearchFilters) -> list[RawListing]:
            raise ConnectionError("service unavailable")

        async def health_check(self) -> AdapterHealthCheck:
            return AdapterHealthCheck(healthy=False, message="down")

    reports_dir = str(tmp_path / "reports")
    config_path = _make_config_path()

    asyncio.run(
        run_search(
            query="brake pads",
            config_path=config_path,
            reports_dir=reports_dir,
            adapters={"failing": FailingAdapter()},
            sources=["failing"],
        )
    )

    captured = capsys.readouterr()
    assert "brake pads" in captured.out
    assert "service unavailable" in captured.out


def test_run_watch_list_empty(capsys, tmp_path):
    """run_watch_list returns message when no watches exist."""
    db_path = str(tmp_path / "test.db")
    config_path = _make_config_path()

    result = asyncio.run(
        run_watch_list(config_path=config_path, db_path=db_path)
    )

    assert result == "No watches configured."


def test_run_watch_list_with_watches(capsys, tmp_path):
    """run_watch_list prints formatted watch entries."""
    from src.db.database import Database
    from src.watch.manager import WatchManager

    db_path = str(tmp_path / "test.db")
    config_path = _make_config_path()

    db = Database(db_path)
    db.initialize()
    mgr = WatchManager(db)
    mgr.create(query="exhaust slip-on", max_total_price=300.0)
    mgr.create(query="windscreen", max_total_price=150.0)

    result = asyncio.run(
        run_watch_list(config_path=config_path, db_path=db_path)
    )

    captured = capsys.readouterr()
    assert "exhaust slip-on" in captured.out
    assert "windscreen" in captured.out
    assert "300.00" in captured.out
    assert "active" in captured.out


def test_run_search_respects_max_total_price(capsys, tmp_path):
    """run_search filters results by max_total_price."""
    cheap = RawListing(
        source_id="1",
        source="mock",
        title="Cheap mirror",
        description="OK",
        price=10.0,
        currency="EUR",
        shipping_price=5.0,
        seller_country="BG",
        condition_label="Good",
        photos=[],
        listing_url="https://mock.com/1",
    )
    expensive = RawListing(
        source_id="2",
        source="mock",
        title="Expensive mirror",
        description="OK",
        price=200.0,
        currency="EUR",
        shipping_price=30.0,
        seller_country="BG",
        condition_label="Good",
        photos=[],
        listing_url="https://mock.com/2",
    )
    adapter = MockAdapter([cheap, expensive])
    reports_dir = str(tmp_path / "reports")
    config_path = _make_config_path()

    asyncio.run(
        run_search(
            query="mirror",
            config_path=config_path,
            reports_dir=reports_dir,
            max_total_price=50,
            adapters={"mock": adapter},
            sources=["mock"],
        )
    )

    captured = capsys.readouterr()
    assert "mirror" in captured.out
    assert "Cheap mirror" in captured.out
    assert "Expensive mirror" not in captured.out
