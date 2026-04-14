import asyncio
import logging
import re
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

from src.adapters.base import BaseAdapter
from src.core.condition import ConditionFilter
from src.core.config import AppConfig
from src.core.currency import CurrencyConverter
from src.core.dedup import deduplicate
from src.core.query_expansion import expand_query
from src.core.shipping import ShippingEstimator
from src.core.types import (
    ConditionScore, CompatibilityConfidence,
    Listing, RawListing, SearchFilters,
)

logger = logging.getLogger(__name__)

_WORD_SPLIT = re.compile(r"[^a-z0-9\u0400-\u04ff\u0100-\u024f]+")


def _is_relevant(title: str, description: str, original_query: str, translated_query: str) -> bool:
    original_words = {w for w in _WORD_SPLIT.split(original_query.lower()) if len(w) >= 3}
    translated_words = {w for w in _WORD_SPLIT.split(translated_query.lower()) if len(w) >= 3}
    all_query_words = original_words | translated_words
    listing_text = f"{title} {description}".lower()
    return any(word in listing_text for word in all_query_words)


class SearchOrchestrator:
    def __init__(self, config: AppConfig, adapters: dict[str, BaseAdapter]):
        self.config = config
        self.adapters = adapters
        self.condition_filter = ConditionFilter()
        self.shipping_estimator = ShippingEstimator(
            destination_postal=config.shipping.destination_postal,
            destination_country=config.shipping.destination_country,
        )
        self.currency_converter = CurrencyConverter()
        self.last_errors: dict[str, str] = {}

    async def run(self, filters: SearchFilters) -> list[Listing]:
        self.last_errors = {}

        await self.currency_converter.fetch_rates()

        adapter_names: list[str] = []
        for tier in filters.tiers:
            adapter_names.extend(self.config.tiers.get(tier, []))
        if filters.sources:
            adapter_names = filters.sources

        selected: dict[str, BaseAdapter] = {}
        for name in adapter_names:
            if name in self.adapters:
                selected[name] = self.adapters[name]

        translated_queries: dict[str, str] = {}
        for name, adapter in selected.items():
            translated_queries[name] = expand_query(
                filters.query,
                adapter.language,
                overrides=filters.translations,
            )

        timeout = self.config.search.adapter_timeout_seconds

        async def _search_adapter(name: str, adapter: BaseAdapter) -> list[RawListing]:
            query = translated_queries[name]
            return await asyncio.wait_for(
                adapter.search(query, filters),
                timeout=timeout,
            )

        coros = {name: _search_adapter(name, adapter) for name, adapter in selected.items()}
        results = await asyncio.gather(*coros.values(), return_exceptions=True)

        raw_results: list[RawListing] = []
        for name, result in zip(coros.keys(), results):
            if isinstance(result, Exception):
                self.last_errors[name] = str(result)
            else:
                raw_results.extend(result)

        listings: list[Listing] = []
        for raw in raw_results:
            adapter_translated = translated_queries.get(raw.source, filters.query)

            if not _is_relevant(raw.title, raw.description, filters.query, adapter_translated):
                continue
            if self.condition_filter.should_exclude(raw.title, raw.description):
                continue
            normalized = self.condition_filter.normalize_label(raw.condition_label)
            if normalized.value == "excluded":
                continue

            part_price_raw = Decimal(str(raw.price))
            currency = raw.currency.upper()
            if currency != "EUR" and self.currency_converter._rates_available:
                try:
                    part_price = self.currency_converter.convert(part_price_raw, currency)
                except KeyError:
                    logger.warning("Unsupported currency %s for listing %s", currency, raw.source_id)
                    part_price = part_price_raw
            else:
                part_price = part_price_raw
            part_price = part_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            if raw.shipping_price is not None:
                shipping = Decimal(str(raw.shipping_price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                shipping = self.shipping_estimator.midpoint(raw.seller_country)

            if raw.photos:
                condition_score = ConditionScore.GREEN if normalized.value in ("excellent", "good") else ConditionScore.YELLOW
            else:
                condition_score = ConditionScore.YELLOW
            if normalized.value == "fair":
                condition_score = ConditionScore.RED

            listing = Listing(
                id=f"{raw.source}_{raw.source_id}",
                source=raw.source, title=raw.title, description=raw.description,
                part_price=part_price, shipping_price=shipping,
                currency_original=raw.currency, seller_country=raw.seller_country,
                is_eu=self.shipping_estimator.is_eu(raw.seller_country),
                condition_raw=raw.condition_label, condition_score=condition_score,
                condition_notes=f"Normalized: {normalized.value}",
                photos=raw.photos, listing_url=raw.listing_url,
                compatible_models=[], compatibility_confidence=CompatibilityConfidence.VERIFY,
                oem_part_number="", date_listed=datetime.now(), date_found=datetime.now(),
            )

            if filters.max_total_price:
                if currency != "EUR" and not self.currency_converter._rates_available:
                    pass
                elif listing.total_price > filters.max_total_price:
                    continue

            listings.append(listing)

        listings = deduplicate(listings)
        listings.sort(key=lambda l: (l.condition_score.value, l.total_price))
        return listings
