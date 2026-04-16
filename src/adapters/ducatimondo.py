"""Ducati Mondo adapter – UK Ducati specialist (ducatimondo.co.uk).

Magento site. Search via /store/catalogsearch/result/?q=QUERY.
"""

import re
import hashlib
from urllib.parse import quote_plus

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class DucatiMondoAdapter(PlaywrightBaseAdapter):
    source_name = "ducatimondo"
    language = "en"
    country = "GB"
    currency = "GBP"
    base_url = "https://www.ducatimondo.co.uk"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/store/catalogsearch/result/?q={quote_plus(query)}"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        # Magento 1.x: products in ul.products-list > li or ul.products-grid > li
        cards = await page.query_selector_all(
            ".products-list li, .products-grid li, .product-info"
        )

        for card in cards[:50]:
            try:
                listing = await self._parse_card(card)
                if listing:
                    results.append(listing)
            except Exception:
                continue
        return results

    async def _parse_card(self, card) -> RawListing | None:
        # Magento 1.x: h2.product-name > a
        title_el = await card.query_selector(".product-name a, h2 a, a.product-name")
        if not title_el:
            return None
        title = (await title_el.inner_text()).strip()
        if not title:
            return None

        listing_url = await title_el.get_attribute("href") or ""
        if not listing_url:
            return None

        source_id = hashlib.md5(listing_url.encode()).hexdigest()[:12]

        price = 0.0
        # Magento 1.x: .price-box .price, .regular-price .price, .special-price .price
        price_el = await card.query_selector(".price-box .price, .regular-price .price, .special-price .price")
        if price_el:
            price_text = (await price_el.inner_text()).strip()
            price = self._parse_price(price_text)

        photos: list[str] = []
        img_el = await card.query_selector(".product-image img, img[src]")
        if img_el:
            src = await img_el.get_attribute("src") or ""
            if src and not src.startswith("data:"):
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
            condition_label="Used",
            photos=photos,
            listing_url=listing_url,
        )

    @staticmethod
    def _parse_price(text: str) -> float:
        if not text:
            return 0.0
        cleaned = re.sub(r"[£$€\s]", "", text).strip()
        if not cleaned:
            return 0.0
        # UK format: 1,250.00
        if "." in cleaned and "," in cleaned:
            cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
