import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.adapters.subito import SubitoAdapter
from src.core.types import SearchFilters


def test_subito_search_url():
    adapter = SubitoAdapter()
    url = adapter._build_search_url("leva frizione multistrada 1260")
    assert "subito.it" in url
    assert "multistrada" in url or "q=" in url


def test_subito_properties():
    adapter = SubitoAdapter()
    assert adapter.source_name == "subito_it"
    assert adapter.country == "IT"
    assert adapter.currency == "EUR"
    assert adapter.language == "it"


def test_subito_base_url():
    adapter = SubitoAdapter()
    assert adapter.base_url == "https://www.subito.it"


def test_subito_search_url_encodes_query():
    adapter = SubitoAdapter()
    url = adapter._build_search_url("leva freno ducati")
    assert "q=" in url
    assert "leva" in url
    assert "freno" in url
    assert "ducati" in url


def test_subito_search_url_format():
    adapter = SubitoAdapter()
    url = adapter._build_search_url("frizione")
    assert url.startswith("https://www.subito.it/annunci-italia/vendita/usato/")
    assert "q=frizione" in url


def test_subito_parse_price_simple():
    adapter = SubitoAdapter()
    assert adapter._parse_price("25") == 25.0
    assert adapter._parse_price("25,50") == 25.50


def test_subito_parse_price_italian_format():
    adapter = SubitoAdapter()
    assert adapter._parse_price("1.250,00") == 1250.0
    assert adapter._parse_price("1.250") == 1250.0
    assert adapter._parse_price("10.000,50") == 10000.50


def test_subito_parse_price_with_currency_symbol():
    adapter = SubitoAdapter()
    assert adapter._parse_price("25,00 \u20ac") == 25.0
    assert adapter._parse_price("\u20ac 1.250,00") == 1250.0


def test_subito_parse_price_edge_cases():
    adapter = SubitoAdapter()
    assert adapter._parse_price("") == 0.0
    assert adapter._parse_price("Prezzo su richiesta") == 0.0
    assert adapter._parse_price("Gratis") == 0.0


def test_subito_extract_listings_with_mock_page():
    adapter = SubitoAdapter()

    mock_card = MagicMock()
    mock_card.get_attribute = AsyncMock(return_value="https://www.subito.it/accessori-moto/leva-frizione-123456.htm")
    mock_card.query_selector = AsyncMock(side_effect=_mock_card_query_selector)

    mock_page = MagicMock()
    mock_page.query_selector_all = AsyncMock(return_value=[mock_card])

    results = asyncio.run(adapter._extract_listings(mock_page, "leva frizione"))

    assert len(results) == 1
    listing = results[0]
    assert listing.source == "subito_it"
    assert listing.seller_country == "IT"
    assert listing.currency == "EUR"
    assert listing.price == 45.0
    assert listing.title == "Leva frizione Ducati Multistrada 1260"
    assert listing.listing_url == "https://www.subito.it/accessori-moto/leva-frizione-123456.htm"


async def _mock_card_query_selector(selector: str):
    mock_el = MagicMock()
    if "title" in selector.lower() or "subject" in selector.lower() or "h2" in selector:
        mock_el.inner_text = AsyncMock(return_value="Leva frizione Ducati Multistrada 1260")
        return mock_el
    elif "price" in selector.lower() or "p" == selector.strip():
        mock_el.inner_text = AsyncMock(return_value="45,00 \u20ac")
        return mock_el
    elif "img" in selector.lower():
        mock_el.get_attribute = AsyncMock(return_value="https://img.subito.it/images/test.jpg")
        return mock_el
    return None


def test_subito_extract_listings_empty_page():
    adapter = SubitoAdapter()
    mock_page = MagicMock()
    mock_page.query_selector_all = AsyncMock(return_value=[])

    results = asyncio.run(adapter._extract_listings(mock_page, "nonexistent part"))
    assert results == []


def test_subito_extract_listings_handles_errors_gracefully():
    adapter = SubitoAdapter()

    mock_card = MagicMock()
    mock_card.get_attribute = AsyncMock(side_effect=Exception("element detached"))
    mock_card.query_selector = AsyncMock(return_value=None)

    mock_page = MagicMock()
    mock_page.query_selector_all = AsyncMock(return_value=[mock_card])

    results = asyncio.run(adapter._extract_listings(mock_page, "leva frizione"))
    assert results == []
