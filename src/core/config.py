import os
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
    adapter_timeout_seconds: int = 30


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

    search_data = raw["search"]
    search_config = SearchConfig(
        default_tiers=search_data["default_tiers"],
        max_results_per_source=search_data["max_results_per_source"],
        currency_display=search_data["currency_display"],
        adapter_timeout_seconds=search_data.get("adapter_timeout_seconds", 30),
    )

    bike_data = raw["bike"]
    bike_model_env = os.environ.get("BIKE_MODEL")
    if bike_model_env:
        bike_data["default_model"] = bike_model_env

    return AppConfig(
        bike=BikeConfig(**bike_data),
        shipping=ShippingConfig(**raw["shipping"]),
        search=search_config,
        condition=ConditionConfig(**raw["condition"]),
        watch=WatchConfig(**raw["watch"]),
        tiers={int(k): v for k, v in raw["tiers"].items()},
    )
