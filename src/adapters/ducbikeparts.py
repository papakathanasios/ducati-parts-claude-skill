"""DucBikeParts adapter – German Ducati specialist (ducbikeparts.de).

WooCommerce + Bricks Builder site. Search via /?s=QUERY&post_type=product.
"""

import re
import hashlib
from urllib.parse import quote_plus

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class DucBikePartsAdapter(PlaywrightBaseAdapter):
    source_name = "ducbikeparts"
    language = "de"
    country = "DE"
    currency = "EUR"
    base_url = "https://ducbikeparts.de"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/?s={quote_plus(query)}&post_type=product"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        cards = await page.query_selector_all("li.product")

        for card in cards[:50]:
            try:
                listing = await self._parse_card(card)
                if listing:
                    results.append(listing)
            except Exception:
                continue
        return results

    async def _parse_card(self, card) -> RawListing | None:
        # Title from h3 heading link (Bricks builder)
        title_el = await card.query_selector("h3 a, .fb-woo-card-one__heading a")
        if not title_el:
            return None
        title = (await title_el.inner_text()).strip()
        if not title:
            return None

        listing_url = await title_el.get_attribute("href") or ""
        if not listing_url:
            return None

        source_id = hashlib.md5(listing_url.encode()).hexdigest()[:12]

        # Price from .price or .amount span
        price = 0.0
        price_el = await card.query_selector(".price, .woocommerce-Price-amount, .amount")
        if price_el:
            price_text = (await price_el.inner_text()).strip()
            price = self._parse_price(price_text)

        # Image (lazy-loaded)
        photos: list[str] = []
        img_el = await card.query_selector("img[data-src], img[src]")
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
            condition_label="Gebraucht",
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
        # German format: 1.250,00
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
