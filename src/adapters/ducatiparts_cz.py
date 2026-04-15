"""DucatiParts.cz (Krejbich Meccanica) adapter – Czech Ducati specialist.

Site redirects to eshop.krejbichmeccanica.cz.
Search via /vyhledavani?code=QUERY (custom platform).
OEM + used parts, also MV Agusta service.
"""

import re
import hashlib
from urllib.parse import quote_plus

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class DucatiPartsCzAdapter(PlaywrightBaseAdapter):
    source_name = "ducatiparts_cz"
    language = "cs"
    country = "CZ"
    currency = "CZK"
    base_url = "https://eshop.krejbichmeccanica.cz"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/vyhledavani?code={quote_plus(query)}"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        cards = await page.query_selector_all("div.product-container")

        for card in cards[:50]:
            try:
                listing = await self._parse_card(card)
                if listing:
                    results.append(listing)
            except Exception:
                continue
        return results

    async def _parse_card(self, card) -> RawListing | None:
        title_el = await card.query_selector(".product-title")
        if not title_el:
            return None
        title = (await title_el.inner_text()).strip()
        if not title:
            return None

        link_el = await card.query_selector("a[href*='/produkt']")
        if not link_el:
            link_el = await card.query_selector("a[href]")
        if not link_el:
            return None
        href = await link_el.get_attribute("href") or ""
        if not href:
            return None
        listing_url = href if href.startswith("http") else f"{self.base_url}{href}"

        source_id = hashlib.md5(listing_url.encode()).hexdigest()[:12]

        price = 0.0
        price_el = await card.query_selector(".product-price, [class*='price']")
        if price_el:
            price_text = (await price_el.inner_text()).strip()
            price = self._parse_price(price_text)

        photos: list[str] = []
        img_el = await card.query_selector("img[src], img[data-src]")
        if img_el:
            src = await img_el.get_attribute("data-src") or await img_el.get_attribute("src") or ""
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
            condition_label="Použité",
            photos=photos,
            listing_url=listing_url,
        )

    @staticmethod
    def _parse_price(text: str) -> float:
        if not text:
            return 0.0
        # CZK format: 1 250 Kč or 1.250 Kč or 1250,00 Kč
        cleaned = re.sub(r"[Kč€\s\xa0]", "", text, flags=re.IGNORECASE).strip()
        if not cleaned:
            return 0.0
        # Handle Czech number format
        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            parts = cleaned.split(",")
            integer_part = parts[0].replace(".", "").replace(" ", "")
            decimal_part = parts[1] if len(parts) > 1 else "0"
            cleaned = f"{integer_part}.{decimal_part}"
        else:
            cleaned = cleaned.replace(".", "").replace(" ", "")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
