from decimal import Decimal
from datetime import datetime
from src.core.types import (
    Listing, RawListing, SearchFilters,
    ConditionScore, CompatibilityConfidence,
)


def test_listing_total_price_calculation():
    listing = Listing(
        id="ebay_123", source="ebay", title="Clutch lever Multistrada",
        description="Good condition", part_price=Decimal("25.00"),
        shipping_price=Decimal("10.00"), currency_original="EUR",
        seller_country="IT", is_eu=True, condition_raw="Good",
        condition_score=ConditionScore.GREEN, condition_notes="Clean part, good photos",
        photos=["https://example.com/photo1.jpg"], listing_url="https://ebay.it/item/123",
        compatible_models=["Multistrada 1260 Enduro", "Multistrada 1260"],
        compatibility_confidence=CompatibilityConfidence.DEFINITE,
        oem_part_number="63040601A", date_listed=datetime(2026, 4, 10),
        date_found=datetime(2026, 4, 14),
    )
    assert listing.total_price == Decimal("35.00")
    assert listing.shipping_ratio_flag is False


def test_listing_shipping_ratio_flag_triggered():
    listing = Listing(
        id="olx_456", source="olx_bg", title="Lever", description="OK",
        part_price=Decimal("10.00"), shipping_price=Decimal("15.00"),
        currency_original="BGN", seller_country="BG", is_eu=True,
        condition_raw="", condition_score=ConditionScore.YELLOW,
        condition_notes="No photos", photos=[], listing_url="https://olx.bg/item/456",
        compatible_models=["Multistrada 1260 Enduro"],
        compatibility_confidence=CompatibilityConfidence.VERIFY,
        oem_part_number="", date_listed=datetime(2026, 4, 12),
        date_found=datetime(2026, 4, 14),
    )
    assert listing.total_price == Decimal("25.00")
    assert listing.shipping_ratio_flag is True


def test_search_filters_defaults():
    filters = SearchFilters(query="clutch lever")
    assert filters.max_total_price is None
    assert filters.tiers == [1, 2]
    assert filters.target_models == []
    assert filters.sources == []


def test_search_filters_translations_default_none():
    f = SearchFilters(query="exhaust")
    assert f.translations is None

def test_search_filters_max_price_hint_default_none():
    f = SearchFilters(query="exhaust")
    assert f.max_price_hint is None

def test_search_filters_with_translations():
    f = SearchFilters(query="exhaust", translations={"bg": "ауспух", "it": "scarico"})
    assert f.translations["bg"] == "ауспух"
    assert f.translations["it"] == "scarico"

def test_search_filters_with_max_price_hint():
    from decimal import Decimal
    f = SearchFilters(query="exhaust", max_price_hint=Decimal("400"))
    assert f.max_price_hint == Decimal("400")


def test_raw_listing_creation():
    raw = RawListing(
        source_id="123", source="ebay", title="Test part", description="A part",
        price=25.50, currency="EUR", shipping_price=10.0, seller_country="IT",
        condition_label="Good", photos=["https://example.com/p1.jpg"],
        listing_url="https://ebay.it/123",
    )
    assert raw.source_id == "123"
    assert raw.price == 25.50
