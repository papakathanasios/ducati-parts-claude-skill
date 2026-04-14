import base64
from typing import Any
import httpx
from src.adapters.base import BaseAdapter, AdapterHealthCheck
from src.core.types import RawListing, SearchFilters

EBAY_AUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
EBAY_MARKETPLACES = [("EBAY_IT", "it"), ("EBAY_DE", "de"), ("EBAY_FR", "fr"), ("EBAY_ES", "es"), ("EBAY_GB", "gb")]


class EbayAdapter(BaseAdapter):
    source_name = "ebay"
    language = "multi"
    country = "multi"
    currency = "multi"

    def __init__(self, app_id: str, cert_id: str):
        self.app_id = app_id
        self.cert_id = cert_id
        self._token: str | None = None

    async def _get_token(self) -> str:
        if self._token:
            return self._token
        credentials = base64.b64encode(f"{self.app_id}:{self.cert_id}".encode()).decode()
        async with httpx.AsyncClient() as client:
            resp = await client.post(EBAY_AUTH_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded", "Authorization": f"Basic {credentials}"},
                data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"}, timeout=10)
            resp.raise_for_status()
            self._token = resp.json()["access_token"]
            return self._token

    async def _api_search(self, query: str, marketplace: str, token: str, limit: int = 50) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(EBAY_SEARCH_URL,
                headers={"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": marketplace},
                params={"q": query, "filter": "conditions:{USED}", "limit": str(limit)}, timeout=15)
            resp.raise_for_status()
            return resp.json()

    async def search(self, query: str, filters: SearchFilters) -> list[RawListing]:
        token = await self._get_token()
        results: list[RawListing] = []
        seen_ids: set[str] = set()
        for marketplace_id, country_code in EBAY_MARKETPLACES:
            try:
                data = await self._api_search(query, marketplace_id, token)
                for item in data.get("itemSummaries", []):
                    item_id = item["itemId"]
                    if item_id in seen_ids:
                        continue
                    seen_ids.add(item_id)
                    shipping_price = None
                    shipping_opts = item.get("shippingOptions", [])
                    if shipping_opts:
                        cost = shipping_opts[0].get("shippingCost", {})
                        if cost:
                            shipping_price = float(cost.get("value", 0))
                    photos = []
                    image = item.get("image", {})
                    if image and image.get("imageUrl"):
                        photos.append(image["imageUrl"])
                    results.append(RawListing(
                        source_id=item_id, source=self.source_name,
                        title=item.get("title", ""), description=item.get("shortDescription", ""),
                        price=float(item["price"]["value"]), currency=item["price"]["currency"],
                        shipping_price=shipping_price,
                        seller_country=item.get("itemLocation", {}).get("country", country_code.upper()),
                        condition_label=item.get("condition", ""),
                        photos=photos, listing_url=item.get("itemWebUrl", "")))
            except Exception:
                continue
        return results

    async def health_check(self) -> AdapterHealthCheck:
        try:
            await self._get_token()
            return AdapterHealthCheck(healthy=True, message="eBay API authenticated")
        except Exception as e:
            return AdapterHealthCheck(healthy=False, message=str(e))
