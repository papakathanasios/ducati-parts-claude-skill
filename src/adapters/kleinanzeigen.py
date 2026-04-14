"""Kleinanzeigen.de adapter – German classifieds marketplace."""

import re
from urllib.parse import quote

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class KleinanzeigenAdapter(PlaywrightBaseAdapter):
    source_name = "kleinanzeigen"
    language = "de"
    country = "DE"
    currency = "EUR"
    base_url = "https://www.kleinanzeigen.de"

    def _build_search_url(self, query: str) -> str:
        # c306 = Motorradteile & Zubehör category
        return f"{self.base_url}/s-motorraeder-roller-teile/{quote(query)}/k0c306"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        cards = await page.query_selector_all("article.aditem")

        for card in cards[:50]:
            try:
                # Title
                title_el = await card.query_selector(".text-module-begin a.ellipsis")
                if not title_el:
                    title_el = await card.query_selector("a.ellipsis")
                title = (await title_el.inner_text()).strip() if title_el else ""

                # Link
                link_el = title_el or await card.query_selector("a[href]")
                href = await link_el.get_attribute("href") if link_el else ""
                listing_url = (
                    href if href and href.startswith("http")
                    else f"{self.base_url}{href}"
                )

                # Source ID from data-adid attribute
                source_id = await card.get_attribute("data-adid") or ""
                if not source_id and href:
                    source_id = href.rstrip("/").split("/")[-1]

                # Price
                price_el = await card.query_selector(
                    ".aditem-main--middle--price-shipping--price"
                )
                price_text = (await price_el.inner_text()).strip() if price_el else ""
                price = self._parse_price(price_text)

                # Image
                photos: list[str] = []
                img_el = await card.query_selector("img")
                if img_el:
                    src = await img_el.get_attribute("src")
                    if src and not src.startswith("data:"):
                        photos.append(src)

                # Location info as condition label
                location_el = await card.query_selector(
                    ".aditem-main--top--left, .aditem-main--top"
                )
                condition_label = ""
                if location_el:
                    condition_label = (await location_el.inner_text()).strip()

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
                        condition_label=condition_label,
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
        cleaned = text.replace("€", "").replace("VB", "").strip()
        # German format: 1.250 (dot = thousands), or 1.250,00
        cleaned = re.sub(r"[^\d.,]", "", cleaned)
        if not cleaned:
            return 0.0
        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", ".")
        elif "." in cleaned:
            # Dot only: if 3 digits after dot it's thousands separator
            parts = cleaned.split(".")
            if len(parts) == 2 and len(parts[1]) == 3:
                cleaned = cleaned.replace(".", "")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
