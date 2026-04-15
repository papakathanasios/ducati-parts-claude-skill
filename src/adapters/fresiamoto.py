"""Fresia Moto adapter – Italian motorcycle breaker (fresiamoto.it).

Custom e-commerce. Search via /shop/search/?search=QUERY.
Dismantles bikes in-house, free IT shipping.
"""

import re
import hashlib
from urllib.parse import quote_plus

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class FresiaMotAdapter(PlaywrightBaseAdapter):
    source_name = "fresiamoto"
    language = "it"
    country = "IT"
    currency = "EUR"
    base_url = "https://www.fresiamoto.it"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/shop/search/?search={quote_plus(query)}"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        # Try common product card selectors for this custom shop
        cards = await page.query_selector_all("[class*='product']")
        if not cards:
            cards = await page.query_selector_all(".item, article, .card")

        for card in cards[:50]:
            try:
                listing = await self._parse_card(card)
                if listing:
                    results.append(listing)
            except Exception:
                continue
        return results

    async def _parse_card(self, card) -> RawListing | None:
        # Title from heading or link text
        title = ""
        for sel in ["h2 a", "h3 a", ".product-title a", ".product-name a", "a[href*='/shop/']"]:
            el = await card.query_selector(sel)
            if el:
                title = (await el.inner_text()).strip()
                if title and len(title) > 3:
                    break
        if not title:
            return None

        # Link
        link_el = await card.query_selector("a[href*='/shop/']")
        if not link_el:
            link_el = await card.query_selector("a[href]")
        if not link_el:
            return None
        href = await link_el.get_attribute("href") or ""
        if not href:
            return None
        listing_url = href if href.startswith("http") else f"{self.base_url}{href}"

        source_id = hashlib.md5(listing_url.encode()).hexdigest()[:12]

        # Price
        price = 0.0
        price_el = await card.query_selector("[class*='price'], .product-price")
        if price_el:
            price_text = (await price_el.inner_text()).strip()
            price = self._parse_price(price_text)

        # Image
        photos: list[str] = []
        img_el = await card.query_selector("img[src]")
        if img_el:
            src = await img_el.get_attribute("src")
            if src and not src.startswith("data:"):
                if not src.startswith("http"):
                    src = f"{self.base_url}{src}"
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
