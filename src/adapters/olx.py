import re
from urllib.parse import quote
from playwright.async_api import Page
from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class OlxBgAdapter(PlaywrightBaseAdapter):
    source_name = "olx_bg"
    language = "bg"
    country = "BG"
    currency = "BGN"
    base_url = "https://www.olx.bg"
    _search_path = "/ads/q-{query}/"

    def _build_search_url(self, query: str) -> str:
        slug = query.strip().replace(" ", "-")
        path = self._search_path.format(query=slug)
        return f"{self.base_url}{path}"

    @staticmethod
    def _parse_price(text: str, default_currency: str) -> tuple[float, str]:
        """Extract numeric price and currency from OLX price text.

        Handles formats like '150 лв.', '200 RON', '350 zł', 'Безплатно', etc.
        Returns (price, currency) tuple; returns (0.0, default_currency) for
        free/unparseable values.
        """
        if not text:
            return 0.0, default_currency

        cleaned = text.strip()

        currency_map = {
            "лв": "BGN",
            "лв.": "BGN",
            "bgn": "BGN",
            "ron": "RON",
            "lei": "RON",
            "zł": "PLN",
            "pln": "PLN",
            "eur": "EUR",
            "€": "EUR",
        }

        # Remove thousands separators and normalise decimal point
        cleaned_num = cleaned.replace(" ", "")
        # Find all digit groups (with possible comma/dot separators)
        price_match = re.search(r"[\d]+(?:[.,\s]\d{3})*(?:[.,]\d{1,2})?", cleaned)
        if not price_match:
            return 0.0, default_currency

        price_str = price_match.group()
        # Normalise: if last separator is comma followed by 1-2 digits, treat as decimal
        if re.search(r",\d{1,2}$", price_str):
            price_str = price_str.replace(".", "").replace(",", ".")
        else:
            price_str = price_str.replace(",", "").replace(" ", "")

        try:
            price = float(price_str)
        except ValueError:
            return 0.0, default_currency

        # Detect currency from remaining text
        remainder = cleaned.lower()
        detected_currency = default_currency
        for token, cur in currency_map.items():
            if token in remainder:
                detected_currency = cur
                break

        return price, detected_currency

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        cards = await page.query_selector_all("[data-cy='l-card']")
        results: list[RawListing] = []

        for card in cards:
            try:
                # Title
                title_el = await card.query_selector("h6")
                title = (await title_el.inner_text()).strip() if title_el else ""
                if not title:
                    continue

                # Link and listing URL
                link_el = await card.query_selector("a")
                href = await link_el.get_attribute("href") if link_el else ""
                listing_url = href if href and href.startswith("http") else f"{self.base_url}{href}"

                # Skip OLX "last resort" results (irrelevant fallback listings)
                if "extended_search_no_results_last_resort" in listing_url:
                    continue

                # Skip OLX cross-site redirects (autovit, otomoto, storia, etc.)
                if href and not href.startswith("/") and self.base_url not in href:
                    continue

                # Source ID from URL or data attribute
                source_id = ""
                data_id = await card.get_attribute("data-id")
                if data_id:
                    source_id = data_id
                elif href:
                    id_match = re.search(r"-ID(\w+)\.html", href)
                    if id_match:
                        source_id = id_match.group(1)
                    else:
                        source_id = href.rstrip("/").split("/")[-1]

                # Price
                price_el = await card.query_selector("[data-testid='ad-price']")
                price_text = (await price_el.inner_text()).strip() if price_el else ""
                price, currency = self._parse_price(price_text, self.currency)

                # Photo
                photos: list[str] = []
                img_el = await card.query_selector("img")
                if img_el:
                    src = await img_el.get_attribute("src")
                    if src and not src.startswith("data:"):
                        photos.append(src)

                # Location / condition (OLX shows location, not condition)
                location_el = await card.query_selector("[data-testid='location-date']")
                condition_label = ""
                if location_el:
                    condition_label = (await location_el.inner_text()).strip()

                results.append(RawListing(
                    source_id=source_id,
                    source=self.source_name,
                    title=title,
                    description="",
                    price=price,
                    currency=currency,
                    shipping_price=None,
                    seller_country=self.country,
                    condition_label=condition_label,
                    photos=photos,
                    listing_url=listing_url,
                ))
            except Exception:
                continue

        return results


class OlxRoAdapter(OlxBgAdapter):
    source_name = "olx_ro"
    language = "ro"
    country = "RO"
    currency = "RON"
    base_url = "https://www.olx.ro"
    _search_path = "/oferte/q-{query}/"


class OlxPlAdapter(OlxBgAdapter):
    source_name = "olx_pl"
    language = "pl"
    country = "PL"
    currency = "PLN"
    base_url = "https://www.olx.pl"
    _search_path = "/oferty/q-{query}/"
