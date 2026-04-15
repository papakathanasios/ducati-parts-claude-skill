"""Tests for the 10 skeleton browser adapters (Task 21).

Each adapter must:
  - Expose correct source_name, country, currency class attributes.
  - Build a search URL that contains the marketplace domain.
  - Include a static _parse_price helper.
"""

import pytest

from src.adapters.kleinanzeigen import KleinanzeigenAdapter
from src.adapters.leboncoin import LeboncoinAdapter
from src.adapters.wallapop import WallapopAdapter
from src.adapters.allegro import AllegroAdapter
from src.adapters.jofogas import JofogasAdapter
from src.adapters.bazos import BazosCzAdapter, BazosSkAdapter
from src.adapters.njuskalo import NjuskaloAdapter
from src.adapters.bolha import BolhaAdapter
from src.adapters.moto_breakers import MotoBreakersAdapter


# ---- property checks --------------------------------------------------------

@pytest.mark.parametrize("adapter_cls,source_name,country,currency,domain", [
    (KleinanzeigenAdapter, "kleinanzeigen", "DE", "EUR", "kleinanzeigen.de"),
    (LeboncoinAdapter, "leboncoin", "FR", "EUR", "leboncoin.fr"),
    (WallapopAdapter, "wallapop", "ES", "EUR", "wallapop.com"),
    (AllegroAdapter, "allegro", "PL", "PLN", "allegro.pl"),
    (JofogasAdapter, "jofogas", "HU", "HUF", "jofogas.hu"),
    (BazosCzAdapter, "bazos_cz", "CZ", "CZK", "bazos.cz"),
    (BazosSkAdapter, "bazos_sk", "SK", "EUR", "bazos.sk"),
    (NjuskaloAdapter, "njuskalo", "HR", "EUR", "njuskalo.hr"),
    (BolhaAdapter, "bolha", "SI", "EUR", "bolha.com"),
    (MotoBreakersAdapter, "moto_breakers", "GB", "GBP", "moto-breakers.co.uk"),
])
def test_adapter_properties(adapter_cls, source_name, country, currency, domain):
    adapter = adapter_cls()
    assert adapter.source_name == source_name
    assert adapter.country == country
    assert adapter.currency == currency
    assert domain in adapter.base_url


# ---- search-URL checks ------------------------------------------------------

@pytest.mark.parametrize("adapter_cls,domain", [
    (KleinanzeigenAdapter, "kleinanzeigen.de"),
    (LeboncoinAdapter, "leboncoin.fr"),
    (WallapopAdapter, "wallapop.com"),
    (AllegroAdapter, "allegro.pl"),
    (JofogasAdapter, "jofogas.hu"),
    (BazosCzAdapter, "bazos.cz"),
    (BazosSkAdapter, "bazos.sk"),
    (NjuskaloAdapter, "njuskalo.hr"),
    (BolhaAdapter, "bolha.com"),
    (MotoBreakersAdapter, "moto-breakers.co.uk"),
])
def test_adapter_search_url(adapter_cls, domain):
    adapter = adapter_cls()
    url = adapter._build_search_url("test query")
    assert domain in url
    assert "test" in url


# ---- _parse_price checks ----------------------------------------------------

@pytest.mark.parametrize("adapter_cls", [
    KleinanzeigenAdapter, LeboncoinAdapter, WallapopAdapter,
    AllegroAdapter, JofogasAdapter, BazosCzAdapter, BazosSkAdapter,
    NjuskaloAdapter, BolhaAdapter,
    MotoBreakersAdapter,
])
class TestParsePrice:
    def test_simple_integer(self, adapter_cls):
        assert adapter_cls._parse_price("100") == 100.0

    def test_with_currency_symbol(self, adapter_cls):
        assert adapter_cls._parse_price("€ 1.250,00") == 1250.0

    def test_comma_decimal(self, adapter_cls):
        assert adapter_cls._parse_price("49,90 €") == 49.90

    def test_garbage_returns_zero(self, adapter_cls):
        assert adapter_cls._parse_price("contact seller") == 0.0

    def test_empty_returns_zero(self, adapter_cls):
        assert adapter_cls._parse_price("") == 0.0
