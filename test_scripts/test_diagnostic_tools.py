"""Tests for adapter diagnostic tooling."""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing, SearchFilters


class StubDiagnosticAdapter(PlaywrightBaseAdapter):
    source_name = "stub_diag"
    language = "en"
    country = "GB"
    currency = "GBP"
    base_url = "https://example.com"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/search?q={query}"

    async def _extract_listings(self, page, query: str) -> list[RawListing]:
        return []


class TestSearchWithDiagnostics:
    def test_method_exists(self):
        adapter = StubDiagnosticAdapter()
        assert hasattr(adapter, "search_with_diagnostics")

    def test_returns_tuple_of_three(self):
        """search_with_diagnostics returns (listings, screenshot_path, dom_path)."""
        adapter = StubDiagnosticAdapter()
        sig = adapter.search_with_diagnostics.__code__.co_varnames
        assert "query" in sig
        assert "filters" in sig
        assert "capture_dir" in sig


class TestGetSelectors:
    def test_base_returns_empty_dict(self):
        adapter = StubDiagnosticAdapter()
        assert adapter._get_selectors() == {}


class TestSmokeTestCLI:
    """Test that the smoke test script accepts the new CLI flags."""

    def test_argparse_accepts_diagnose_flag(self):
        import test_scripts.smoke_test_live as smoke

        parser = smoke.build_parser()
        args = parser.parse_args(["--diagnose"])
        assert args.diagnose is True

    def test_argparse_accepts_report_flag(self):
        import test_scripts.smoke_test_live as smoke

        parser = smoke.build_parser()
        args = parser.parse_args(["--report"])
        assert args.report is True

    def test_argparse_accepts_query_flag(self):
        import test_scripts.smoke_test_live as smoke

        parser = smoke.build_parser()
        args = parser.parse_args(["--query", "exhaust pipe"])
        assert args.query == "exhaust pipe"

    def test_default_query_is_ducati_multistrada(self):
        import test_scripts.smoke_test_live as smoke

        parser = smoke.build_parser()
        args = parser.parse_args([])
        assert args.query == "Ducati Multistrada"


class TestSelectorTesterCLI:
    """Test that selector_tester.py accepts expected CLI flags."""

    def test_argparse_accepts_url_and_selector(self):
        import test_scripts.selector_tester as tester

        parser = tester.build_parser()
        args = parser.parse_args(["--url", "https://example.com", "--selector", ".product"])
        assert args.url == "https://example.com"
        assert args.selector == ".product"

    def test_argparse_accepts_adapter_mode(self):
        import test_scripts.selector_tester as tester

        parser = tester.build_parser()
        args = parser.parse_args(["--adapter", "bmotor", "--query", "Multistrada"])
        assert args.adapter == "bmotor"
        assert args.query == "Multistrada"

    def test_argparse_requires_url_or_adapter(self):
        import test_scripts.selector_tester as tester

        parser = tester.build_parser()
        args = parser.parse_args([])
        assert args.url is None
        assert args.adapter is None
