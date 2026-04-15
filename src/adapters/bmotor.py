"""BMotor adapter – Hungarian motorcycle breaker (bmotor.hu).

Budapest-based. Search via /keresese?search=QUERY.
1-month warranty on parts.
"""

import re
import hashlib
from urllib.parse import quote_plus

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class BMotorAdapter(PlaywrightBaseAdapter):
    source_name = "bmotor"
    language = "hu"
    country = "HU"
    currency = "HUF"
    base_url = "https://www.bmotor.hu"

    def _build_search_url(self, query: str) -> str:
        # ShopRenter uses JS search; navigate to home and use the search input
        return self.base_url

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        # ShopRenter search is AJAX-based — fill the search input and trigger it
        search_input = await page.query_selector(
            "input.disableAutocomplete[type='text'], "
            "input[placeholder*='keres'], #search input[type='text']"
        )
        if search_input:
            await search_input.fill(query)
            search_btn = await page.query_selector("#search_btn, button.btn:has(i.fa-search)")
            if search_btn:
                await search_btn.click()
            else:
                await search_input.press("Enter")
            # Wait for AJAX results
            try:
                await page.wait_for_selector(
                    ".search-results a, #results a, .product-item",
                    timeout=10000,
                )
            except Exception:
                pass

        results: list[RawListing] = []
        # Search results appear in the #results div or as product items
        cards = await page.query_selector_all(
            "#results a[href], .search-results a[href], "
            ".product-item, .product-card"
        )

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
        # Look for title link
        title_el = await card.query_selector(
            "a[href*='/ducati'], a[href*='/product'], h2 a, h3 a, "
            ".product-title a, .product-name a, a.product-link"
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

        # Price (HUF format: 25 000 Ft or 25.000 Ft)
        price = 0.0
        price_el = await card.query_selector("[class*='price'], .price, .product-price")
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
            condition_label="Használt",
            photos=photos,
            listing_url=listing_url,
        )

    @staticmethod
    def _parse_price(text: str) -> float:
        if not text:
            return 0.0
        # Remove currency symbols and whitespace
        cleaned = re.sub(r"[Ft\s\xa0]", "", text, flags=re.IGNORECASE).strip()
        # Remove thousands separator (space or dot)
        cleaned = cleaned.replace(".", "").replace(",", "").replace(" ", "")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
