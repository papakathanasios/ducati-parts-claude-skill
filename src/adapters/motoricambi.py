"""Motoricambi Cerignola adapter – Italian motorcycle breaker (motoricambicerignola.com).

Magento site. Search via /catalogsearch/result/?q=QUERY.
"""

import re
import hashlib
from urllib.parse import quote_plus

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class MotoricambiAdapter(PlaywrightBaseAdapter):
    source_name = "motoricambi"
    language = "it"
    country = "IT"
    currency = "EUR"
    base_url = "https://www.motoricambicerignola.com"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/catalogsearch/result/?q={quote_plus(query)}"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        cards = await page.query_selector_all("li.item.product-item")

        for card in cards[:50]:
            try:
                listing = await self._parse_card(card)
                if listing:
                    results.append(listing)
            except Exception:
                continue
        return results

    async def _parse_card(self, card) -> RawListing | None:
        # Title from product link
        title_el = await card.query_selector("a.product-item-link")
        if not title_el:
            return None
        title = (await title_el.inner_text()).strip()
        if not title:
            return None

        listing_url = await title_el.get_attribute("href") or ""
        if not listing_url:
            return None

        source_id = hashlib.md5(listing_url.encode()).hexdigest()[:12]

        # Price
        price = 0.0
        price_el = await card.query_selector(".price-box .price")
        if price_el:
            price_text = (await price_el.inner_text()).strip()
            price = self._parse_price(price_text)

        # Image (Magento lazy loads, try data-src first)
        photos: list[str] = []
        img_el = await card.query_selector("img.product-image-photo")
        if img_el:
            src = await img_el.get_attribute("data-src") or await img_el.get_attribute("src") or ""
            if src and not src.startswith("data:") and "lazyloading" not in src:
                photos.append(src)

        return RawListing(
            source_id=source_id,
            source=self.source_name,
            title=title,
            description="",
            price=price,
            currency=self.currency,
            shipping_price=None,
            seller_country=self.country,
            condition_label="Usato",
            photos=photos,
            listing_url=listing_url,
        )

    @staticmethod
    def _parse_price(text: str) -> float:
        if not text:
            return 0.0
        cleaned = re.sub(r"[€\s]", "", text).strip()
        if not cleaned:
            return 0.0
        if "," in cleaned:
            parts = cleaned.split(",")
            integer_part = parts[0].replace(".", "")
            decimal_part = parts[1] if len(parts) > 1 else "0"
            try:
                return float(f"{integer_part}.{decimal_part}")
            except ValueError:
                return 0.0
        cleaned = cleaned.replace(".", "")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
