import re
import hashlib
from urllib.parse import quote_plus
from playwright.async_api import Page
from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class SubitoAdapter(PlaywrightBaseAdapter):
    source_name = "subito_it"
    language = "it"
    country = "IT"
    currency = "EUR"
    base_url = "https://www.subito.it"

    def _build_search_url(self, query: str) -> str:
        encoded_query = quote_plus(query)
        return f"{self.base_url}/annunci-italia/vendita/accessori-moto/?q={encoded_query}"

    def _parse_price(self, price_text: str) -> float:
        if not price_text:
            return 0.0

        cleaned = re.sub(r'[€\s]', '', price_text).strip()

        if not cleaned or not re.search(r'\d', cleaned):
            return 0.0

        # Italian number format: dots as thousands separator, comma as decimal
        if ',' in cleaned:
            parts = cleaned.split(',')
            integer_part = parts[0].replace('.', '')
            decimal_part = parts[1] if len(parts) > 1 else '0'
            try:
                return float(f"{integer_part}.{decimal_part}")
            except ValueError:
                return 0.0
        elif '.' in cleaned:
            integer_part = cleaned.replace('.', '')
            try:
                return float(integer_part)
            except ValueError:
                return 0.0
        else:
            try:
                return float(cleaned)
            except ValueError:
                return 0.0

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []

        # Current Subito DOM: article cards with module-based class names
        cards = await page.query_selector_all(
            "article[class*='index-module_card']"
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
        # Title from h3
        title_el = await card.query_selector("h3")
        title = (await title_el.inner_text()).strip() if title_el else ""
        if not title:
            return None

        # Link
        link_el = await card.query_selector("a[class*='index-module_link']")
        if not link_el:
            link_el = await card.query_selector("a[href]")
        listing_url = ""
        if link_el:
            listing_url = await link_el.get_attribute("href") or ""
        if not listing_url:
            return None
        if listing_url.startswith("/"):
            listing_url = f"{self.base_url}{listing_url}"

        # Source ID from URL
        source_id = hashlib.md5(listing_url.encode()).hexdigest()[:12]

        # Price from p with price class
        price = 0.0
        price_el = await card.query_selector("p[class*='price']")
        if price_el:
            price_text = (await price_el.inner_text()).strip()
            price = self._parse_price(price_text)

        # Image
        photos: list[str] = []
        img_el = await card.query_selector("img[src]")
        if img_el:
            img_url = await img_el.get_attribute("src")
            if img_url and not img_url.startswith("data:"):
                photos.append(img_url)

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
