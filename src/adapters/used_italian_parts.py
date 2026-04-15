"""Used Italian Parts adapter – German Ducati specialist (used-italian-parts.de).

Zen-cart site. Search via /advanced_search_result.php?keywords=QUERY.
5,000+ used parts in stock.
"""

import re
import hashlib
from urllib.parse import quote_plus

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class UsedItalianPartsAdapter(PlaywrightBaseAdapter):
    source_name = "used_italian_parts"
    language = "de"
    country = "DE"
    currency = "EUR"
    base_url = "https://used-italian-parts.de"

    def _build_search_url(self, query: str) -> str:
        return (
            f"{self.base_url}/advanced_search_result.php"
            f"?keywords={quote_plus(query)}&inc_subcat=1"
        )

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        links = await page.query_selector_all('a[href*="product_info"]')

        seen_urls: set[str] = set()
        for link in links[:50]:
            try:
                href = await link.get_attribute("href") or ""
                if not href or href in seen_urls:
                    continue
                title = (await link.inner_text()).strip()
                if not title or len(title) < 3:
                    continue
                seen_urls.add(href)

                source_id = hashlib.md5(href.encode()).hexdigest()[:12]

                # Try to find price near the link
                parent = await link.evaluate_handle("el => el.closest('div, td, tr, li')")
                price = 0.0
                if parent:
                    parent_text = await parent.evaluate("el => el.textContent")
                    price = self._extract_price(parent_text)

                # Try to find image near the link
                photos: list[str] = []
                img = await link.query_selector("img")
                if img:
                    src = await img.get_attribute("src") or ""
                    if src and not src.startswith("data:"):
                        if not src.startswith("http"):
                            src = f"{self.base_url}/{src}"
                        photos.append(src)

                results.append(RawListing(
                    source_id=source_id,
                    source=self.source_name,
                    title=title,
                    description="",
                    price=price,
                    currency=self.currency,
                    shipping_price=None,
                    seller_country=self.country,
                    condition_label="Gebraucht",
                    photos=photos,
                    listing_url=href,
                ))
            except Exception:
                continue
        return results

    @staticmethod
    def _extract_price(text: str) -> float:
        if not text:
            return 0.0
        # Look for EUR price patterns: 79,90 EUR or 79.90€ or 79¤
        match = re.search(r"(\d[\d.,]*)\s*(?:€|EUR|¤)", text)
        if not match:
            return 0.0
        cleaned = match.group(1)
        if "," in cleaned:
            parts = cleaned.split(",")
            integer_part = parts[0].replace(".", "")
            decimal_part = parts[1] if len(parts) > 1 else "0"
            try:
                return float(f"{integer_part}.{decimal_part}")
            except ValueError:
                return 0.0
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
