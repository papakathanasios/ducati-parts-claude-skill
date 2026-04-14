"""Wallapop.com adapter – Spanish classifieds marketplace."""

import re
import hashlib
from urllib.parse import quote

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class WallapopAdapter(PlaywrightBaseAdapter):
    source_name = "wallapop"
    language = "es"
    country = "ES"
    currency = "EUR"
    base_url = "https://es.wallapop.com"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/app/search?keywords={quote(query)}"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        cards = await page.query_selector_all("a[href*='/item/']")

        for card in cards[:50]:
            try:
                # The card itself is an <a> element
                href = await card.get_attribute("href") or ""
                listing_url = (
                    href if href.startswith("http")
                    else f"{self.base_url}{href}"
                )

                # Title from h3 or class containing "title"
                title = ""
                title_el = await card.query_selector(
                    "h3, [class*='ItemCard__title']"
                )
                if title_el:
                    title = (await title_el.inner_text()).strip()
                if not title:
                    title = (await card.get_attribute("aria-label") or "").strip()
                if not title:
                    continue

                # Source ID from URL (e.g., /item/felpa-ducati-1252403705)
                source_id = ""
                if href:
                    parts = href.rstrip("/").split("-")
                    if parts and parts[-1].isdigit():
                        source_id = parts[-1]
                if not source_id:
                    source_id = hashlib.md5(listing_url.encode()).hexdigest()[:12]

                # Price
                price = 0.0
                price_el = await card.query_selector(
                    "[class*='ItemCard__price'], strong"
                )
                if price_el:
                    price_text = (await price_el.inner_text()).strip()
                    price = self._parse_price(price_text)

                # Image
                photos: list[str] = []
                img_el = await card.query_selector("img[src]")
                if img_el:
                    src = await img_el.get_attribute("src")
                    if src and not src.startswith("data:"):
                        photos.append(src)

                results.append(
                    RawListing(
                        source_id=source_id,
                        source=self.source_name,
                        title=title,
                        description="",
                        price=price,
                        currency=self.currency,
                        shipping_price=None,
                        seller_country=self.country,
                        condition_label="",
                        photos=photos,
                        listing_url=listing_url,
                    )
                )
            except Exception:
                continue
        return results

    @staticmethod
    def _parse_price(text: str) -> float:
        if not text:
            return 0.0
        cleaned = text.replace("€", "").strip()
        cleaned = re.sub(r"[^\d.,]", "", cleaned)
        if not cleaned:
            return 0.0
        # Spanish format: 1.250,00 or 1.250
        if "," in cleaned and "." in cleaned:
            if cleaned.rfind(",") > cleaned.rfind("."):
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", ".")
        elif "." in cleaned:
            parts = cleaned.split(".")
            if len(parts) == 2 and len(parts[1]) == 3:
                cleaned = cleaned.replace(".", "")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
