import os

from src.adapters.registry import build_adapter_registry


def test_registry_returns_adapters():
    adapters = build_adapter_registry()
    assert len(adapters) >= 4  # OLX BG/RO/PL + Subito
    assert "olx_bg" in adapters
    assert "olx_ro" in adapters
    assert "olx_pl" in adapters
    assert "subito_it" in adapters


def test_registry_excludes_ebay_without_credentials(monkeypatch):
    """Without EBAY_APP_ID / EBAY_CERT_ID env vars, eBay should not be registered."""
    monkeypatch.delenv("EBAY_APP_ID", raising=False)
    monkeypatch.delenv("EBAY_CERT_ID", raising=False)
    adapters = build_adapter_registry()
    assert "ebay_eu" not in adapters


def test_registry_includes_ebay_with_credentials(monkeypatch):
    """With both eBay env vars set, eBay should be registered."""
    monkeypatch.setenv("EBAY_APP_ID", "test_app_id")
    monkeypatch.setenv("EBAY_CERT_ID", "test_cert_id")
    adapters = build_adapter_registry()
    assert "ebay_eu" in adapters
