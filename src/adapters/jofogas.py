"""Jofogas.hu adapter – Hungarian classifieds marketplace."""

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
        return f"{self.base_url}/keres/{quote(query)}"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        # Skeleton: CSS selectors need refinement during live testing
        cards = await page.query_selector_all(
            "[class*='item'], [class*='card'], article"
        )
        for card in cards[:50]:
            try:
                title_el = await card.query_selector("h2, h3, [class*='title']")
                title = await title_el.inner_text() if title_el else ""

                price_el = await card.query_selector("[class*='price']")
                price_text = await price_el.inner_text() if price_el else "0"
                price = self._parse_price(price_text)

                link_el = await card.query_selector("a")
                href = await link_el.get_attribute("href") if link_el else ""
                listing_url = (
                    href if href and href.startswith("http") else f"{self.base_url}{href}"
                )

                img_el = await card.query_selector("img")
                photo_url = await img_el.get_attribute("src") if img_el else ""
                photos = [photo_url] if photo_url else []

                results.append(
                    RawListing(
                        source_id=(
                            href.split("/")[-1].split(".")[0]
                            if href
                            else str(len(results))
                        ),
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
        cleaned = "".join(c for c in text if c.isdigit() or c in ".,")
        if not cleaned:
            return 0.0
        if "," in cleaned and "." in cleaned:
            if cleaned.rfind(",") > cleaned.rfind("."):
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        else:
            cleaned = cleaned.replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
