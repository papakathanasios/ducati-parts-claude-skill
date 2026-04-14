from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class BikeConfig:
    default_model: str
    year_range: list[int]
    also_compatible: list[str]


@dataclass
class ShippingConfig:
    destination_country: str
    destination_postal: str
    destination_city: str
    shipping_ratio_warning: float


@dataclass
class SearchConfig:
    default_tiers: list[int]
    max_results_per_source: int
    currency_display: str


@dataclass
class ConditionConfig:
    min_score: str
    photo_required: bool


@dataclass
class WatchConfig:
    check_interval_hours: int
    stale_listing_days: int
    notification: str


@dataclass
class AppConfig:
    bike: BikeConfig
    shipping: ShippingConfig
    search: SearchConfig
    condition: ConditionConfig
    watch: WatchConfig
    tiers: dict[int, list[str]]


def load_config(config_path: str) -> AppConfig:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    required_sections = ["bike", "shipping", "search", "condition", "watch", "tiers"]
    for section in required_sections:
        if section not in raw:
            raise KeyError(f"Missing required config section: {section}")

    return AppConfig(
        bike=BikeConfig(**raw["bike"]),
        shipping=ShippingConfig(**raw["shipping"]),
        search=SearchConfig(**raw["search"]),
        condition=ConditionConfig(**raw["condition"]),
        watch=WatchConfig(**raw["watch"]),
        tiers={int(k): v for k, v in raw["tiers"].items()},
    )
