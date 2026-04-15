"""Tests for the 23 specialist Ducati shop/breaker adapters.

Each adapter must:
  - Expose correct source_name, country, currency class attributes.
  - Build a search URL that contains the marketplace domain.
  - Include a static _parse_price (or _extract_price) helper.
"""

import pytest

# Italian specialists
from src.adapters.desmomarket import DesmoMarketAdapter
from src.adapters.dgarageparts import DGaragePartsAdapter
from src.adapters.fresiamoto import FresiaMotAdapter
from src.adapters.motoricambi import MotoricambiAdapter
from src.adapters.eramotoricambi import EraMotoRicambiAdapter

# German specialists
from src.adapters.used_italian_parts import UsedItalianPartsAdapter
from src.adapters.ducbikeparts import DucBikePartsAdapter
from src.adapters.motorradteile_hannover import MotorradteileHannoverAdapter
from src.adapters.duc_store import DucStoreAdapter

# French specialists
from src.adapters.ital_allparts import ItalAllpartsAdapter
from src.adapters.forza_moto import ForzaMotoAdapter
from src.adapters.dezosmoto import DezosmotoAdapter
from src.adapters.speckmoto import SpeckMotoAdapter

# Spanish specialists
from src.adapters.motodesguace_ferrer import MotodesguaceFerrerAdapter
from src.adapters.motoye import MotoyeAdapter
from src.adapters.desguaces_pedros import DesguacesPedrosAdapter

# UK specialists
from src.adapters.ducatimondo import DucatiMondoAdapter
from src.adapters.motogrotto import MotoGrottoAdapter
from src.adapters.colchester_breakers import ColchesterBreakersAdapter
from src.adapters.cheshire_breakers import CheshireBreakersAdapter

# Hungarian specialists
from src.adapters.bmotor import BMotorAdapter
from src.adapters.maleducati import MaleDucatiAdapter

# Czech specialist
from src.adapters.ducatiparts_cz import DucatiPartsCzAdapter


# ---- property checks --------------------------------------------------------

@pytest.mark.parametrize("adapter_cls,source_name,country,currency,domain", [
    # Italy
    (DesmoMarketAdapter, "desmomarket", "IT", "EUR", "desmomarket.com"),
    (DGaragePartsAdapter, "dgarageparts", "IT", "EUR", "dgarageparts.com"),
    (FresiaMotAdapter, "fresiamoto", "IT", "EUR", "fresiamoto.it"),
    (MotoricambiAdapter, "motoricambi", "IT", "EUR", "motoricambicerignola.com"),
    (EraMotoRicambiAdapter, "eramotoricambi", "IT", "EUR", "eramotoricambi.it"),
    # Germany
    (UsedItalianPartsAdapter, "used_italian_parts", "DE", "EUR", "used-italian-parts.de"),
    (DucBikePartsAdapter, "ducbikeparts", "DE", "EUR", "ducbikeparts.de"),
    (MotorradteileHannoverAdapter, "motorradteile_hannover", "DE", "EUR", "motorradteilehannover.de"),
    (DucStoreAdapter, "duc_store", "DE", "EUR", "duc-store.de"),
    # France
    (ItalAllpartsAdapter, "ital_allparts", "FR", "EUR", "pieces-detachees-occasion-ducati.com"),
    (ForzaMotoAdapter, "forza_moto", "FR", "EUR", "forza-moto.com"),
    (DezosmotoAdapter, "dezosmoto", "FR", "EUR", "dezosmoto.fr"),
    (SpeckMotoAdapter, "speckmoto", "FR", "EUR", "speckmotospieces.com"),
    # Spain
    (MotodesguaceFerrerAdapter, "motodesguace_ferrer", "ES", "EUR", "motodesguacevferrer.es"),
    (MotoyeAdapter, "motoye", "ES", "EUR", "motoye.es"),
    (DesguacesPedrosAdapter, "desguaces_pedros", "ES", "EUR", "desguacespedros.es"),
    # UK
    (DucatiMondoAdapter, "ducatimondo", "GB", "GBP", "ducatimondo.co.uk"),
    (MotoGrottoAdapter, "motogrotto", "GB", "GBP", "motogrotto.co.uk"),
    (ColchesterBreakersAdapter, "colchester_breakers", "GB", "GBP", "colchesterbreakers.co.uk"),
    (CheshireBreakersAdapter, "cheshire_breakers", "GB", "GBP", "cheshirebikebreakers.com"),
    # Hungary
    (BMotorAdapter, "bmotor", "HU", "HUF", "bmotor.hu"),
    (MaleDucatiAdapter, "maleducati", "HU", "HUF", "maleducati.hu"),
    # Czech Republic
    (DucatiPartsCzAdapter, "ducatiparts_cz", "CZ", "CZK", "krejbichmeccanica.cz"),
])
def test_adapter_properties(adapter_cls, source_name, country, currency, domain):
    adapter = adapter_cls()
    assert adapter.source_name == source_name
    assert adapter.country == country
    assert adapter.currency == currency
    assert domain in adapter.base_url


# ---- search-URL checks ------------------------------------------------------

@pytest.mark.parametrize("adapter_cls,domain", [
    (DesmoMarketAdapter, "desmomarket.com"),
    (DGaragePartsAdapter, "dgarageparts.com"),
    (FresiaMotAdapter, "fresiamoto.it"),
    (MotoricambiAdapter, "motoricambicerignola.com"),
    (EraMotoRicambiAdapter, "eramotoricambi.it"),
    (UsedItalianPartsAdapter, "used-italian-parts.de"),
    (DucBikePartsAdapter, "ducbikeparts.de"),
    (MotorradteileHannoverAdapter, "motorradteilehannover.de"),
    (DucStoreAdapter, "duc-store.de"),
    (ItalAllpartsAdapter, "pieces-detachees-occasion-ducati.com"),
    (ForzaMotoAdapter, "forza-moto.com"),
    (DezosmotoAdapter, "dezosmoto.fr"),
    (SpeckMotoAdapter, "speckmotospieces.com"),
    (MotodesguaceFerrerAdapter, "motodesguacevferrer.es"),
    (MotoyeAdapter, "motoye.es"),
    (DesguacesPedrosAdapter, "desguacespedros.es"),
    (DucatiMondoAdapter, "ducatimondo.co.uk"),
    (MotoGrottoAdapter, "motogrotto.co.uk"),
    (ColchesterBreakersAdapter, "colchesterbreakers.co.uk"),
    (CheshireBreakersAdapter, "cheshirebikebreakers.com"),
    (BMotorAdapter, "bmotor.hu"),
    (MaleDucatiAdapter, "maleducati.hu"),
    (DucatiPartsCzAdapter, "krejbichmeccanica.cz"),
])
def test_adapter_search_url(adapter_cls, domain):
    adapter = adapter_cls()
    url = adapter._build_search_url("test exhaust")
    assert domain in url
    # BMotor uses AJAX search — URL is just the homepage
    if adapter_cls is not BMotorAdapter:
        assert "test" in url


# ---- EUR price parsing (Italian/German/French/Spanish format: 1.250,00) ------

EUR_ADAPTERS = [
    DesmoMarketAdapter, DGaragePartsAdapter, FresiaMotAdapter,
    MotoricambiAdapter, EraMotoRicambiAdapter,
    DucBikePartsAdapter, DucStoreAdapter,
    ItalAllpartsAdapter, ForzaMotoAdapter, DezosmotoAdapter, SpeckMotoAdapter,
    MotodesguaceFerrerAdapter, MotoyeAdapter, DesguacesPedrosAdapter,
]


@pytest.mark.parametrize("adapter_cls", EUR_ADAPTERS)
class TestEurParsePrice:
    def test_simple_integer(self, adapter_cls):
        assert adapter_cls._parse_price("100") == 100.0

    def test_comma_decimal(self, adapter_cls):
        assert adapter_cls._parse_price("49,90") == 49.90

    def test_thousands_with_dot_and_comma(self, adapter_cls):
        assert adapter_cls._parse_price("1.250,00") == 1250.0

    def test_with_euro_symbol(self, adapter_cls):
        assert adapter_cls._parse_price("€ 350,00") == 350.0

    def test_empty_returns_zero(self, adapter_cls):
        assert adapter_cls._parse_price("") == 0.0

    def test_garbage_returns_zero(self, adapter_cls):
        assert adapter_cls._parse_price("contact seller") == 0.0


# ---- GBP price parsing (UK format: 1,250.00) --------------------------------

GBP_ADAPTERS = [
    DucatiMondoAdapter, MotoGrottoAdapter,
    ColchesterBreakersAdapter, CheshireBreakersAdapter,
]


@pytest.mark.parametrize("adapter_cls", GBP_ADAPTERS)
class TestGbpParsePrice:
    def test_simple_integer(self, adapter_cls):
        assert adapter_cls._parse_price("100") == 100.0

    def test_with_pence(self, adapter_cls):
        assert adapter_cls._parse_price("49.90") == 49.90

    def test_thousands_with_comma(self, adapter_cls):
        assert adapter_cls._parse_price("1,250.00") == 1250.0

    def test_with_pound_symbol(self, adapter_cls):
        assert adapter_cls._parse_price("£350.00") == 350.0

    def test_empty_returns_zero(self, adapter_cls):
        assert adapter_cls._parse_price("") == 0.0

    def test_garbage_returns_zero(self, adapter_cls):
        assert adapter_cls._parse_price("contact seller") == 0.0


# ---- HUF price parsing (Hungarian format: 25 000 Ft) ------------------------

HUF_ADAPTERS = [BMotorAdapter, MaleDucatiAdapter]


@pytest.mark.parametrize("adapter_cls", HUF_ADAPTERS)
class TestHufParsePrice:
    def test_simple_integer(self, adapter_cls):
        assert adapter_cls._parse_price("5000") == 5000.0

    def test_with_spaces(self, adapter_cls):
        assert adapter_cls._parse_price("25 000 Ft") == 25000.0

    def test_with_dot_thousands(self, adapter_cls):
        assert adapter_cls._parse_price("25.000 Ft") == 25000.0

    def test_empty_returns_zero(self, adapter_cls):
        assert adapter_cls._parse_price("") == 0.0

    def test_garbage_returns_zero(self, adapter_cls):
        assert adapter_cls._parse_price("contact seller") == 0.0


# ---- CZK price parsing (Czech format: 1 250 Kc) -----------------------------

class TestCzkParsePrice:
    def test_simple_integer(self):
        assert DucatiPartsCzAdapter._parse_price("1250") == 1250.0

    def test_with_spaces_and_kc(self):
        assert DucatiPartsCzAdapter._parse_price("1 250 Kč") == 1250.0

    def test_with_comma_decimal(self):
        assert DucatiPartsCzAdapter._parse_price("1250,00 Kč") == 1250.0

    def test_thousands_with_dot(self):
        assert DucatiPartsCzAdapter._parse_price("1.250 Kč") == 1250.0

    def test_empty_returns_zero(self):
        assert DucatiPartsCzAdapter._parse_price("") == 0.0

    def test_garbage_returns_zero(self):
        assert DucatiPartsCzAdapter._parse_price("contact seller") == 0.0


# ---- Used Italian Parts uses _extract_price (regex-based) --------------------

class TestUsedItalianPartsExtractPrice:
    def test_eur_suffix(self):
        assert UsedItalianPartsAdapter._extract_price("79,90 EUR") == 79.90

    def test_euro_symbol(self):
        assert UsedItalianPartsAdapter._extract_price("Price: 250€") == 250.0

    def test_thousands(self):
        assert UsedItalianPartsAdapter._extract_price("1.250,00 EUR") == 1250.0

    def test_embedded_in_text(self):
        assert UsedItalianPartsAdapter._extract_price("Ducati part 350,00 EUR in stock") == 350.0

    def test_no_price_returns_zero(self):
        assert UsedItalianPartsAdapter._extract_price("no price here") == 0.0

    def test_empty_returns_zero(self):
        assert UsedItalianPartsAdapter._extract_price("") == 0.0


# ---- Motorradteile Hannover uses _parse_price (regex-based) ------------------

class TestMotorradteileParsePrice:
    def test_eur_suffix(self):
        assert MotorradteileHannoverAdapter._parse_price("79,90 EUR") == 79.90

    def test_euro_symbol(self):
        assert MotorradteileHannoverAdapter._parse_price("250€") == 250.0

    def test_thousands(self):
        assert MotorradteileHannoverAdapter._parse_price("1.250,00 EUR") == 1250.0

    def test_no_price_returns_zero(self):
        assert MotorradteileHannoverAdapter._parse_price("no price here") == 0.0

    def test_empty_returns_zero(self):
        assert MotorradteileHannoverAdapter._parse_price("") == 0.0


# ---- Registry includes all new adapters -------------------------------------

def test_registry_includes_all_specialists():
    from src.adapters.registry import build_adapter_registry
    adapters = build_adapter_registry()

    expected_keys = [
        # Italy
        "desmomarket", "dgarageparts", "fresiamoto", "motoricambi", "eramotoricambi",
        # Germany
        "used_italian_parts", "ducbikeparts", "motorradteile_hannover", "duc_store",
        # France
        "ital_allparts", "forza_moto", "dezosmoto", "speckmoto",
        # Spain
        "motodesguace_ferrer", "motoye", "desguaces_pedros",
        # UK
        "ducatimondo", "motogrotto", "colchester_breakers", "cheshire_breakers",
        # Hungary
        "bmotor", "maleducati",
        # Czech Republic
        "ducatiparts_cz",
    ]
    for key in expected_keys:
        assert key in adapters, f"Missing adapter: {key}"


# ---- Config tiers include all new adapters -----------------------------------

def test_config_tiers_include_specialists():
    import yaml
    with open("config/config.yaml") as f:
        config = yaml.safe_load(f)

    all_tier_adapters = []
    for tier_num in config["tiers"]:
        all_tier_adapters.extend(config["tiers"][tier_num])

    expected = [
        "bmotor", "maleducati", "ducatiparts_cz",
        "desmomarket", "dgarageparts", "fresiamoto", "motoricambi", "eramotoricambi",
        "used_italian_parts", "ducbikeparts", "motorradteile_hannover", "duc_store",
        "ital_allparts", "forza_moto", "dezosmoto", "speckmoto",
        "motodesguace_ferrer", "motoye", "desguaces_pedros",
        "ducatimondo", "motogrotto", "colchester_breakers", "cheshire_breakers",
    ]
    for key in expected:
        assert key in all_tier_adapters, f"Missing from config tiers: {key}"
