import asyncio
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

from src.adapters.base import BaseAdapter
from src.core.condition import ConditionFilter
from src.core.config import AppConfig
from src.core.dedup import deduplicate
from src.core.shipping import ShippingEstimator
from src.core.types import (
    ConditionScore, CompatibilityConfidence,
    Listing, RawListing, SearchFilters,
)


class SearchOrchestrator:
    def __init__(self, config: AppConfig, adapters: dict[str, BaseAdapter]):
        self.config = config
        self.adapters = adapters
        self.condition_filter = ConditionFilter()
        self.shipping_estimator = ShippingEstimator(
            destination_postal=config.shipping.destination_postal,
            destination_country=config.shipping.destination_country,
        )
        self.last_errors: dict[str, str] = {}

    async def run(self, filters: SearchFilters) -> list[Listing]:
        self.last_errors = {}
        adapter_names: list[str] = []
        for tier in filters.tiers:
            adapter_names.extend(self.config.tiers.get(tier, []))
        if filters.sources:
            adapter_names = filters.sources

        tasks = {}
        for name in adapter_names:
            if name in self.adapters:
                tasks[name] = self.adapters[name].search(filters.query, filters)

        raw_results: list[RawListing] = []
        for name, coro in tasks.items():
            try:
                results = await coro
                raw_results.extend(results)
            except Exception as e:
                self.last_errors[name] = str(e)

        listings: list[Listing] = []
        for raw in raw_results:
            if self.condition_filter.should_exclude(raw.title, raw.description):
                continue
            normalized = self.condition_filter.normalize_label(raw.condition_label)
            if normalized.value == "excluded":
                continue

            if raw.shipping_price is not None:
                shipping = Decimal(str(raw.shipping_price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                shipping = self.shipping_estimator.midpoint(raw.seller_country)

            part_price = Decimal(str(raw.price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

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
            if filters.max_total_price and listing.total_price > filters.max_total_price:
                continue
            listings.append(listing)

        listings = deduplicate(listings)
        listings.sort(key=lambda l: (l.condition_score.value, l.total_price))
        return listings
