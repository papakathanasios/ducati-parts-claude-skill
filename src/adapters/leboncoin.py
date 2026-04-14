"""Leboncoin.fr adapter – French classifieds marketplace."""

import re
import hashlib
from urllib.parse import quote

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class LeboncoinAdapter(PlaywrightBaseAdapter):
    source_name = "leboncoin"
    language = "fr"
    country = "FR"
    currency = "EUR"
    base_url = "https://www.leboncoin.fr"

    def _build_search_url(self, query: str) -> str:
        # category=44 = Equipement moto (motorcycle equipment/parts)
        return f"{self.base_url}/recherche?text={quote(query)}&category=44&u_car_brand=ducati"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        cards = await page.query_selector_all("article")

        for card in cards[:50]:
            try:
                # Link with title from span[title]
                link_el = await card.query_selector("a[href*='/ad/']")
                if not link_el:
                    continue

                href = await link_el.get_attribute("href") or ""
                listing_url = (
                    href if href.startswith("http")
                    else f"{self.base_url}{href}"
                )

                # Title from the span with title attribute inside the link
                title = ""
                title_span = await link_el.query_selector("span[title]")
                if title_span:
                    title = (await title_span.get_attribute("title") or "").strip()
                    # Title often starts with "Voir l'annonce: "
                    if title.startswith("Voir l'annonce: "):
                        title = title[len("Voir l'annonce: "):]

                if not title:
                    continue

                # Source ID from URL path (e.g., /ad/equipement_moto/3058160325)
                source_id = href.rstrip("/").split("/")[-1] if href else ""
                if not source_id:
                    source_id = hashlib.md5(listing_url.encode()).hexdigest()[:12]

                # Price from sr-only text or visible price element
                price = 0.0
                # Try visible price first
                price_els = await card.query_selector_all("p")
                for p_el in price_els:
                    p_text = (await p_el.inner_text()).strip()
                    if "€" in p_text and len(p_text) < 30:
                        price = self._parse_price(p_text)
                        if price > 0:
                            break

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
        cleaned = text.replace("€", "").replace("Prix:", "").strip()
        cleaned = re.sub(r"[^\d.,\s]", "", cleaned).strip()
        if not cleaned:
            return 0.0
        # French format: 1 250,00 or 1.250,00
        cleaned = cleaned.replace(" ", "")
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
