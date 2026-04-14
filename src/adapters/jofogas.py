"""Jofogas.hu adapter – Hungarian classifieds marketplace."""

import re
from urllib.parse import quote

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class JofogasAdapter(PlaywrightBaseAdapter):
    source_name = "jofogas"
    language = "hu"
    country = "HU"
    currency = "HUF"
    base_url = "https://www.jofogas.hu"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/magyarorszag?q={quote(query)}"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        cards = await page.query_selector_all("[data-testid='ad-card-general']")

        for card in cards[:50]:
            try:
                # Title from h5 (MUI Typography)
                title_el = await card.query_selector("h5")
                title = (await title_el.inner_text()).strip() if title_el else ""
                if not title:
                    continue

                # Link
                link_el = await card.query_selector("a[href*='jofogas.hu/']")
                if not link_el:
                    link_el = await card.query_selector("a[href]")
                href = await link_el.get_attribute("href") if link_el else ""
                listing_url = (
                    href if href and href.startswith("http")
                    else f"{self.base_url}{href}"
                )

                # Source ID from URL (e.g., .../__160038616.htm)
                source_id = ""
                if href:
                    match = re.search(r"__(\d+)\.htm", href)
                    if match:
                        source_id = match.group(1)
                    else:
                        source_id = href.rstrip("/").split("/")[-1].split(".")[-1]

                # Price from h3 (MUI Typography, displays the price number)
                price = 0.0
                price_el = await card.query_selector("h3")
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
        # Hungarian format: "300" (plain number) or "15 000" (space thousands)
        cleaned = text.replace("Ft", "").replace("HUF", "").strip()
        cleaned = re.sub(r"[^\d.,\s]", "", cleaned).strip()
        cleaned = cleaned.replace(" ", "")
        if not cleaned:
            return 0.0
        if "," in cleaned:
            cleaned = cleaned.replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
