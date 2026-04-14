"""Njuskalo.hr adapter – Croatian classifieds marketplace.

Njuskalo and Bolha share the same platform (Styria Media Group).
The base extraction logic is shared via _StyriaPlatformBase.
"""

import re
import hashlib
from urllib.parse import quote

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class _StyriaPlatformBase(PlaywrightBaseAdapter):
    """Shared extraction logic for Njuskalo.hr and Bolha.com (same platform)."""

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        cards = await page.query_selector_all("li.EntityList-item--Regular")

        for card in cards[:50]:
            try:
                article = await card.query_selector("article.entity-body")
                if not article:
                    continue

                # Title from .entity-title a
                title_el = await article.query_selector(".entity-title a")
                title = (await title_el.inner_text()).strip() if title_el else ""
                if not title:
                    continue

                # Link
                href = await title_el.get_attribute("href") if title_el else ""
                listing_url = (
                    href if href and href.startswith("http")
                    else f"{self.base_url}{href}"
                )

                # Source ID from URL (e.g., ...-oglas-50310133)
                source_id = ""
                if href:
                    match = re.search(r"oglas-(\d+)", href)
                    if match:
                        source_id = match.group(1)
                    else:
                        source_id = href.rstrip("/").split("/")[-1]
                if not source_id:
                    source_id = hashlib.md5(listing_url.encode()).hexdigest()[:12]

                # Price from .price element inside .entity-prices
                price = 0.0
                price_el = await article.query_selector(
                    ".price, .entity-prices strong"
                )
                if price_el:
                    price_text = (await price_el.inner_text()).strip()
                    price = self._parse_price(price_text)

                # Description from .entity-description
                description = ""
                desc_el = await article.query_selector(".entity-description")
                if desc_el:
                    description = (await desc_el.inner_text()).strip()[:200]

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
                        description=description,
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
        cleaned = text.replace("€", "").replace("EUR", "").strip()
        cleaned = re.sub(r"[^\d.,]", "", cleaned)
        if not cleaned:
            return 0.0
        # Croatian/Slovenian format: 21.800 (dot = thousands)
        if "," in cleaned and "." in cleaned:
            if cleaned.rfind(",") > cleaned.rfind("."):
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        elif "." in cleaned:
            parts = cleaned.split(".")
            if len(parts) == 2 and len(parts[1]) == 3:
                cleaned = cleaned.replace(".", "")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0


class NjuskaloAdapter(_StyriaPlatformBase):
    source_name = "njuskalo"
    language = "hr"
    country = "HR"
    currency = "EUR"
    base_url = "https://www.njuskalo.hr"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/search/?keywords={quote(query)}"
