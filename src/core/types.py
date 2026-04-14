from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from enum import Enum


class ConditionScore(Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class CompatibilityConfidence(Enum):
    DEFINITE = "definite"
    LIKELY = "likely"
    VERIFY = "verify"


@dataclass
class RawListing:
    source_id: str
    source: str
    title: str
    description: str
    price: float
    currency: str
    shipping_price: float | None
    seller_country: str
    condition_label: str
    photos: list[str]
    listing_url: str


@dataclass
class Listing:
    id: str
    source: str
    title: str
    description: str
    part_price: Decimal
    shipping_price: Decimal
    currency_original: str
    seller_country: str
    is_eu: bool
    condition_raw: str
    condition_score: ConditionScore
    condition_notes: str
    photos: list[str]
    listing_url: str
    compatible_models: list[str]
    compatibility_confidence: CompatibilityConfidence
    oem_part_number: str
    date_listed: datetime
    date_found: datetime

    @property
    def total_price(self) -> Decimal:
        return self.part_price + self.shipping_price

    @property
    def shipping_ratio_flag(self) -> bool:
        if self.part_price == 0:
            return True
        return self.shipping_price / self.part_price > Decimal("0.5")


@dataclass
class SearchFilters:
    query: str
    max_total_price: Decimal | None = None
    tiers: list[int] = field(default_factory=lambda: [1, 2])
    target_models: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    oem_number: str | None = None
    part_category: str | None = None
