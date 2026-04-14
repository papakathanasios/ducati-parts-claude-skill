import os
import pytest
from src.core.config import load_config


def test_load_config_returns_bike_settings(tmp_path):
    config_yaml = tmp_path / "config.yaml"
    config_yaml.write_text("""
bike:
  default_model: "Multistrada 1260 Enduro"
  year_range: [2019, 2021]
  also_compatible:
    - "Multistrada 1260"

shipping:
  destination_country: "GR"
  destination_postal: "15562"
  destination_city: "Athens"
  shipping_ratio_warning: 0.5

search:
  default_tiers: [1, 2]
  max_results_per_source: 50
  currency_display: "EUR"

condition:
  min_score: "red"
  photo_required: false

watch:
  check_interval_hours: 4
  stale_listing_days: 30
  notification: "macos"

tiers:
  1:
    - olx_bg
    - olx_ro
  2:
    - subito_it
    - ebay_eu
  3:
    - kleinanzeigen_de
""")
    cfg = load_config(str(config_yaml))
    assert cfg.bike.default_model == "Multistrada 1260 Enduro"
    assert cfg.bike.year_range == [2019, 2021]
    assert cfg.shipping.destination_postal == "15562"
    assert cfg.search.default_tiers == [1, 2]
    assert cfg.condition.min_score == "red"
    assert cfg.watch.check_interval_hours == 4
    assert cfg.tiers[1] == ["olx_bg", "olx_ro"]
    assert cfg.tiers[3] == ["kleinanzeigen_de"]


def test_load_config_raises_on_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/config.yaml")


def test_load_config_raises_on_missing_required_section(tmp_path):
    config_yaml = tmp_path / "config.yaml"
    config_yaml.write_text("""
bike:
  default_model: "Test"
""")
    with pytest.raises(KeyError):
        load_config(str(config_yaml))
