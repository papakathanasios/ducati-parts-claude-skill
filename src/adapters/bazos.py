"""Bazos adapters – Czech (bazos.cz) and Slovak (bazos.sk) classifieds."""

import re
from urllib.parse import quote

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class _BazosBase(PlaywrightBaseAdapter):
    """Shared extraction logic for both bazos.cz and bazos.sk."""

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        cards = await page.query_selector_all("div.inzeraty")

        for card in cards[:50]:
            try:
                # Title from h2.nadpis > a
                title_el = await card.query_selector(".nadpis a")
                title = (await title_el.inner_text()).strip() if title_el else ""
                if not title:
                    continue

                # Link (full URL on bazos, e.g., https://motorky.bazos.cz/inzerat/...)
                href = await title_el.get_attribute("href") if title_el else ""
                listing_url = (
                    href if href and href.startswith("http")
                    else f"{self.base_url}{href}"
                )

                # Source ID from URL (e.g., .../inzerat/217101759/...)
                source_id = ""
                if href:
                    match = re.search(r"/inzerat/(\d+)/", href)
                    if match:
                        source_id = match.group(1)
                    else:
                        source_id = href.rstrip("/").split("/")[-1].split(".")[0]

                # Price from .inzeratycena
                price = 0.0
                price_el = await card.query_selector(".inzeratycena")
                if price_el:
                    price_text = (await price_el.inner_text()).strip()
                    price = self._parse_price(price_text)

                # Description from .popis
                description = ""
                desc_el = await card.query_selector(".popis")
                if desc_el:
                    description = (await desc_el.inner_text()).strip()[:200]

                # Image
                photos: list[str] = []
                img_el = await card.query_selector("img.obrazek")
                if not img_el:
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
        # Czech/Slovak format: "280 000 Kč" or "150 €"
        cleaned = (
            text.replace("Kč", "")
            .replace("€", "")
            .replace("EUR", "")
            .replace("CZK", "")
            .strip()
        )
        cleaned = re.sub(r"[^\d.,\s]", "", cleaned).strip()
        cleaned = cleaned.replace(" ", "")
        if not cleaned:
            return 0.0
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


class BazosCzAdapter(_BazosBase):
    source_name = "bazos_cz"
    language = "cs"
    country = "CZ"
    currency = "CZK"
    base_url = "https://www.bazos.cz"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/search.php?hledat={quote(query)}"


class BazosSkAdapter(_BazosBase):
    source_name = "bazos_sk"
    language = "sk"
    country = "SK"
    currency = "EUR"
    base_url = "https://www.bazos.sk"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/search.php?hledat={quote(query)}"
