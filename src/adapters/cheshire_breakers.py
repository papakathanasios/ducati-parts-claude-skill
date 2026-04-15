"""Cheshire Bike Breakers adapter (cheshirebikebreakers.com).

25 years experience. Fully licensed.
Search via /?s=QUERY&post_type=product.
"""

import re
import hashlib
from urllib.parse import quote_plus

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class CheshireBreakersAdapter(PlaywrightBaseAdapter):
    source_name = "cheshire_breakers"
    language = "en"
    country = "GB"
    currency = "GBP"
    base_url = "https://cheshirebikebreakers.com"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/?s={quote_plus(query)}&post_type=product"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        cards = await page.query_selector_all(
            "li.product, .type-product, article.product, .product-card"
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
        title_el = await card.query_selector(
            ".woocommerce-loop-product__title, h2, h3"
        )
        if not title_el:
            return None
        title = (await title_el.inner_text()).strip()
        if not title:
            return None

        link_el = await card.query_selector("a[href*='/product'], a[href]")
        if not link_el:
            return None
        listing_url = await link_el.get_attribute("href") or ""
        if not listing_url:
            return None
        if not listing_url.startswith("http"):
            listing_url = f"{self.base_url}{listing_url}"

        source_id = hashlib.md5(listing_url.encode()).hexdigest()[:12]

        price = 0.0
        price_el = await card.query_selector(".woocommerce-Price-amount, .price, .amount")
        if price_el:
            price_text = (await price_el.inner_text()).strip()
            price = self._parse_price(price_text)

        photos: list[str] = []
        img_el = await card.query_selector("img[src], img[data-src]")
        if img_el:
            src = await img_el.get_attribute("data-src") or await img_el.get_attribute("src") or ""
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
        if "." in cleaned and "," in cleaned:
            cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
