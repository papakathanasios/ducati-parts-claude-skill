"""MaleDucati adapter – Hungarian Ducati specialist (ducatiwebshop.maleducati.hu).

Ducati and CNC Racing dealer. New + used parts.
Search via /tcskereso?search=QUERY.
"""

import re
import hashlib
from urllib.parse import quote_plus

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class MaleDucatiAdapter(PlaywrightBaseAdapter):
    source_name = "maleducati"
    language = "hu"
    country = "HU"
    currency = "HUF"
    base_url = "https://ducatiwebshop.maleducati.hu"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/tlista_altalanos_kereso?din_altalanos_kifejezes={quote_plus(query)}"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        # Search results are in .termek_sor_lista_tarto containers
        cards = await page.query_selector_all(".termek_sor_lista_tarto")

        seen_urls: set[str] = set()
        for card in cards[:50]:
            try:
                listing = await self._parse_card(card, seen_urls)
                if listing:
                    results.append(listing)
            except Exception:
                continue
        return results

    async def _parse_card(self, card, seen_urls: set) -> RawListing | None:
        # Product name link
        title_el = await card.query_selector(
            "a.blokk_lista_termek_nev_link, a.termek_sor_lista_nev"
        )
        if not title_el:
            return None

        title = (await title_el.inner_text()).strip()
        if not title or len(title) < 3:
            return None

        href = await title_el.get_attribute("href") or ""
        if not href or href in seen_urls:
            return None

        listing_url = href if href.startswith("http") else f"{self.base_url}{href}"
        seen_urls.add(href)
        source_id = hashlib.md5(listing_url.encode()).hexdigest()[:12]

        # Price (uses &nbsp; separated values like "27 000 Ft")
        price = 0.0
        price_el = await card.query_selector(
            ".blokk_lista_uj_ar, .blokk_lista_uj_ar_2, .termek_sor_lista_ar"
        )
        if price_el:
            price_text = (await price_el.inner_text()).strip()
            price = self._parse_price(price_text)

        photos: list[str] = []
        img_el = await card.query_selector("img.lista_kep, img[src]")
        if img_el:
            src = await img_el.get_attribute("src") or ""
            if src and not src.startswith("data:"):
                if not src.startswith("http"):
                    src = f"{self.base_url}/{src}"
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
            condition_label="Használt",
            photos=photos,
            listing_url=listing_url,
        )

    def _get_selectors(self) -> dict[str, list[str]]:
        return {
            "product_cards": [
                ".termek_sor_lista_tarto",
            ],
            "title": [
                "a.blokk_lista_termek_nev_link",
                "a.termek_sor_lista_nev",
            ],
            "price": [
                ".blokk_lista_uj_ar",
                ".blokk_lista_uj_ar_2",
                ".termek_sor_lista_ar",
            ],
        }

    @staticmethod
    def _parse_price(text: str) -> float:
        if not text:
            return 0.0
        cleaned = re.sub(r"[Ft\s\xa0]", "", text, flags=re.IGNORECASE).strip()
        cleaned = cleaned.replace(".", "").replace(",", "").replace(" ", "")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
