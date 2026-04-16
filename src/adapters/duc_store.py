"""Duc-Store adapter – German Ducati specialist (duc-store.de).

ePages shop. Search via ?ViewAction=FacetedSearchProducts&SearchString=QUERY.
"""

import re
import hashlib
from urllib.parse import quote_plus

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class DucStoreAdapter(PlaywrightBaseAdapter):
    source_name = "duc_store"
    language = "de"
    country = "DE"
    currency = "EUR"
    base_url = "https://www.duc-store.de"

    def _build_search_url(self, query: str) -> str:
        return (
            f"{self.base_url}/?ViewAction=FacetedSearchProducts"
            f"&ObjectID=5152036&SearchString={quote_plus(query)}"
        )

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        # ePages: product cards are div.InfoArea
        cards = await page.query_selector_all("div.InfoArea")

        for card in cards[:50]:
            try:
                listing = await self._parse_card(card)
                if listing:
                    results.append(listing)
            except Exception:
                continue
        return results

    async def _parse_card(self, card) -> RawListing | None:
        # ePages: h3 > a for title and link
        link_el = await card.query_selector("h3 a")
        if not link_el:
            return None

        title = (await link_el.inner_text()).strip()
        href = await link_el.get_attribute("href") or ""
        if not title or not href:
            return None

        listing_url = href if href.startswith("http") else f"{self.base_url}/{href}"
        source_id = hashlib.md5(listing_url.encode()).hexdigest()[:12]

        # Price: span.Price > p.price-value > span[itemprop='price']
        price = 0.0
        price_el = await card.query_selector("p.price-value, span.Price")
        if price_el:
            price_text = (await price_el.inner_text()).strip()
            price = self._parse_price(price_text)

        # Image: img.ProductSmallImage
        photos: list[str] = []
        img_el = await card.query_selector("img.ProductSmallImage, img[src]")
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
