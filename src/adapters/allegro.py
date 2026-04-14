"""Allegro.pl adapter – Polish marketplace."""

import re
from urllib.parse import quote

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class AllegroAdapter(PlaywrightBaseAdapter):
    source_name = "allegro"
    language = "pl"
    country = "PL"
    currency = "PLN"
    base_url = "https://allegro.pl"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/listing?string={quote(query)}"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        cards = await page.query_selector_all(
            "[class*='opbox-listing'] article"
        )

        for card in cards[:50]:
            try:
                # Title from h2
                title_el = await card.query_selector("h2")
                title = (await title_el.inner_text()).strip() if title_el else ""
                if not title:
                    continue

                # Link to offer
                link_el = await card.query_selector("a[href*='oferta']")
                if not link_el:
                    link_el = await card.query_selector("a[href]")
                href = await link_el.get_attribute("href") if link_el else ""
                listing_url = (
                    href if href and href.startswith("http")
                    else f"{self.base_url}{href}"
                )

                # Source ID from URL
                source_id = ""
                if href:
                    # Allegro URLs end with the item ID
                    parts = href.rstrip("/").split("-")
                    if parts:
                        source_id = parts[-1]

                # Price from aria-label containing "cena"
                price = 0.0
                price_el = await card.query_selector("[aria-label*='cena']")
                if price_el:
                    price_text = (await price_el.inner_text()).strip()
                    price = self._parse_price(price_text)

                # Image
                photos: list[str] = []
                img_el = await card.query_selector("img")
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
        cleaned = text.lower().replace("zł", "").strip()
        cleaned = re.sub(r"[^\d.,]", "", cleaned)
        if not cleaned:
            return 0.0
        # Polish format: 1 250,00 or 1.250,00
        if "," in cleaned and "." in cleaned:
            if cleaned.rfind(",") > cleaned.rfind("."):
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
