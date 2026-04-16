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
        slug = query.strip().replace(" ", "+")
        return f"{self.base_url}/shop/search/{slug}"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        # Storeden platform: product cards in div.product_wrapper
        cards = await page.query_selector_all(".product_wrapper")

        for card in cards[:50]:
            try:
                listing = await self._parse_card(card)
                if listing:
                    results.append(listing)
            except Exception:
                continue
        return results

    async def _parse_card(self, card) -> RawListing | None:
        # Storeden: p.product_preview_title inside an <a> tag
        title_el = await card.query_selector(".product_preview_title")
        if not title_el:
            return None
        title = (await title_el.inner_text()).strip()
        if not title:
            return None

        # Link: a[href*='/product/']
        link_el = await card.query_selector("a[href*='/product/']")
        if not link_el:
            link_el = await card.query_selector("a[href]")
        if not link_el:
            return None
        href = await link_el.get_attribute("href") or ""
        if not href:
            return None
        listing_url = href if href.startswith("http") else f"{self.base_url}{href}"

        source_id = hashlib.md5(listing_url.encode()).hexdigest()[:12]

        # Price: span.final_price inside p.product_preview_price
        price = 0.0
        price_el = await card.query_selector(".final_price, .product_preview_price")
        if price_el:
            price_text = (await price_el.inner_text()).strip()
            price = self._parse_price(price_text)

        # Image: inside div.product_preview_img
        photos: list[str] = []
        img_el = await card.query_selector(".product_preview_img img, img[src]")
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
