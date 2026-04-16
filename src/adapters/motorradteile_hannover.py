"""Motorradteile Hannover adapter – German motorcycle breaker (motorradteilehannover.de).

Custom shop. Search via /search/?q=QUERY.
Focus on hard-to-find older model parts.
"""

import re
import hashlib
from urllib.parse import quote_plus

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class MotorradteileHannoverAdapter(PlaywrightBaseAdapter):
    source_name = "motorradteile_hannover"
    language = "de"
    country = "DE"
    currency = "EUR"
    base_url = "https://motorradteilehannover.de"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/search/?qs={quote_plus(query)}"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        # Try common product card selectors
        cards = await page.query_selector_all(
            ".product, .product-item, article, .item, [class*='product']"
        )
        if not cards:
            # Fallback: look for product links with images
            cards = await page.query_selector_all("a[href*='/product/'], a[href*='/Ducati']")

        seen_urls: set[str] = set()
        for card in cards[:50]:
            try:
                listing = await self._parse_element(card, seen_urls)
                if listing:
                    results.append(listing)
            except Exception:
                continue
        return results

    async def _parse_element(self, el, seen_urls: set) -> RawListing | None:
        # If it's a link itself
        tag = await el.evaluate("el => el.tagName.toLowerCase()")

        if tag == "a":
            href = await el.get_attribute("href") or ""
            title = (await el.inner_text()).strip()
        else:
            link_el = await el.query_selector("a[href]")
            if not link_el:
                return None
            href = await link_el.get_attribute("href") or ""
            title = (await link_el.inner_text()).strip()

        if not href or not title or len(title) < 3 or href in seen_urls:
            return None

        if not href.startswith("http"):
            href = f"{self.base_url}{href}"

        seen_urls.add(href)
        source_id = hashlib.md5(href.encode()).hexdigest()[:12]

        # Price
        price = 0.0
        price_el = await el.query_selector("[class*='price'], .price")
        if price_el:
            price_text = (await price_el.inner_text()).strip()
            price = self._parse_price(price_text)
        else:
            # Try extracting from full text
            full_text = await el.evaluate("el => el.textContent")
            price = self._parse_price(full_text)

        # Image
        photos: list[str] = []
        img_el = await el.query_selector("img[src]")
        if img_el:
            src = await img_el.get_attribute("src") or ""
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
            condition_label="Gebraucht",
            photos=photos,
            listing_url=href,
        )

    @staticmethod
    def _parse_price(text: str) -> float:
        if not text:
            return 0.0
        match = re.search(r"(\d[\d.,]*)\s*(?:€|EUR)", text)
        if not match:
            return 0.0
        cleaned = match.group(1)
        if "," in cleaned:
            parts = cleaned.split(",")
            integer_part = parts[0].replace(".", "")
            decimal_part = parts[1] if len(parts) > 1 else "0"
            try:
                return float(f"{integer_part}.{decimal_part}")
            except ValueError:
                return 0.0
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
