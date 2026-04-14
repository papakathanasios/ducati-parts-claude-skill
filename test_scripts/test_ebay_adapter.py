import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.adapters.ebay import EbayAdapter
from src.core.types import SearchFilters

MOCK_SEARCH_RESPONSE = {
    "itemSummaries": [
        {
            "itemId": "v1|123456|0",
            "title": "Ducati Multistrada 1260 Clutch Lever OEM",
            "price": {"value": "25.00", "currency": "EUR"},
            "condition": "Used",
            "seller": {"username": "moto_parts_it"},
            "itemLocation": {"country": "IT"},
            "shippingOptions": [{"shippingCost": {"value": "12.00", "currency": "EUR"}}],
            "image": {"imageUrl": "https://i.ebayimg.com/images/g/test/s-l1600.jpg"},
            "itemWebUrl": "https://www.ebay.it/itm/123456",
            "shortDescription": "OEM clutch lever for Ducati Multistrada 1260. Good condition.",
        },
        {
            "itemId": "v1|789012|0",
            "title": "Broken Ducati lever for parts",
            "price": {"value": "5.00", "currency": "EUR"},
            "condition": "For parts or not working",
            "seller": {"username": "seller2"},
            "itemLocation": {"country": "DE"},
            "shippingOptions": [],
            "image": {"imageUrl": "https://i.ebayimg.com/images/g/test2/s-l1600.jpg"},
            "itemWebUrl": "https://www.ebay.de/itm/789012",
            "shortDescription": "Broken, sold as is.",
        },
    ],
    "total": 2,
}


def test_ebay_adapter_parses_search_results():
    adapter = EbayAdapter(app_id="test_id", cert_id="test_cert")
    with patch.object(adapter, '_get_token', new_callable=AsyncMock, return_value="test_token"):
        with patch.object(adapter, '_api_search', new_callable=AsyncMock, return_value=MOCK_SEARCH_RESPONSE):
            filters = SearchFilters(query="clutch lever multistrada 1260")
            results = asyncio.run(adapter.search("clutch lever multistrada 1260", filters))
    assert len(results) == 2
    assert results[0].source_id == "v1|123456|0"
    assert results[0].source == "ebay"
    assert results[0].price == 25.00
    assert results[0].shipping_price == 12.00
    assert results[0].seller_country == "IT"
    assert results[0].condition_label == "Used"
    assert len(results[0].photos) == 1


def test_ebay_adapter_handles_missing_shipping():
    adapter = EbayAdapter(app_id="test_id", cert_id="test_cert")
    with patch.object(adapter, '_get_token', new_callable=AsyncMock, return_value="test_token"):
        with patch.object(adapter, '_api_search', new_callable=AsyncMock, return_value=MOCK_SEARCH_RESPONSE):
            results = asyncio.run(adapter.search("lever", SearchFilters(query="lever")))
    assert results[1].shipping_price is None


def test_ebay_adapter_health_check():
    adapter = EbayAdapter(app_id="test_id", cert_id="test_cert")
    with patch.object(adapter, '_get_token', new_callable=AsyncMock, return_value="test_token"):
        health = asyncio.run(adapter.health_check())
        assert health.healthy is True
    with patch.object(adapter, '_get_token', new_callable=AsyncMock, side_effect=Exception("auth failed")):
        health = asyncio.run(adapter.health_check())
        assert health.healthy is False
