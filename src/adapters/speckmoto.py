"""Speck Moto Pieces adapter – French motorcycle breaker (speckmotospieces.com).

Magento site. Search via /fr/catalogsearch/result/?q=QUERY.
"""

import re
import hashlib
from urllib.parse import quote_plus

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class SpeckMotoAdapter(PlaywrightBaseAdapter):
    source_name = "speckmoto"
    language = "fr"
    country = "FR"
    currency = "EUR"
    base_url = "https://www.speckmotospieces.com"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/fr/catalogsearch/result/?q={quote_plus(query)}"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        # Magento 2: product cards in div.product-item-info
        cards = await page.query_selector_all(".product-item-info")

        for card in cards[:50]:
            try:
                listing = await self._parse_card(card)
                if listing:
                    results.append(listing)
            except Exception:
                continue
        return results

    async def _parse_card(self, card) -> RawListing | None:
        # Magento 2: a.product-item-link inside strong.product-item-name
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

        price = 0.0
        # Magento 2: .price-final_price .price or .price-box .price
        price_el = await card.query_selector(".price-final_price .price, .price-box .price, .special-price .price")
        if price_el:
            price_text = (await price_el.inner_text()).strip()
            price = self._parse_price(price_text)

        photos: list[str] = []
        # Magento 2: img.product-image-photo
        img_el = await card.query_selector("img.product-image-photo")
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
            condition_label="Occasion",
            photos=photos,
            listing_url=listing_url,
        )

    @staticmethod
    def _parse_price(text: str) -> float:
        if not text:
            return 0.0
        cleaned = re.sub(r"[€\s\xa0]", "", text).strip()
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
        try:
            return float(cleaned.replace(".", ""))
        except ValueError:
            return 0.0
