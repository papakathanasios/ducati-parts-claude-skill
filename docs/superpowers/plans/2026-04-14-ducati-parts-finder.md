# Ducati Parts Finder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code skill that finds used Ducati Multistrada 1260 Enduro parts across 15+ European marketplaces, prioritizing cheap Eastern EU sources, with condition assessment, watch lists, and macOS notifications.

**Architecture:** Project-local Claude Code skill (SKILL.md) orchestrates a Python backend. The Python backend handles marketplace scraping (eBay API + Playwright for browser-automated sites), condition filtering, shipping estimation, currency conversion, and report generation. A SQLite database stores watches, seen listings, and the parts compatibility catalog. macOS launchd schedules periodic watch checks.

**Tech Stack:** Python 3.12+, UV package manager, httpx, Playwright, BeautifulSoup4, Jinja2, SQLite3, PyYAML, python-dotenv, Pillow

**Spec:** `docs/superpowers/specs/2026-04-14-ducati-parts-finder-design.md`

---

## Phase 1: Project Foundation

Sets up the project scaffold, configuration loading, database layer, and core data types. After this phase you can load config, connect to the database, and run migrations.

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `config/config.yaml`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "ducati-parts-finder"
version = "0.1.0"
description = "Find used Ducati parts across European marketplaces"
requires-python = ">=3.12"
dependencies = [
    "httpx>=0.27",
    "playwright>=1.42",
    "beautifulsoup4>=4.12",
    "jinja2>=3.1",
    "pyyaml>=6.0",
    "python-dotenv>=1.0",
    "pillow>=10.0",
]

[tool.pytest.ini_options]
testpaths = ["test_scripts"]
pythonpath = ["."]
```

- [ ] **Step 2: Create .gitignore**

```
.venv/
__pycache__/
*.pyc
.env
data/ducati_parts.db
reports/*.html
.pytest_cache/
```

- [ ] **Step 3: Create .env.example**

```
EBAY_APP_ID=
EBAY_CERT_ID=
```

- [ ] **Step 4: Create config/config.yaml**

Use the exact config from the spec (see spec section "Configuration > config.yaml").

- [ ] **Step 5: Initialize UV project and install dependencies**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && uv venv && uv sync`
Expected: Virtual environment created, all dependencies installed.

- [ ] **Step 6: Install Playwright browsers**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && playwright install chromium`
Expected: Chromium browser downloaded for Playwright.

- [ ] **Step 7: Create required directories**

Run:
```bash
mkdir -p src/adapters src/catalog src/core src/watch src/reports/templates src/db/migrations
mkdir -p data/seed reports config/launchd test_scripts .claude/skills/ducati-parts
touch src/__init__.py src/adapters/__init__.py src/catalog/__init__.py src/core/__init__.py
touch src/watch/__init__.py src/reports/__init__.py src/db/__init__.py
```

- [ ] **Step 8: Commit**

```bash
git init
git add pyproject.toml .gitignore .env.example config/config.yaml src/ data/seed/ test_scripts/ .claude/
git commit -m "chore: scaffold ducati-parts-finder project structure"
```

---

### Task 2: Configuration Loader

**Files:**
- Create: `src/core/config.py`
- Create: `test_scripts/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# test_scripts/test_config.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_config.py -v`
Expected: FAIL with "ModuleNotFoundError" or "ImportError"

- [ ] **Step 3: Write implementation**

```python
# src/core/config.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_config.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/config.py test_scripts/test_config.py
git commit -m "feat: add configuration loader with validation"
```

---

### Task 3: Core Data Types

**Files:**
- Create: `src/core/types.py`
- Create: `test_scripts/test_types.py`

- [ ] **Step 1: Write the failing test**

```python
# test_scripts/test_types.py
from decimal import Decimal
from datetime import datetime
from src.core.types import (
    Listing, RawListing, SearchFilters,
    ConditionScore, CompatibilityConfidence,
)


def test_listing_total_price_calculation():
    listing = Listing(
        id="ebay_123",
        source="ebay",
        title="Clutch lever Multistrada",
        description="Good condition",
        part_price=Decimal("25.00"),
        shipping_price=Decimal("10.00"),
        currency_original="EUR",
        seller_country="IT",
        is_eu=True,
        condition_raw="Good",
        condition_score=ConditionScore.GREEN,
        condition_notes="Clean part, good photos",
        photos=["https://example.com/photo1.jpg"],
        listing_url="https://ebay.it/item/123",
        compatible_models=["Multistrada 1260 Enduro", "Multistrada 1260"],
        compatibility_confidence=CompatibilityConfidence.DEFINITE,
        oem_part_number="63040601A",
        date_listed=datetime(2026, 4, 10),
        date_found=datetime(2026, 4, 14),
    )
    assert listing.total_price == Decimal("35.00")
    assert listing.shipping_ratio_flag is False


def test_listing_shipping_ratio_flag_triggered():
    listing = Listing(
        id="olx_456",
        source="olx_bg",
        title="Lever",
        description="OK",
        part_price=Decimal("10.00"),
        shipping_price=Decimal("15.00"),
        currency_original="BGN",
        seller_country="BG",
        is_eu=True,
        condition_raw="",
        condition_score=ConditionScore.YELLOW,
        condition_notes="No photos",
        photos=[],
        listing_url="https://olx.bg/item/456",
        compatible_models=["Multistrada 1260 Enduro"],
        compatibility_confidence=CompatibilityConfidence.VERIFY,
        oem_part_number="",
        date_listed=datetime(2026, 4, 12),
        date_found=datetime(2026, 4, 14),
    )
    assert listing.total_price == Decimal("25.00")
    assert listing.shipping_ratio_flag is True


def test_search_filters_defaults():
    filters = SearchFilters(query="clutch lever")
    assert filters.max_total_price is None
    assert filters.tiers == [1, 2]
    assert filters.target_models == []
    assert filters.sources == []


def test_raw_listing_creation():
    raw = RawListing(
        source_id="123",
        source="ebay",
        title="Test part",
        description="A part",
        price=25.50,
        currency="EUR",
        shipping_price=10.0,
        seller_country="IT",
        condition_label="Good",
        photos=["https://example.com/p1.jpg"],
        listing_url="https://ebay.it/123",
    )
    assert raw.source_id == "123"
    assert raw.price == 25.50
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_types.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write implementation**

```python
# src/core/types.py
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
    """Raw listing data as returned by a source adapter before enrichment."""
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
    """Enriched listing with condition scoring, compatibility, and pricing."""
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
    """Filters passed to source adapters and the search orchestrator."""
    query: str
    max_total_price: Decimal | None = None
    tiers: list[int] = field(default_factory=lambda: [1, 2])
    target_models: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    oem_number: str | None = None
    part_category: str | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_types.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/types.py test_scripts/test_types.py
git commit -m "feat: add core data types for listings, filters, and enums"
```

---

### Task 4: Database Layer

**Files:**
- Create: `src/db/database.py`
- Create: `test_scripts/test_database.py`

- [ ] **Step 1: Write the failing test**

```python
# test_scripts/test_database.py
import sqlite3
from pathlib import Path
from src.db.database import Database


def test_database_creates_tables(tmp_path):
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    db.initialize()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    assert "Listing" in tables
    assert "Watch" in tables
    assert "SeenListing" in tables
    assert "PartsCatalog" in tables


def test_database_insert_and_query_listing(tmp_path):
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    db.initialize()

    db.upsert_listing({
        "id": "ebay_123",
        "source": "ebay",
        "title": "Clutch lever",
        "description": "Good condition OEM",
        "part_price": 25.00,
        "shipping_price": 10.00,
        "total_price": 35.00,
        "shipping_ratio_flag": False,
        "currency_original": "EUR",
        "seller_country": "IT",
        "is_eu": True,
        "condition_raw": "Good",
        "condition_score": "green",
        "condition_notes": "Clean",
        "photos": '["https://example.com/p1.jpg"]',
        "listing_url": "https://ebay.it/123",
        "compatible_models": '["Multistrada 1260 Enduro"]',
        "compatibility_confidence": "definite",
        "oem_part_number": "63040601A",
        "date_listed": "2026-04-10T00:00:00",
        "date_found": "2026-04-14T00:00:00",
    })

    listings = db.get_listings_by_source("ebay")
    assert len(listings) == 1
    assert listings[0]["id"] == "ebay_123"
    assert listings[0]["part_price"] == 25.00


def test_database_upsert_updates_existing(tmp_path):
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    db.initialize()

    listing_data = {
        "id": "ebay_123",
        "source": "ebay",
        "title": "Clutch lever",
        "description": "Good condition",
        "part_price": 25.00,
        "shipping_price": 10.00,
        "total_price": 35.00,
        "shipping_ratio_flag": False,
        "currency_original": "EUR",
        "seller_country": "IT",
        "is_eu": True,
        "condition_raw": "Good",
        "condition_score": "green",
        "condition_notes": "Clean",
        "photos": "[]",
        "listing_url": "https://ebay.it/123",
        "compatible_models": "[]",
        "compatibility_confidence": "definite",
        "oem_part_number": "",
        "date_listed": "2026-04-10T00:00:00",
        "date_found": "2026-04-14T00:00:00",
    }
    db.upsert_listing(listing_data)

    listing_data["part_price"] = 20.00
    listing_data["total_price"] = 30.00
    db.upsert_listing(listing_data)

    listings = db.get_listings_by_source("ebay")
    assert len(listings) == 1
    assert listings[0]["part_price"] == 20.00


def test_watch_crud(tmp_path):
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    db.initialize()

    watch_id = db.create_watch({
        "query": "clutch lever",
        "part_category": "controls",
        "oem_number": "",
        "max_total_price": 40.00,
        "target_models": '["Multistrada 1260 Enduro", "Multistrada 1260"]',
        "sources": '["all"]',
        "active": True,
    })
    assert watch_id == 1

    watches = db.get_active_watches()
    assert len(watches) == 1
    assert watches[0]["query"] == "clutch lever"

    db.deactivate_watch(watch_id)
    watches = db.get_active_watches()
    assert len(watches) == 0


def test_seen_listing_tracking(tmp_path):
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    db.initialize()

    watch_id = db.create_watch({
        "query": "test",
        "part_category": "",
        "oem_number": "",
        "max_total_price": 100.00,
        "target_models": "[]",
        "sources": "[]",
        "active": True,
    })

    assert db.is_listing_seen("ebay_123", watch_id) is False

    db.mark_listing_seen("ebay_123", watch_id)
    assert db.is_listing_seen("ebay_123", watch_id) is True

    db.mark_listing_notified("ebay_123", watch_id)
    seen = db.get_seen_listing("ebay_123", watch_id)
    assert seen["notified"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_database.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write implementation**

```python
# src/db/database.py
import sqlite3
from datetime import datetime
from pathlib import Path


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def initialize(self) -> None:
        conn = self._connect()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS Listing (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                part_price REAL NOT NULL,
                shipping_price REAL NOT NULL,
                total_price REAL NOT NULL,
                shipping_ratio_flag INTEGER NOT NULL,
                currency_original TEXT NOT NULL,
                seller_country TEXT NOT NULL,
                is_eu INTEGER NOT NULL,
                condition_raw TEXT NOT NULL,
                condition_score TEXT NOT NULL,
                condition_notes TEXT NOT NULL,
                photos TEXT NOT NULL,
                listing_url TEXT NOT NULL,
                compatible_models TEXT NOT NULL,
                compatibility_confidence TEXT NOT NULL,
                oem_part_number TEXT NOT NULL,
                date_listed TEXT NOT NULL,
                date_found TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS Watch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                part_category TEXT NOT NULL DEFAULT '',
                oem_number TEXT NOT NULL DEFAULT '',
                max_total_price REAL NOT NULL,
                target_models TEXT NOT NULL DEFAULT '[]',
                sources TEXT NOT NULL DEFAULT '[]',
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                last_checked TEXT
            );

            CREATE TABLE IF NOT EXISTS SeenListing (
                listing_id TEXT NOT NULL,
                watch_id INTEGER NOT NULL,
                first_seen TEXT NOT NULL DEFAULT (datetime('now')),
                notified INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (listing_id, watch_id),
                FOREIGN KEY (watch_id) REFERENCES Watch(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS PartsCatalog (
                oem_number TEXT PRIMARY KEY,
                part_name TEXT NOT NULL,
                category TEXT NOT NULL,
                compatible_models TEXT NOT NULL DEFAULT '[]',
                enduro_specific INTEGER NOT NULL DEFAULT 0,
                search_aliases TEXT NOT NULL DEFAULT '[]'
            );
        """)
        conn.commit()
        conn.close()

    def upsert_listing(self, data: dict) -> None:
        conn = self._connect()
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        updates = ", ".join(f"{k}=excluded.{k}" for k in data if k != "id")
        conn.execute(
            f"INSERT INTO Listing ({columns}) VALUES ({placeholders}) "
            f"ON CONFLICT(id) DO UPDATE SET {updates}",
            list(data.values()),
        )
        conn.commit()
        conn.close()

    def get_listings_by_source(self, source: str) -> list[dict]:
        conn = self._connect()
        cursor = conn.execute(
            "SELECT * FROM Listing WHERE source = ?", (source,)
        )
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def create_watch(self, data: dict) -> int:
        conn = self._connect()
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        cursor = conn.execute(
            f"INSERT INTO Watch ({columns}) VALUES ({placeholders})",
            list(data.values()),
        )
        conn.commit()
        watch_id = cursor.lastrowid
        conn.close()
        return watch_id

    def get_active_watches(self) -> list[dict]:
        conn = self._connect()
        cursor = conn.execute("SELECT * FROM Watch WHERE active = 1")
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_all_watches(self) -> list[dict]:
        conn = self._connect()
        cursor = conn.execute("SELECT * FROM Watch ORDER BY created_at DESC")
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def deactivate_watch(self, watch_id: int) -> None:
        conn = self._connect()
        conn.execute("UPDATE Watch SET active = 0 WHERE id = ?", (watch_id,))
        conn.commit()
        conn.close()

    def activate_watch(self, watch_id: int) -> None:
        conn = self._connect()
        conn.execute("UPDATE Watch SET active = 1 WHERE id = ?", (watch_id,))
        conn.commit()
        conn.close()

    def delete_watch(self, watch_id: int) -> None:
        conn = self._connect()
        conn.execute("DELETE FROM Watch WHERE id = ?", (watch_id,))
        conn.commit()
        conn.close()

    def update_watch_last_checked(self, watch_id: int) -> None:
        conn = self._connect()
        conn.execute(
            "UPDATE Watch SET last_checked = ? WHERE id = ?",
            (datetime.now().isoformat(), watch_id),
        )
        conn.commit()
        conn.close()

    def is_listing_seen(self, listing_id: str, watch_id: int) -> bool:
        conn = self._connect()
        cursor = conn.execute(
            "SELECT 1 FROM SeenListing WHERE listing_id = ? AND watch_id = ?",
            (listing_id, watch_id),
        )
        result = cursor.fetchone() is not None
        conn.close()
        return result

    def mark_listing_seen(self, listing_id: str, watch_id: int) -> None:
        conn = self._connect()
        conn.execute(
            "INSERT OR IGNORE INTO SeenListing (listing_id, watch_id) VALUES (?, ?)",
            (listing_id, watch_id),
        )
        conn.commit()
        conn.close()

    def mark_listing_notified(self, listing_id: str, watch_id: int) -> None:
        conn = self._connect()
        conn.execute(
            "UPDATE SeenListing SET notified = 1 WHERE listing_id = ? AND watch_id = ?",
            (listing_id, watch_id),
        )
        conn.commit()
        conn.close()

    def get_seen_listing(self, listing_id: str, watch_id: int) -> dict | None:
        conn = self._connect()
        cursor = conn.execute(
            "SELECT * FROM SeenListing WHERE listing_id = ? AND watch_id = ?",
            (listing_id, watch_id),
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_database.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/db/database.py test_scripts/test_database.py
git commit -m "feat: add SQLite database layer with Listing, Watch, SeenListing, PartsCatalog tables"
```

---

## Phase 2: Core Search Infrastructure

Builds the shipping estimator, currency converter, condition filter, base adapter interface, and search orchestrator. After this phase you can run a search pipeline end-to-end with a mock adapter.

---

### Task 5: Shipping Estimator

**Files:**
- Create: `src/core/shipping.py`
- Create: `test_scripts/test_shipping.py`

- [ ] **Step 1: Write the failing test**

```python
# test_scripts/test_shipping.py
from decimal import Decimal
from src.core.shipping import ShippingEstimator

EU_COUNTRIES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE",
}


def test_estimate_shipping_bulgaria():
    estimator = ShippingEstimator(destination_postal="15562", destination_country="GR")
    low, high = estimator.estimate("BG")
    assert low == Decimal("5")
    assert high == Decimal("10")


def test_estimate_shipping_germany():
    estimator = ShippingEstimator(destination_postal="15562", destination_country="GR")
    low, high = estimator.estimate("DE")
    assert low == Decimal("10")
    assert high == Decimal("20")


def test_estimate_shipping_uk_includes_customs_warning():
    estimator = ShippingEstimator(destination_postal="15562", destination_country="GR")
    low, high = estimator.estimate("GB")
    assert low == Decimal("15")
    assert high == Decimal("30")


def test_is_eu():
    estimator = ShippingEstimator(destination_postal="15562", destination_country="GR")
    assert estimator.is_eu("BG") is True
    assert estimator.is_eu("IT") is True
    assert estimator.is_eu("GB") is False
    assert estimator.is_eu("US") is False


def test_midpoint_estimate():
    estimator = ShippingEstimator(destination_postal="15562", destination_country="GR")
    mid = estimator.midpoint("RO")
    assert mid == Decimal("9")  # (6 + 12) / 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_shipping.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write implementation**

```python
# src/core/shipping.py
from decimal import Decimal


EU_COUNTRIES = frozenset({
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE",
})

# Estimated shipping cost ranges to Athens 15562, in EUR
SHIPPING_RANGES: dict[str, tuple[int, int]] = {
    "BG": (5, 10),
    "RO": (6, 12),
    "HR": (8, 15),
    "SI": (10, 16),
    "HU": (10, 18),
    "IT": (8, 15),
    "PL": (12, 22),
    "CZ": (14, 22),
    "SK": (12, 20),
    "DE": (10, 20),
    "FR": (12, 22),
    "ES": (12, 25),
    "AT": (10, 18),
    "NL": (12, 20),
    "BE": (12, 20),
    "GB": (15, 30),
}

DEFAULT_RANGE = (15, 30)


class ShippingEstimator:
    def __init__(self, destination_postal: str, destination_country: str):
        self.destination_postal = destination_postal
        self.destination_country = destination_country

    def estimate(self, seller_country: str) -> tuple[Decimal, Decimal]:
        low, high = SHIPPING_RANGES.get(seller_country.upper(), DEFAULT_RANGE)
        return Decimal(str(low)), Decimal(str(high))

    def midpoint(self, seller_country: str) -> Decimal:
        low, high = self.estimate(seller_country)
        return (low + high) / 2

    def is_eu(self, country_code: str) -> bool:
        return country_code.upper() in EU_COUNTRIES
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_shipping.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/shipping.py test_scripts/test_shipping.py
git commit -m "feat: add shipping estimator with EU country detection and cost ranges"
```

---

### Task 6: Currency Converter

**Files:**
- Create: `src/core/currency.py`
- Create: `test_scripts/test_currency.py`

- [ ] **Step 1: Write the failing test**

```python
# test_scripts/test_currency.py
from decimal import Decimal
from unittest.mock import AsyncMock, patch
import asyncio
from src.core.currency import CurrencyConverter


def test_convert_eur_to_eur():
    converter = CurrencyConverter()
    converter._rates = {"EUR": Decimal("1")}
    result = converter.convert(Decimal("100"), "EUR")
    assert result == Decimal("100")


def test_convert_bgn_to_eur():
    converter = CurrencyConverter()
    # BGN is pegged at ~1.9558 per EUR
    converter._rates = {"BGN": Decimal("1.9558")}
    result = converter.convert(Decimal("19.558"), "BGN")
    assert result == Decimal("10.00")


def test_convert_pln_to_eur():
    converter = CurrencyConverter()
    converter._rates = {"PLN": Decimal("4.30")}
    result = converter.convert(Decimal("43.00"), "PLN")
    assert result == Decimal("10.00")


def test_convert_unknown_currency_raises():
    converter = CurrencyConverter()
    converter._rates = {}
    try:
        converter.convert(Decimal("100"), "XYZ")
        assert False, "Should have raised"
    except KeyError:
        pass


def test_supported_currencies():
    converter = CurrencyConverter()
    converter._rates = {
        "BGN": Decimal("1.96"),
        "RON": Decimal("4.97"),
        "HUF": Decimal("395"),
        "PLN": Decimal("4.30"),
        "CZK": Decimal("25.30"),
        "GBP": Decimal("0.86"),
    }
    assert converter.is_supported("BGN") is True
    assert converter.is_supported("EUR") is True
    assert converter.is_supported("XYZ") is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_currency.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write implementation**

```python
# src/core/currency.py
from decimal import Decimal, ROUND_HALF_UP
from xml.etree import ElementTree

import httpx


ECB_RATES_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
ECB_NS = {"gesmes": "http://www.gesmes.org/xml/2002-08-01", "eurofxref": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"}


class CurrencyConverter:
    def __init__(self):
        self._rates: dict[str, Decimal] = {}

    async def fetch_rates(self) -> None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(ECB_RATES_URL, timeout=10)
            resp.raise_for_status()

        root = ElementTree.fromstring(resp.text)
        cube = root.find(".//eurofxref:Cube/eurofxref:Cube", ECB_NS)
        if cube is None:
            raise RuntimeError("Failed to parse ECB rate data")

        self._rates = {}
        for rate_elem in cube.findall("eurofxref:Cube", ECB_NS):
            currency = rate_elem.attrib["currency"]
            rate = Decimal(rate_elem.attrib["rate"])
            self._rates[currency] = rate

    def convert(self, amount: Decimal, from_currency: str) -> Decimal:
        from_currency = from_currency.upper()
        if from_currency == "EUR":
            return amount

        if from_currency not in self._rates:
            raise KeyError(f"Unsupported currency: {from_currency}")

        rate = self._rates[from_currency]
        eur_amount = amount / rate
        return eur_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def is_supported(self, currency: str) -> bool:
        return currency.upper() == "EUR" or currency.upper() in self._rates
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_currency.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/currency.py test_scripts/test_currency.py
git commit -m "feat: add currency converter with ECB rate fetching"
```

---

### Task 7: Condition Filter (Stages 1 & 2)

**Files:**
- Create: `src/core/condition.py`
- Create: `test_scripts/test_condition.py`

- [ ] **Step 1: Write the failing test**

```python
# test_scripts/test_condition.py
from src.core.condition import ConditionFilter, NormalizedCondition


def test_exclude_broken_english():
    cf = ConditionFilter()
    assert cf.should_exclude("Broken clutch lever for parts", "") is True


def test_exclude_rotto_italian():
    cf = ConditionFilter()
    assert cf.should_exclude("Leva frizione", "Rotto, venduto per ricambi") is True


def test_exclude_kaputt_german():
    cf = ConditionFilter()
    assert cf.should_exclude("Kupplungshebel kaputt", "") is True


def test_exclude_for_parts_romanian():
    cf = ConditionFilter()
    assert cf.should_exclude("Maneta", "pentru piese de schimb") is True


def test_exclude_rusty_bulgarian():
    cf = ConditionFilter()
    assert cf.should_exclude("Лост съединител ръждясал", "") is True


def test_allow_good_condition():
    cf = ConditionFilter()
    assert cf.should_exclude("Clutch lever Multistrada 1260", "Good condition, barely used") is False


def test_allow_normal_description():
    cf = ConditionFilter()
    assert cf.should_exclude("Leva frizione Ducati", "Ottimo stato, come nuova") is False


def test_normalize_like_new():
    cf = ConditionFilter()
    assert cf.normalize_label("Like new") == NormalizedCondition.EXCELLENT
    assert cf.normalize_label("Come nuovo") == NormalizedCondition.EXCELLENT
    assert cf.normalize_label("Wie neu") == NormalizedCondition.EXCELLENT


def test_normalize_good():
    cf = ConditionFilter()
    assert cf.normalize_label("Good") == NormalizedCondition.GOOD
    assert cf.normalize_label("Buono") == NormalizedCondition.GOOD
    assert cf.normalize_label("Gut") == NormalizedCondition.GOOD


def test_normalize_unknown():
    cf = ConditionFilter()
    assert cf.normalize_label("") == NormalizedCondition.UNKNOWN
    assert cf.normalize_label("some random text") == NormalizedCondition.UNKNOWN


def test_normalize_for_parts_feeds_to_exclusion():
    cf = ConditionFilter()
    assert cf.normalize_label("For parts or not working") == NormalizedCondition.EXCLUDED
    assert cf.normalize_label("Per ricambi") == NormalizedCondition.EXCLUDED
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_condition.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write implementation**

```python
# src/core/condition.py
import re
from enum import Enum


class NormalizedCondition(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    UNKNOWN = "unknown"
    EXCLUDED = "excluded"


# Negative keywords that indicate broken/damaged parts across languages
EXCLUSION_KEYWORDS: list[str] = [
    # English
    r"\bbroken\b", r"\bcracked\b", r"\bfor parts\b", r"\bdamaged\b",
    r"\bbent\b", r"\brush?ted?\b", r"\bscrap\b", r"\bdefective\b",
    # Italian
    r"\brotto\b", r"\bcrepato\b", r"\bper ricambi\b", r"\bdanneggiato\b",
    r"\bpiegato\b", r"\barrugginito\b", r"\brottame\b",
    # German
    r"\bkaputt\b", r"\bgerissen\b", r"\bfür teile\b", r"\bbeschädigt\b",
    r"\bverbogen\b", r"\bverrostet\b", r"\bschrott\b", r"\bdefekt\b",
    # French
    r"\bcassé\b", r"\bfissuré\b", r"\bpour pièces\b", r"\bendommagé\b",
    r"\btordu\b", r"\brouillé\b", r"\bferraille\b",
    # Romanian
    r"\bstricat\b", r"\bcrăpat\b", r"\bpentru piese\b", r"\bdeteriora\b",
    r"\bîndoit\b", r"\bruginit\b",
    # Bulgarian
    r"счупен", r"напукан", r"за части", r"повреден", r"огънат", r"ръждясал", r"скрап",
    # Polish
    r"\bzłamany\b", r"\bpęknięty\b", r"\bna części\b", r"\buszkodzony\b",
    r"\bzgięty\b", r"\bzardzewiały\b", r"\bzłom\b",
    # Hungarian
    r"\btörött\b", r"\brepedt\b", r"\balkatrésznek\b", r"\bsérült\b",
    r"\bgörbült\b", r"\brozsdás\b",
    # Czech
    r"\bzlomený\b", r"\bprasklý\b", r"\bna díly\b", r"\bpoškozený\b",
    r"\bohnutý\b", r"\bzrezivělý\b",
    # Croatian
    r"\bslomljen\b", r"\bnapuknut\b", r"\bza dijelove\b", r"\boštećen\b",
    r"\bsavijen\b", r"\bzahrđao\b",
]

_EXCLUSION_PATTERN = re.compile("|".join(EXCLUSION_KEYWORDS), re.IGNORECASE)

# Condition label mappings
_EXCELLENT_LABELS = [
    "like new", "come nuovo", "wie neu", "comme neuf", "como nuevo",
    "mint", "as new", "nuovo", "neuwertig", "neuf", "nuevo",
    "ca nou", "като нов", "jak nowy", "jako novy",
]

_GOOD_LABELS = [
    "good", "buono", "gut", "bon", "bueno", "buen",
    "bun", "добър", "dobry", "dobar", "dobra",
]

_FAIR_LABELS = [
    "acceptable", "accettabile", "akzeptabel", "acceptable", "aceptable",
    "fair", "satisfactory", "usato", "gebraucht", "usado",
]

_EXCLUDED_LABELS = [
    "for parts", "per ricambi", "für teile", "pour pièces", "para piezas",
    "not working", "non funzionante", "defekt",
    "for parts or not working", "per ricambi o non funzionante",
]


class ConditionFilter:
    def should_exclude(self, title: str, description: str) -> bool:
        text = f"{title} {description}"
        return bool(_EXCLUSION_PATTERN.search(text))

    def normalize_label(self, label: str) -> NormalizedCondition:
        if not label.strip():
            return NormalizedCondition.UNKNOWN

        lower = label.lower().strip()

        for excluded in _EXCLUDED_LABELS:
            if excluded in lower:
                return NormalizedCondition.EXCLUDED

        for excellent in _EXCELLENT_LABELS:
            if excellent in lower:
                return NormalizedCondition.EXCELLENT

        for good in _GOOD_LABELS:
            if good in lower:
                return NormalizedCondition.GOOD

        for fair in _FAIR_LABELS:
            if fair in lower:
                return NormalizedCondition.FAIR

        return NormalizedCondition.UNKNOWN
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_condition.py -v`
Expected: All 12 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/condition.py test_scripts/test_condition.py
git commit -m "feat: add condition filter with multi-language keyword exclusion and label normalization"
```

---

### Task 8: Base Adapter Interface

**Files:**
- Create: `src/adapters/base.py`
- Create: `test_scripts/test_adapter_base.py`

- [ ] **Step 1: Write the failing test**

```python
# test_scripts/test_adapter_base.py
import pytest
from src.adapters.base import BaseAdapter, AdapterHealthCheck
from src.core.types import RawListing, SearchFilters


class FakeAdapter(BaseAdapter):
    source_name = "fake"
    language = "en"
    country = "GB"
    currency = "GBP"

    async def search(self, query: str, filters: SearchFilters) -> list[RawListing]:
        return [
            RawListing(
                source_id="1",
                source=self.source_name,
                title=f"Fake result for {query}",
                description="A fake listing",
                price=10.0,
                currency=self.currency,
                shipping_price=5.0,
                seller_country=self.country,
                condition_label="Good",
                photos=[],
                listing_url="https://fake.com/1",
            )
        ]

    async def health_check(self) -> AdapterHealthCheck:
        return AdapterHealthCheck(healthy=True, message="OK")


class BrokenAdapter(BaseAdapter):
    source_name = "broken"
    language = "en"
    country = "US"
    currency = "USD"

    async def search(self, query: str, filters: SearchFilters) -> list[RawListing]:
        raise ConnectionError("Site is down")

    async def health_check(self) -> AdapterHealthCheck:
        return AdapterHealthCheck(healthy=False, message="Site unreachable")


def test_fake_adapter_search():
    import asyncio
    adapter = FakeAdapter()
    results = asyncio.run(adapter.search("clutch lever", SearchFilters(query="clutch lever")))
    assert len(results) == 1
    assert results[0].source == "fake"
    assert "clutch lever" in results[0].title


def test_adapter_properties():
    adapter = FakeAdapter()
    assert adapter.source_name == "fake"
    assert adapter.language == "en"
    assert adapter.country == "GB"


def test_adapter_health_check():
    import asyncio
    adapter = FakeAdapter()
    health = asyncio.run(adapter.health_check())
    assert health.healthy is True

    broken = BrokenAdapter()
    health = asyncio.run(broken.health_check())
    assert health.healthy is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_adapter_base.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write implementation**

```python
# src/adapters/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.core.types import RawListing, SearchFilters


@dataclass
class AdapterHealthCheck:
    healthy: bool
    message: str


class BaseAdapter(ABC):
    source_name: str
    language: str
    country: str
    currency: str

    @abstractmethod
    async def search(self, query: str, filters: SearchFilters) -> list[RawListing]:
        ...

    @abstractmethod
    async def health_check(self) -> AdapterHealthCheck:
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_adapter_base.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/base.py test_scripts/test_adapter_base.py
git commit -m "feat: add base adapter interface with health check"
```

---

### Task 9: Search Orchestrator

**Files:**
- Create: `src/core/search.py`
- Create: `src/core/dedup.py`
- Create: `test_scripts/test_search.py`

- [ ] **Step 1: Write the failing test**

```python
# test_scripts/test_search.py
import asyncio
from decimal import Decimal
from src.core.search import SearchOrchestrator
from src.core.types import RawListing, SearchFilters
from src.core.config import AppConfig, BikeConfig, ShippingConfig, SearchConfig, ConditionConfig, WatchConfig
from src.adapters.base import BaseAdapter, AdapterHealthCheck


class MockAdapter(BaseAdapter):
    source_name = "mock"
    language = "en"
    country = "BG"
    currency = "EUR"

    def __init__(self, results: list[RawListing]):
        self._results = results

    async def search(self, query: str, filters: SearchFilters) -> list[RawListing]:
        return self._results

    async def health_check(self) -> AdapterHealthCheck:
        return AdapterHealthCheck(healthy=True, message="OK")


class FailingAdapter(BaseAdapter):
    source_name = "failing"
    language = "en"
    country = "US"
    currency = "USD"

    async def search(self, query: str, filters: SearchFilters) -> list[RawListing]:
        raise ConnectionError("down")

    async def health_check(self) -> AdapterHealthCheck:
        return AdapterHealthCheck(healthy=False, message="down")


def _make_config() -> AppConfig:
    return AppConfig(
        bike=BikeConfig(
            default_model="Multistrada 1260 Enduro",
            year_range=[2019, 2021],
            also_compatible=["Multistrada 1260"],
        ),
        shipping=ShippingConfig(
            destination_country="GR",
            destination_postal="15562",
            destination_city="Athens",
            shipping_ratio_warning=0.5,
        ),
        search=SearchConfig(default_tiers=[1, 2], max_results_per_source=50, currency_display="EUR"),
        condition=ConditionConfig(min_score="red", photo_required=False),
        watch=WatchConfig(check_interval_hours=4, stale_listing_days=30, notification="macos"),
        tiers={1: ["mock"], 2: [], 3: []},
    )


def test_orchestrator_collects_results_from_adapters():
    raw = RawListing(
        source_id="1", source="mock", title="Clutch lever Multistrada",
        description="Good condition", price=20.0, currency="EUR",
        shipping_price=8.0, seller_country="BG", condition_label="Good",
        photos=["https://example.com/p.jpg"], listing_url="https://mock.com/1",
    )
    adapter = MockAdapter([raw])
    config = _make_config()
    orchestrator = SearchOrchestrator(config=config, adapters={"mock": adapter})

    filters = SearchFilters(query="clutch lever", tiers=[1])
    listings = asyncio.run(orchestrator.run(filters))

    assert len(listings) == 1
    assert listings[0].id == "mock_1"
    assert listings[0].part_price == Decimal("20.00")
    assert listings[0].seller_country == "BG"
    assert listings[0].is_eu is True


def test_orchestrator_excludes_bad_condition():
    raw = RawListing(
        source_id="2", source="mock", title="Broken lever for parts",
        description="Cracked, not usable", price=5.0, currency="EUR",
        shipping_price=3.0, seller_country="BG", condition_label="For parts",
        photos=[], listing_url="https://mock.com/2",
    )
    adapter = MockAdapter([raw])
    config = _make_config()
    orchestrator = SearchOrchestrator(config=config, adapters={"mock": adapter})

    filters = SearchFilters(query="lever", tiers=[1])
    listings = asyncio.run(orchestrator.run(filters))

    assert len(listings) == 0


def test_orchestrator_filters_by_max_total_price():
    raw1 = RawListing(
        source_id="1", source="mock", title="Cheap lever",
        description="OK", price=10.0, currency="EUR",
        shipping_price=5.0, seller_country="BG", condition_label="Good",
        photos=[], listing_url="https://mock.com/1",
    )
    raw2 = RawListing(
        source_id="2", source="mock", title="Expensive lever",
        description="OK", price=100.0, currency="EUR",
        shipping_price=20.0, seller_country="BG", condition_label="Good",
        photos=[], listing_url="https://mock.com/2",
    )
    adapter = MockAdapter([raw1, raw2])
    config = _make_config()
    orchestrator = SearchOrchestrator(config=config, adapters={"mock": adapter})

    filters = SearchFilters(query="lever", tiers=[1], max_total_price=Decimal("50"))
    listings = asyncio.run(orchestrator.run(filters))

    assert len(listings) == 1
    assert listings[0].total_price == Decimal("15.00")


def test_orchestrator_handles_adapter_failure():
    adapter = FailingAdapter()
    config = _make_config()
    config.tiers[1] = ["failing"]
    orchestrator = SearchOrchestrator(config=config, adapters={"failing": adapter})

    filters = SearchFilters(query="lever", tiers=[1])
    listings = asyncio.run(orchestrator.run(filters))

    assert len(listings) == 0
    assert "failing" in orchestrator.last_errors


def test_dedup_removes_duplicate_listings():
    raw = RawListing(
        source_id="1", source="mock", title="Lever",
        description="Good", price=20.0, currency="EUR",
        shipping_price=8.0, seller_country="BG", condition_label="Good",
        photos=[], listing_url="https://mock.com/1",
    )
    adapter = MockAdapter([raw, raw])
    config = _make_config()
    orchestrator = SearchOrchestrator(config=config, adapters={"mock": adapter})

    filters = SearchFilters(query="lever", tiers=[1])
    listings = asyncio.run(orchestrator.run(filters))

    assert len(listings) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_search.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write dedup module**

```python
# src/core/dedup.py
from src.core.types import Listing


def deduplicate(listings: list[Listing]) -> list[Listing]:
    seen_ids: set[str] = set()
    unique: list[Listing] = []
    for listing in listings:
        if listing.id not in seen_ids:
            seen_ids.add(listing.id)
            unique.append(listing)
    return unique
```

- [ ] **Step 4: Write search orchestrator**

```python
# src/core/search.py
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

        # Resolve which adapters to run based on tiers
        adapter_names: list[str] = []
        for tier in filters.tiers:
            adapter_names.extend(self.config.tiers.get(tier, []))

        # If specific sources requested, override tiers
        if filters.sources:
            adapter_names = filters.sources

        # Run adapters concurrently
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

        # Convert raw listings to enriched listings
        listings: list[Listing] = []
        for raw in raw_results:
            # Stage 1+2: Condition exclusion
            if self.condition_filter.should_exclude(raw.title, raw.description):
                continue
            normalized = self.condition_filter.normalize_label(raw.condition_label)
            if normalized.value == "excluded":
                continue

            # Shipping estimation
            if raw.shipping_price is not None:
                shipping = Decimal(str(raw.shipping_price)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            else:
                shipping = self.shipping_estimator.midpoint(raw.seller_country)

            part_price = Decimal(str(raw.price)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            # Determine condition score (placeholder -- AI scoring in Phase 5)
            if raw.photos:
                condition_score = ConditionScore.GREEN if normalized.value in ("excellent", "good") else ConditionScore.YELLOW
            else:
                condition_score = ConditionScore.YELLOW

            if normalized.value == "fair":
                condition_score = ConditionScore.RED

            listing = Listing(
                id=f"{raw.source}_{raw.source_id}",
                source=raw.source,
                title=raw.title,
                description=raw.description,
                part_price=part_price,
                shipping_price=shipping,
                currency_original=raw.currency,
                seller_country=raw.seller_country,
                is_eu=self.shipping_estimator.is_eu(raw.seller_country),
                condition_raw=raw.condition_label,
                condition_score=condition_score,
                condition_notes=f"Normalized: {normalized.value}",
                photos=raw.photos,
                listing_url=raw.listing_url,
                compatible_models=[],
                compatibility_confidence=CompatibilityConfidence.VERIFY,
                oem_part_number="",
                date_listed=datetime.now(),
                date_found=datetime.now(),
            )

            # Total price filter
            if filters.max_total_price and listing.total_price > filters.max_total_price:
                continue

            listings.append(listing)

        # Deduplicate and sort by total price
        listings = deduplicate(listings)
        listings.sort(key=lambda l: (l.condition_score.value, l.total_price))

        return listings
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_search.py -v`
Expected: All 5 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/core/search.py src/core/dedup.py test_scripts/test_search.py
git commit -m "feat: add search orchestrator with tier-based adapter dispatch, condition filtering, and dedup"
```

---

## Phase 3: Report Generation

Builds the terminal summary and HTML report. After this phase you can display results in the terminal and generate rich HTML reports.

---

### Task 10: Terminal Report

**Files:**
- Create: `src/reports/terminal_report.py`
- Create: `test_scripts/test_terminal_report.py`

- [ ] **Step 1: Write the failing test**

```python
# test_scripts/test_terminal_report.py
from decimal import Decimal
from datetime import datetime
from src.reports.terminal_report import format_terminal_report
from src.core.types import Listing, ConditionScore, CompatibilityConfidence


def _make_listing(id: str, price: float, shipping: float, source: str, score: ConditionScore) -> Listing:
    return Listing(
        id=id, source=source, title=f"Part from {source}",
        description="Good", part_price=Decimal(str(price)),
        shipping_price=Decimal(str(shipping)), currency_original="EUR",
        seller_country="BG", is_eu=True, condition_raw="Good",
        condition_score=score, condition_notes="OK", photos=[],
        listing_url=f"https://{source}.com/{id}",
        compatible_models=["Multistrada 1260 Enduro"],
        compatibility_confidence=CompatibilityConfidence.DEFINITE,
        oem_part_number="", date_listed=datetime.now(), date_found=datetime.now(),
    )


def test_format_terminal_report_with_results():
    listings = [
        _make_listing("1", 10, 5, "olx_bg", ConditionScore.GREEN),
        _make_listing("2", 20, 8, "subito", ConditionScore.YELLOW),
        _make_listing("3", 30, 10, "ebay", ConditionScore.RED),
    ]
    output = format_terminal_report(listings, query="clutch lever", report_path="/tmp/report.html")
    assert "clutch lever" in output
    assert "3 listings" in output.lower() or "3" in output
    assert "15.00" in output  # best total price
    assert "/tmp/report.html" in output


def test_format_terminal_report_empty():
    output = format_terminal_report([], query="exhaust", report_path="/tmp/r.html")
    assert "no listings" in output.lower() or "0" in output


def test_format_terminal_report_shows_top_3():
    listings = [
        _make_listing(str(i), 10 + i, 5, "olx_bg", ConditionScore.GREEN)
        for i in range(10)
    ]
    output = format_terminal_report(listings, query="lever", report_path="/tmp/r.html")
    # Should mention at least 3 results in the summary
    lines = output.strip().split("\n")
    assert len(lines) >= 5  # header + 3 results + report path
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_terminal_report.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write implementation**

```python
# src/reports/terminal_report.py
from src.core.types import Listing, ConditionScore

SCORE_ICONS = {
    ConditionScore.GREEN: "G",
    ConditionScore.YELLOW: "Y",
    ConditionScore.RED: "R",
}


def format_terminal_report(listings: list[Listing], query: str, report_path: str) -> str:
    lines: list[str] = []

    if not listings:
        lines.append(f'Search: "{query}" -- No listings found.')
        lines.append(f"Report: {report_path}")
        return "\n".join(lines)

    green_count = sum(1 for l in listings if l.condition_score == ConditionScore.GREEN)
    yellow_count = sum(1 for l in listings if l.condition_score == ConditionScore.YELLOW)
    red_count = sum(1 for l in listings if l.condition_score == ConditionScore.RED)

    lines.append(f'Search: "{query}" -- {len(listings)} listings found')
    lines.append(f"  Condition: {green_count} green | {yellow_count} yellow | {red_count} red")
    lines.append("")

    # Top 3 by total price
    top = sorted(listings, key=lambda l: l.total_price)[:3]
    lines.append("Top 3 by price:")
    for i, listing in enumerate(top, 1):
        icon = SCORE_ICONS[listing.condition_score]
        eu_tag = "EU" if listing.is_eu else "non-EU"
        flag = " [!ship]" if listing.shipping_ratio_flag else ""
        lines.append(
            f"  {i}. [{icon}] {listing.total_price:.2f} EUR total | "
            f"{listing.source} | {listing.seller_country} ({eu_tag}){flag}"
        )
        lines.append(f"     {listing.title[:70]}")
        lines.append(f"     Part: {listing.part_price:.2f} | Ship: {listing.shipping_price:.2f} | {listing.listing_url}")

    lines.append("")
    lines.append(f"Full report: {report_path}")

    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_terminal_report.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/reports/terminal_report.py test_scripts/test_terminal_report.py
git commit -m "feat: add terminal report formatter with top-3 summary"
```

---

### Task 11: HTML Report Generator

**Files:**
- Create: `src/reports/templates/report.html`
- Create: `src/reports/html_report.py`
- Create: `test_scripts/test_html_report.py`

- [ ] **Step 1: Write the failing test**

```python
# test_scripts/test_html_report.py
import os
from decimal import Decimal
from datetime import datetime
from src.reports.html_report import generate_html_report
from src.core.types import Listing, ConditionScore, CompatibilityConfidence


def _make_listing(id: str, price: float, shipping: float, source: str, score: ConditionScore) -> Listing:
    return Listing(
        id=id, source=source, title=f"Clutch lever from {source}",
        description="Good condition, OEM part",
        part_price=Decimal(str(price)), shipping_price=Decimal(str(shipping)),
        currency_original="EUR", seller_country="BG", is_eu=True,
        condition_raw="Good", condition_score=score,
        condition_notes="Looks clean in photos",
        photos=["https://example.com/photo1.jpg"],
        listing_url=f"https://{source}.com/{id}",
        compatible_models=["Multistrada 1260 Enduro", "Multistrada 1260"],
        compatibility_confidence=CompatibilityConfidence.DEFINITE,
        oem_part_number="63040601A",
        date_listed=datetime(2026, 4, 10),
        date_found=datetime(2026, 4, 14),
    )


def test_generate_html_report_creates_file(tmp_path):
    listings = [
        _make_listing("1", 10, 5, "olx_bg", ConditionScore.GREEN),
        _make_listing("2", 20, 8, "subito", ConditionScore.YELLOW),
    ]
    report_path = str(tmp_path / "report.html")
    generate_html_report(listings, query="clutch lever", output_path=report_path)
    assert os.path.exists(report_path)

    with open(report_path) as f:
        html = f.read()

    assert "clutch lever" in html.lower()
    assert "olx_bg" in html
    assert "15.00" in html  # total price
    assert "63040601A" in html  # OEM number
    assert "Multistrada 1260 Enduro" in html
    assert "photo1.jpg" in html


def test_generate_html_report_empty(tmp_path):
    report_path = str(tmp_path / "empty.html")
    generate_html_report([], query="exhaust", output_path=report_path)
    assert os.path.exists(report_path)

    with open(report_path) as f:
        html = f.read()

    assert "no listings" in html.lower() or "0 listings" in html.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_html_report.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Create HTML template**

```html
<!-- src/reports/templates/report.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Ducati Parts: {{ query }}</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #e0e0e0; padding: 20px; }
        h1 { color: #ff4444; margin-bottom: 10px; }
        .summary { background: #16213e; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .summary span { margin-right: 20px; }
        .green { color: #4caf50; } .yellow { color: #ff9800; } .red { color: #f44336; }
        .filters { margin-bottom: 20px; display: flex; gap: 10px; flex-wrap: wrap; }
        .filters select, .filters input { background: #16213e; color: #e0e0e0; border: 1px solid #333; padding: 8px; border-radius: 4px; }
        .listing { background: #16213e; border-radius: 8px; padding: 15px; margin-bottom: 15px; display: flex; gap: 15px; border-left: 4px solid #333; }
        .listing.score-green { border-left-color: #4caf50; }
        .listing.score-yellow { border-left-color: #ff9800; }
        .listing.score-red { border-left-color: #f44336; }
        .listing-photo { width: 150px; height: 120px; object-fit: cover; border-radius: 4px; background: #0f3460; }
        .listing-info { flex: 1; }
        .listing-title { font-size: 16px; font-weight: bold; margin-bottom: 5px; }
        .listing-title a { color: #64b5f6; text-decoration: none; }
        .listing-title a:hover { text-decoration: underline; }
        .listing-meta { font-size: 13px; color: #999; margin-bottom: 8px; }
        .listing-price { font-size: 18px; font-weight: bold; color: #fff; }
        .listing-price .breakdown { font-size: 12px; color: #999; font-weight: normal; }
        .ship-warning { color: #ff9800; font-size: 12px; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
        .badge-green { background: #1b5e20; color: #4caf50; }
        .badge-yellow { background: #4e3800; color: #ff9800; }
        .badge-red { background: #4a0000; color: #f44336; }
        .badge-eu { background: #0d47a1; color: #64b5f6; }
        .badge-non-eu { background: #4a0000; color: #f44336; }
        .compat { font-size: 12px; color: #999; margin-top: 5px; }
        .condition-notes { font-size: 12px; color: #aaa; margin-top: 5px; font-style: italic; }
        .no-photo { width: 150px; height: 120px; background: #0f3460; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: #666; font-size: 12px; }
        .empty { text-align: center; padding: 60px 20px; color: #666; }
    </style>
</head>
<body>
    <h1>Ducati Parts: "{{ query }}"</h1>
    <div class="summary">
        <span>{{ listings | length }} listings</span>
        <span class="green">{{ green_count }} green</span>
        <span class="yellow">{{ yellow_count }} yellow</span>
        <span class="red">{{ red_count }} red</span>
        <span>Generated: {{ generated_at }}</span>
    </div>

    {% if listings %}
    <div class="filters">
        <select id="filterCondition" onchange="filterListings()">
            <option value="all">All conditions</option>
            <option value="green">Green only</option>
            <option value="yellow">Yellow only</option>
            <option value="red">Red only</option>
        </select>
        <select id="filterCountry" onchange="filterListings()">
            <option value="all">All countries</option>
            {% for country in countries %}
            <option value="{{ country }}">{{ country }}</option>
            {% endfor %}
        </select>
        <input type="number" id="filterMaxPrice" placeholder="Max total EUR" onchange="filterListings()">
    </div>

    <div id="listings">
    {% for listing in listings %}
        <div class="listing score-{{ listing.condition_score.value }}"
             data-score="{{ listing.condition_score.value }}"
             data-country="{{ listing.seller_country }}"
             data-total="{{ listing.total_price }}">
            {% if listing.photos %}
            <img class="listing-photo" src="{{ listing.photos[0] }}" alt="Part photo" loading="lazy"
                 onerror="this.outerHTML='<div class=no-photo>Photo unavailable</div>'">
            {% else %}
            <div class="no-photo">No photo</div>
            {% endif %}
            <div class="listing-info">
                <div class="listing-title">
                    <a href="{{ listing.listing_url }}" target="_blank">{{ listing.title }}</a>
                </div>
                <div class="listing-meta">
                    {{ listing.source }} | {{ listing.seller_country }}
                    <span class="badge badge-{{ 'eu' if listing.is_eu else 'non-eu' }}">
                        {{ 'EU' if listing.is_eu else 'non-EU + customs' }}
                    </span>
                    <span class="badge badge-{{ listing.condition_score.value }}">
                        {{ listing.condition_score.value | upper }}
                    </span>
                    {% if listing.oem_part_number %}
                    | OEM: {{ listing.oem_part_number }}
                    {% endif %}
                </div>
                <div class="listing-price">
                    {{ "%.2f" | format(listing.total_price) }} EUR
                    <span class="breakdown">
                        (Part: {{ "%.2f" | format(listing.part_price) }} + Ship: {{ "%.2f" | format(listing.shipping_price) }})
                    </span>
                    {% if listing.shipping_ratio_flag %}
                    <span class="ship-warning">Shipping > 50% of part price</span>
                    {% endif %}
                </div>
                <div class="compat">
                    Fits: {{ listing.compatible_models | join(", ") }}
                    ({{ listing.compatibility_confidence.value }})
                </div>
                <div class="condition-notes">{{ listing.condition_notes }}</div>
            </div>
        </div>
    {% endfor %}
    </div>
    {% else %}
    <div class="empty">
        <h2>0 listings found for "{{ query }}"</h2>
        <p>Try broadening your search or checking different tiers.</p>
    </div>
    {% endif %}

    <script>
    function filterListings() {
        const score = document.getElementById('filterCondition').value;
        const country = document.getElementById('filterCountry').value;
        const maxPrice = parseFloat(document.getElementById('filterMaxPrice').value) || Infinity;
        document.querySelectorAll('.listing').forEach(el => {
            const matchScore = score === 'all' || el.dataset.score === score;
            const matchCountry = country === 'all' || el.dataset.country === country;
            const matchPrice = parseFloat(el.dataset.total) <= maxPrice;
            el.style.display = matchScore && matchCountry && matchPrice ? 'flex' : 'none';
        });
    }
    </script>
</body>
</html>
```

- [ ] **Step 4: Write HTML report generator**

```python
# src/reports/html_report.py
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.core.types import Listing, ConditionScore


TEMPLATE_DIR = Path(__file__).parent / "templates"


def generate_html_report(listings: list[Listing], query: str, output_path: str) -> None:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)
    template = env.get_template("report.html")

    green_count = sum(1 for l in listings if l.condition_score == ConditionScore.GREEN)
    yellow_count = sum(1 for l in listings if l.condition_score == ConditionScore.YELLOW)
    red_count = sum(1 for l in listings if l.condition_score == ConditionScore.RED)
    countries = sorted(set(l.seller_country for l in listings))

    html = template.render(
        query=query,
        listings=listings,
        green_count=green_count,
        yellow_count=yellow_count,
        red_count=red_count,
        countries=countries,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_html_report.py -v`
Expected: All 2 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/reports/html_report.py src/reports/terminal_report.py src/reports/templates/report.html test_scripts/test_html_report.py
git commit -m "feat: add HTML report generator with filtering, condition color coding, and photo thumbnails"
```

---

## Phase 4: eBay Adapter (First Real Source)

Implements the eBay Browse API adapter -- the first real marketplace integration. After this phase you can search eBay for used Ducati parts end-to-end.

---

### Task 12: eBay API Adapter

**Files:**
- Create: `src/adapters/ebay.py`
- Create: `test_scripts/test_ebay_adapter.py`

- [ ] **Step 1: Write the failing test**

```python
# test_scripts/test_ebay_adapter.py
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from src.adapters.ebay import EbayAdapter
from src.core.types import SearchFilters


MOCK_TOKEN_RESPONSE = {
    "access_token": "test_token_123",
    "expires_in": 7200,
    "token_type": "Application Access Token",
}

MOCK_SEARCH_RESPONSE = {
    "itemSummaries": [
        {
            "itemId": "v1|123456|0",
            "title": "Ducati Multistrada 1260 Clutch Lever OEM",
            "price": {"value": "25.00", "currency": "EUR"},
            "condition": "Used",
            "seller": {"username": "moto_parts_it"},
            "itemLocation": {"country": "IT"},
            "shippingOptions": [
                {"shippingCost": {"value": "12.00", "currency": "EUR"}}
            ],
            "image": {"imageUrl": "https://i.ebayimg.com/images/g/test/s-l1600.jpg"},
            "itemWebUrl": "https://www.ebay.it/itm/123456",
            "shortDescription": "OEM clutch lever for Ducati Multistrada 1260. Good condition.",
        },
        {
            "itemId": "v1|789012|0",
            "title": "Broken Ducati lever for parts",
            "price": {"value": "5.00", "currency": "EUR"},
            "condition": "For parts or not working",
            "seller": {"username": "seller2"},
            "itemLocation": {"country": "DE"},
            "shippingOptions": [],
            "image": {"imageUrl": "https://i.ebayimg.com/images/g/test2/s-l1600.jpg"},
            "itemWebUrl": "https://www.ebay.de/itm/789012",
            "shortDescription": "Broken, sold as is.",
        },
    ],
    "total": 2,
}


def _make_mock_response(json_data, status_code=200):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.raise_for_status = MagicMock()
    return mock


def test_ebay_adapter_parses_search_results():
    adapter = EbayAdapter(app_id="test_id", cert_id="test_cert")

    with patch.object(adapter, '_get_token', new_callable=AsyncMock, return_value="test_token"):
        with patch.object(adapter, '_api_search', new_callable=AsyncMock, return_value=MOCK_SEARCH_RESPONSE):
            filters = SearchFilters(query="clutch lever multistrada 1260")
            results = asyncio.run(adapter.search("clutch lever multistrada 1260", filters))

    assert len(results) == 2
    assert results[0].source_id == "v1|123456|0"
    assert results[0].source == "ebay"
    assert results[0].price == 25.00
    assert results[0].shipping_price == 12.00
    assert results[0].seller_country == "IT"
    assert results[0].condition_label == "Used"
    assert len(results[0].photos) == 1


def test_ebay_adapter_handles_missing_shipping():
    adapter = EbayAdapter(app_id="test_id", cert_id="test_cert")

    with patch.object(adapter, '_get_token', new_callable=AsyncMock, return_value="test_token"):
        with patch.object(adapter, '_api_search', new_callable=AsyncMock, return_value=MOCK_SEARCH_RESPONSE):
            filters = SearchFilters(query="lever")
            results = asyncio.run(adapter.search("lever", filters))

    # Second result has no shipping options
    assert results[1].shipping_price is None


def test_ebay_adapter_health_check():
    adapter = EbayAdapter(app_id="test_id", cert_id="test_cert")

    with patch.object(adapter, '_get_token', new_callable=AsyncMock, return_value="test_token"):
        health = asyncio.run(adapter.health_check())
        assert health.healthy is True

    with patch.object(adapter, '_get_token', new_callable=AsyncMock, side_effect=Exception("auth failed")):
        health = asyncio.run(adapter.health_check())
        assert health.healthy is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_ebay_adapter.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write implementation**

```python
# src/adapters/ebay.py
import base64
from typing import Any

import httpx

from src.adapters.base import BaseAdapter, AdapterHealthCheck
from src.core.types import RawListing, SearchFilters

EBAY_AUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

EBAY_MARKETPLACES = [
    ("EBAY_IT", "it"),
    ("EBAY_DE", "de"),
    ("EBAY_FR", "fr"),
    ("EBAY_ES", "es"),
    ("EBAY_GB", "gb"),
]


class EbayAdapter(BaseAdapter):
    source_name = "ebay"
    language = "multi"
    country = "multi"
    currency = "multi"

    def __init__(self, app_id: str, cert_id: str):
        self.app_id = app_id
        self.cert_id = cert_id
        self._token: str | None = None

    async def _get_token(self) -> str:
        if self._token:
            return self._token

        credentials = base64.b64encode(f"{self.app_id}:{self.cert_id}".encode()).decode()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                EBAY_AUTH_URL,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {credentials}",
                },
                data={
                    "grant_type": "client_credentials",
                    "scope": "https://api.ebay.com/oauth/api_scope",
                },
                timeout=10,
            )
            resp.raise_for_status()
            self._token = resp.json()["access_token"]
            return self._token

    async def _api_search(self, query: str, marketplace: str, token: str, limit: int = 50) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                EBAY_SEARCH_URL,
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-EBAY-C-MARKETPLACE-ID": marketplace,
                },
                params={
                    "q": query,
                    "filter": "conditions:{USED}",
                    "limit": str(limit),
                },
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()

    async def search(self, query: str, filters: SearchFilters) -> list[RawListing]:
        token = await self._get_token()
        results: list[RawListing] = []

        for marketplace_id, country_code in EBAY_MARKETPLACES:
            try:
                data = await self._api_search(query, marketplace_id, token)
                items = data.get("itemSummaries", [])

                for item in items:
                    shipping_price = None
                    shipping_opts = item.get("shippingOptions", [])
                    if shipping_opts:
                        cost = shipping_opts[0].get("shippingCost", {})
                        if cost:
                            shipping_price = float(cost.get("value", 0))

                    photos = []
                    image = item.get("image", {})
                    if image and image.get("imageUrl"):
                        photos.append(image["imageUrl"])

                    results.append(RawListing(
                        source_id=item["itemId"],
                        source=self.source_name,
                        title=item.get("title", ""),
                        description=item.get("shortDescription", ""),
                        price=float(item["price"]["value"]),
                        currency=item["price"]["currency"],
                        shipping_price=shipping_price,
                        seller_country=item.get("itemLocation", {}).get("country", country_code.upper()),
                        condition_label=item.get("condition", ""),
                        photos=photos,
                        listing_url=item.get("itemWebUrl", ""),
                    ))
            except Exception:
                continue  # Skip failing marketplaces, try the rest

        return results

    async def health_check(self) -> AdapterHealthCheck:
        try:
            await self._get_token()
            return AdapterHealthCheck(healthy=True, message="eBay API authenticated")
        except Exception as e:
            return AdapterHealthCheck(healthy=False, message=str(e))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_ebay_adapter.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/ebay.py test_scripts/test_ebay_adapter.py
git commit -m "feat: add eBay Browse API adapter with multi-marketplace search"
```

---

## Phase 5: Parts Catalog & Compatibility

Builds the seed data, compatibility resolution, and catalog management. After this phase the search can tag results with compatibility confidence.

---

### Task 13: Parts Catalog Seed Data & Compatibility

**Files:**
- Create: `data/seed/multistrada_1260_enduro.json`
- Create: `src/catalog/models.py`
- Create: `src/catalog/compatibility.py`
- Create: `src/catalog/seed_data.py`
- Create: `test_scripts/test_catalog.py`

- [ ] **Step 1: Create seed data JSON**

```json
{
  "model": "Multistrada 1260 Enduro",
  "year_range": [2019, 2021],
  "enduro_specific_parts": [
    {
      "category": "exhaust",
      "part_name": "Akrapovic Slip-On Exhaust",
      "oem_number": "96481712A",
      "search_aliases": ["akrapovic multistrada enduro", "scarico akrapovic enduro"]
    },
    {
      "category": "protection",
      "part_name": "Skid Plate / Engine Guard",
      "oem_number": "97380961A",
      "search_aliases": ["paracoppa enduro", "motorschutz enduro", "skid plate enduro"]
    },
    {
      "category": "stand",
      "part_name": "Center Stand",
      "oem_number": "55610952AA",
      "search_aliases": ["cavalletto centrale", "hauptständer", "center stand enduro"]
    },
    {
      "category": "seat",
      "part_name": "Rally Seat",
      "oem_number": "96880991A",
      "search_aliases": ["sella rally", "rallye sitzbank", "rally seat enduro"]
    },
    {
      "category": "wheels",
      "part_name": "Spoked Wheel Front",
      "oem_number": "50121561A",
      "search_aliases": ["ruota a raggi anteriore", "speichenrad vorne"]
    },
    {
      "category": "wheels",
      "part_name": "Spoked Wheel Rear",
      "oem_number": "50221561A",
      "search_aliases": ["ruota a raggi posteriore", "speichenrad hinten"]
    },
    {
      "category": "protection",
      "part_name": "Crash Bars",
      "oem_number": "97380971A",
      "search_aliases": ["paramotore", "sturzbügel", "crash bars enduro"]
    },
    {
      "category": "windscreen",
      "part_name": "Touring Windscreen (Enduro)",
      "oem_number": "48710571A",
      "search_aliases": ["cupolino enduro", "windschild enduro", "parabrezza enduro"]
    },
    {
      "category": "suspension",
      "part_name": "Front Fork (Sachs 48mm)",
      "oem_number": "34520861A",
      "search_aliases": ["forcella sachs", "gabel sachs 48mm"]
    }
  ],
  "shared_parts": [
    {
      "category": "controls",
      "part_name": "Clutch Lever",
      "oem_number": "63040601A",
      "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"],
      "search_aliases": ["leva frizione", "Kupplungshebel", "levier embrayage", "clutch lever"]
    },
    {
      "category": "controls",
      "part_name": "Brake Lever",
      "oem_number": "63040501A",
      "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"],
      "search_aliases": ["leva freno", "Bremshebel", "levier frein", "brake lever"]
    },
    {
      "category": "brakes",
      "part_name": "Front Brake Pads",
      "oem_number": "61340961A",
      "compatible_with": ["Multistrada 1260", "Multistrada 1260 S"],
      "search_aliases": ["pastiglie freno anteriori", "Bremsbeläge vorne"]
    },
    {
      "category": "mirrors",
      "part_name": "Mirror Left",
      "oem_number": "52340501A",
      "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"],
      "search_aliases": ["specchietto sinistro", "Spiegel links", "mirror left"]
    },
    {
      "category": "mirrors",
      "part_name": "Mirror Right",
      "oem_number": "52340601A",
      "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"],
      "search_aliases": ["specchietto destro", "Spiegel rechts", "mirror right"]
    },
    {
      "category": "drivetrain",
      "part_name": "Chain Kit",
      "oem_number": "67620711A",
      "compatible_with": ["Multistrada 1260", "Multistrada 1260 S"],
      "search_aliases": ["kit catena", "Kettensatz", "chain kit"]
    },
    {
      "category": "cooling",
      "part_name": "Radiator",
      "oem_number": "54840901A",
      "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"],
      "search_aliases": ["radiatore", "Kühler", "radiateur", "radiator"]
    },
    {
      "category": "electrical",
      "part_name": "Headlight Assembly",
      "oem_number": "52010561A",
      "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"],
      "search_aliases": ["faro anteriore", "Scheinwerfer", "phare", "headlight"]
    }
  ]
}
```

- [ ] **Step 2: Write the failing test**

```python
# test_scripts/test_catalog.py
from pathlib import Path
from src.catalog.seed_data import load_seed_data
from src.catalog.compatibility import CompatibilityResolver
from src.db.database import Database


SEED_PATH = str(Path(__file__).parent.parent / "data" / "seed" / "multistrada_1260_enduro.json")


def test_load_seed_data():
    parts = load_seed_data(SEED_PATH)
    assert len(parts) > 0
    enduro_parts = [p for p in parts if p["enduro_specific"]]
    shared_parts = [p for p in parts if not p["enduro_specific"]]
    assert len(enduro_parts) >= 8
    assert len(shared_parts) >= 8


def test_compatibility_resolver_oem_lookup(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.initialize()

    # Seed the catalog
    parts = load_seed_data(SEED_PATH)
    from src.catalog.seed_data import seed_database
    seed_database(db, SEED_PATH)

    resolver = CompatibilityResolver(db)

    # Clutch lever is shared
    result = resolver.resolve_by_oem("63040601A")
    assert result is not None
    assert result["enduro_specific"] == 0
    assert "Multistrada 1260" in result["compatible_models"]

    # Akrapovic exhaust is enduro-specific
    result = resolver.resolve_by_oem("96481712A")
    assert result is not None
    assert result["enduro_specific"] == 1


def test_compatibility_resolver_by_query(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.initialize()
    from src.catalog.seed_data import seed_database
    seed_database(db, SEED_PATH)

    resolver = CompatibilityResolver(db)

    matches = resolver.resolve_by_name("clutch lever")
    assert len(matches) >= 1
    assert any("Clutch" in m["part_name"] for m in matches)


def test_compatibility_resolver_unknown_part(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.initialize()
    from src.catalog.seed_data import seed_database
    seed_database(db, SEED_PATH)

    resolver = CompatibilityResolver(db)
    result = resolver.resolve_by_oem("UNKNOWN123")
    assert result is None
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_catalog.py -v`
Expected: FAIL with ImportError

- [ ] **Step 4: Write seed_data module**

```python
# src/catalog/seed_data.py
import json
from pathlib import Path

from src.db.database import Database


def load_seed_data(seed_path: str) -> list[dict]:
    path = Path(seed_path)
    if not path.exists():
        raise FileNotFoundError(f"Seed file not found: {seed_path}")

    with open(path) as f:
        data = json.load(f)

    parts = []

    model = data["model"]

    for part in data.get("enduro_specific_parts", []):
        parts.append({
            "oem_number": part["oem_number"],
            "part_name": part["part_name"],
            "category": part["category"],
            "compatible_models": json.dumps([model]),
            "enduro_specific": True,
            "search_aliases": json.dumps(part.get("search_aliases", [])),
        })

    for part in data.get("shared_parts", []):
        compatible = [model] + part.get("compatible_with", [])
        parts.append({
            "oem_number": part["oem_number"],
            "part_name": part["part_name"],
            "category": part["category"],
            "compatible_models": json.dumps(compatible),
            "enduro_specific": False,
            "search_aliases": json.dumps(part.get("search_aliases", [])),
        })

    return parts


def seed_database(db: Database, seed_path: str) -> int:
    parts = load_seed_data(seed_path)
    conn = db._connect()
    count = 0
    for part in parts:
        conn.execute(
            "INSERT OR REPLACE INTO PartsCatalog "
            "(oem_number, part_name, category, compatible_models, enduro_specific, search_aliases) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                part["oem_number"],
                part["part_name"],
                part["category"],
                part["compatible_models"],
                1 if part["enduro_specific"] else 0,
                part["search_aliases"],
            ),
        )
        count += 1
    conn.commit()
    conn.close()
    return count
```

- [ ] **Step 5: Write compatibility resolver**

```python
# src/catalog/compatibility.py
import json

from src.db.database import Database


class CompatibilityResolver:
    def __init__(self, db: Database):
        self.db = db

    def resolve_by_oem(self, oem_number: str) -> dict | None:
        conn = self.db._connect()
        cursor = conn.execute(
            "SELECT * FROM PartsCatalog WHERE oem_number = ?",
            (oem_number,),
        )
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return None
        result = dict(row)
        result["compatible_models"] = json.loads(result["compatible_models"])
        result["search_aliases"] = json.loads(result["search_aliases"])
        return result

    def resolve_by_name(self, query: str) -> list[dict]:
        conn = self.db._connect()
        search_term = f"%{query}%"
        cursor = conn.execute(
            "SELECT * FROM PartsCatalog WHERE "
            "part_name LIKE ? OR search_aliases LIKE ? OR category LIKE ?",
            (search_term, search_term, search_term),
        )
        rows = cursor.fetchall()
        conn.close()
        results = []
        for row in rows:
            result = dict(row)
            result["compatible_models"] = json.loads(result["compatible_models"])
            result["search_aliases"] = json.loads(result["search_aliases"])
            results.append(result)
        return results

    def is_enduro_specific(self, oem_number: str) -> bool | None:
        part = self.resolve_by_oem(oem_number)
        if part is None:
            return None
        return bool(part["enduro_specific"])
```

- [ ] **Step 6: Write models module**

```python
# src/catalog/models.py
from dataclasses import dataclass


@dataclass
class BikeModel:
    name: str
    year_start: int
    year_end: int
    variant: str = ""

    @property
    def display_name(self) -> str:
        years = f"{self.year_start}-{self.year_end}"
        if self.variant:
            return f"{self.name} {self.variant} ({years})"
        return f"{self.name} ({years})"


MULTISTRADA_1260_ENDURO = BikeModel(
    name="Ducati Multistrada",
    year_start=2019,
    year_end=2021,
    variant="1260 Enduro",
)

MULTISTRADA_1260 = BikeModel(
    name="Ducati Multistrada",
    year_start=2018,
    year_end=2020,
    variant="1260",
)
```

- [ ] **Step 7: Run test to verify it passes**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_catalog.py -v`
Expected: All 4 tests PASS

- [ ] **Step 8: Commit**

```bash
git add data/seed/multistrada_1260_enduro.json src/catalog/ test_scripts/test_catalog.py
git commit -m "feat: add parts catalog with seed data, OEM compatibility, and query-based resolution"
```

---

## Phase 6: Watch System & Notifications

Builds the watch manager, cron runner, and macOS notifications. After this phase you can create watches and receive notifications for new listings.

---

### Task 14: Watch Manager & Notifier

**Files:**
- Create: `src/watch/manager.py`
- Create: `src/watch/notifier.py`
- Create: `src/watch/runner.py`
- Create: `test_scripts/test_watch.py`

- [ ] **Step 1: Write the failing test**

```python
# test_scripts/test_watch.py
import asyncio
import json
from unittest.mock import patch, MagicMock
from src.watch.manager import WatchManager
from src.watch.notifier import send_macos_notification
from src.db.database import Database


def test_watch_manager_create_and_list(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.initialize()
    mgr = WatchManager(db)

    watch_id = mgr.create(
        query="clutch lever",
        max_total_price=40.0,
        target_models=["Multistrada 1260 Enduro", "Multistrada 1260"],
        part_category="controls",
    )
    assert watch_id == 1

    watches = mgr.list_active()
    assert len(watches) == 1
    assert watches[0]["query"] == "clutch lever"
    assert watches[0]["max_total_price"] == 40.0


def test_watch_manager_pause_and_resume(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.initialize()
    mgr = WatchManager(db)

    watch_id = mgr.create(query="exhaust", max_total_price=500.0)
    mgr.pause(watch_id)
    assert len(mgr.list_active()) == 0

    mgr.resume(watch_id)
    assert len(mgr.list_active()) == 1


def test_watch_manager_remove(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.initialize()
    mgr = WatchManager(db)

    watch_id = mgr.create(query="lever", max_total_price=30.0)
    mgr.remove(watch_id)
    assert len(mgr.list_all()) == 0


def test_watch_manager_update_budget(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.initialize()
    mgr = WatchManager(db)

    watch_id = mgr.create(query="guard", max_total_price=60.0)
    mgr.update_budget(watch_id, 80.0)

    watches = mgr.list_active()
    assert watches[0]["max_total_price"] == 80.0


def test_macos_notification_command():
    with patch("subprocess.run") as mock_run:
        send_macos_notification(
            title="Ducati Parts Finder",
            message='3 new listings for "clutch lever"',
            subtitle="Best: 18 EUR total (OLX.bg)",
        )
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "osascript" in cmd[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_watch.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write watch manager**

```python
# src/watch/manager.py
import json
from src.db.database import Database


class WatchManager:
    def __init__(self, db: Database):
        self.db = db

    def create(
        self,
        query: str,
        max_total_price: float,
        target_models: list[str] | None = None,
        sources: list[str] | None = None,
        part_category: str = "",
        oem_number: str = "",
    ) -> int:
        return self.db.create_watch({
            "query": query,
            "part_category": part_category,
            "oem_number": oem_number,
            "max_total_price": max_total_price,
            "target_models": json.dumps(target_models or []),
            "sources": json.dumps(sources or []),
            "active": True,
        })

    def list_active(self) -> list[dict]:
        return self.db.get_active_watches()

    def list_all(self) -> list[dict]:
        return self.db.get_all_watches()

    def pause(self, watch_id: int) -> None:
        self.db.deactivate_watch(watch_id)

    def resume(self, watch_id: int) -> None:
        self.db.activate_watch(watch_id)

    def remove(self, watch_id: int) -> None:
        self.db.delete_watch(watch_id)

    def update_budget(self, watch_id: int, new_budget: float) -> None:
        conn = self.db._connect()
        conn.execute(
            "UPDATE Watch SET max_total_price = ? WHERE id = ?",
            (new_budget, watch_id),
        )
        conn.commit()
        conn.close()
```

- [ ] **Step 4: Write notifier**

```python
# src/watch/notifier.py
import subprocess


def send_macos_notification(title: str, message: str, subtitle: str = "", open_url: str = "") -> None:
    script_parts = [
        f'display notification "{_escape(message)}"',
        f'with title "{_escape(title)}"',
    ]
    if subtitle:
        script_parts.append(f'subtitle "{_escape(subtitle)}"')

    script = " ".join(script_parts)
    subprocess.run(["osascript", "-e", script], check=False)

    if open_url:
        subprocess.run(["open", open_url], check=False)


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')
```

- [ ] **Step 5: Write watch runner (cron entry point)**

```python
# src/watch/runner.py
import asyncio
import json
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from src.core.config import load_config
from src.core.search import SearchOrchestrator
from src.core.types import SearchFilters
from src.db.database import Database
from src.reports.html_report import generate_html_report
from src.watch.manager import WatchManager
from src.watch.notifier import send_macos_notification


PROJECT_ROOT = Path(__file__).parent.parent.parent


async def run_watches(config_path: str, db_path: str) -> None:
    config = load_config(config_path)
    db = Database(db_path)
    db.initialize()
    mgr = WatchManager(db)

    # Import adapters here to avoid circular imports at module level
    from src.adapters.ebay import EbayAdapter
    import os
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")

    adapters = {}
    ebay_app_id = os.environ.get("EBAY_APP_ID")
    ebay_cert_id = os.environ.get("EBAY_CERT_ID")
    if ebay_app_id and ebay_cert_id:
        adapters["ebay_eu"] = EbayAdapter(app_id=ebay_app_id, cert_id=ebay_cert_id)

    orchestrator = SearchOrchestrator(config=config, adapters=adapters)

    for watch in mgr.list_active():
        filters = SearchFilters(
            query=watch["query"],
            max_total_price=Decimal(str(watch["max_total_price"])) if watch["max_total_price"] else None,
            target_models=json.loads(watch["target_models"]),
            sources=json.loads(watch["sources"]) if json.loads(watch["sources"]) else [],
        )

        listings = await orchestrator.run(filters)

        # Filter out already-seen listings
        new_listings = [
            l for l in listings
            if not db.is_listing_seen(l.id, watch["id"])
        ]

        if new_listings:
            # Mark as seen
            for listing in new_listings:
                db.mark_listing_seen(listing.id, watch["id"])

            # Generate report
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            report_path = str(PROJECT_ROOT / "reports" / f"watch_{watch['id']}_{timestamp}.html")
            generate_html_report(new_listings, query=watch["query"], output_path=report_path)

            # Send notification
            best = min(new_listings, key=lambda l: l.total_price)
            send_macos_notification(
                title="Ducati Parts Finder",
                message=f'{len(new_listings)} new listings for "{watch["query"]}"',
                subtitle=f"Best: {best.total_price:.2f} EUR total ({best.source})",
                open_url=report_path,
            )

            # Mark as notified
            for listing in new_listings:
                db.mark_listing_notified(listing.id, watch["id"])

        db.update_watch_last_checked(watch["id"])


def main() -> None:
    config_path = str(PROJECT_ROOT / "config" / "config.yaml")
    db_path = str(PROJECT_ROOT / "data" / "ducati_parts.db")
    asyncio.run(run_watches(config_path, db_path))


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_watch.py -v`
Expected: All 5 tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/watch/ test_scripts/test_watch.py
git commit -m "feat: add watch manager, macOS notifier, and cron runner"
```

---

### Task 15: Launchd Plist for Scheduled Watches

**Files:**
- Create: `config/launchd/com.ducati-parts.watcher.plist`
- Create: `src/watch/scheduler.py`

- [ ] **Step 1: Create launchd plist template**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ducati-parts.watcher</string>
    <key>ProgramArguments</key>
    <array>
        <string>__VENV_PYTHON__</string>
        <string>-m</string>
        <string>src.watch.runner</string>
    </array>
    <key>WorkingDirectory</key>
    <string>__PROJECT_ROOT__</string>
    <key>StartInterval</key>
    <integer>14400</integer>
    <key>StandardOutPath</key>
    <string>__PROJECT_ROOT__/data/watcher.log</string>
    <key>StandardErrorPath</key>
    <string>__PROJECT_ROOT__/data/watcher.err</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

- [ ] **Step 2: Write scheduler installer**

```python
# src/watch/scheduler.py
import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent.parent
PLIST_TEMPLATE = PROJECT_ROOT / "config" / "launchd" / "com.ducati-parts.watcher.plist"
PLIST_NAME = "com.ducati-parts.watcher"
LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"


def install_schedule(interval_hours: int = 4) -> str:
    plist_dest = LAUNCH_AGENTS_DIR / f"{PLIST_NAME}.plist"

    template_content = PLIST_TEMPLATE.read_text()
    venv_python = str(PROJECT_ROOT / ".venv" / "bin" / "python")
    content = (
        template_content
        .replace("__VENV_PYTHON__", venv_python)
        .replace("__PROJECT_ROOT__", str(PROJECT_ROOT))
        .replace("<integer>14400</integer>", f"<integer>{interval_hours * 3600}</integer>")
    )

    LAUNCH_AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    plist_dest.write_text(content)

    subprocess.run(["launchctl", "unload", str(plist_dest)], check=False, capture_output=True)
    subprocess.run(["launchctl", "load", str(plist_dest)], check=True)

    return str(plist_dest)


def uninstall_schedule() -> None:
    plist_dest = LAUNCH_AGENTS_DIR / f"{PLIST_NAME}.plist"
    if plist_dest.exists():
        subprocess.run(["launchctl", "unload", str(plist_dest)], check=False, capture_output=True)
        plist_dest.unlink()


def is_installed() -> bool:
    plist_dest = LAUNCH_AGENTS_DIR / f"{PLIST_NAME}.plist"
    return plist_dest.exists()
```

- [ ] **Step 3: Commit**

```bash
git add config/launchd/com.ducati-parts.watcher.plist src/watch/scheduler.py
git commit -m "feat: add launchd scheduler for periodic watch execution"
```

---

## Phase 7: CLI Entry Point & Skill Definition

Wires everything together with a Python CLI entry point and the Claude Code SKILL.md. After this phase the skill is fully usable for on-demand searches via Claude Code.

---

### Task 16: CLI Entry Point

**Files:**
- Create: `src/cli.py`
- Create: `test_scripts/test_cli.py`

- [ ] **Step 1: Write the failing test**

```python
# test_scripts/test_cli.py
import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
from src.cli import run_search, run_watch_list


def test_run_search_outputs_results(tmp_path, capsys):
    mock_listing = MagicMock()
    mock_listing.id = "mock_1"
    mock_listing.source = "olx_bg"
    mock_listing.title = "Clutch lever"
    mock_listing.total_price = 15.00
    mock_listing.part_price = 10.00
    mock_listing.shipping_price = 5.00
    mock_listing.seller_country = "BG"
    mock_listing.is_eu = True
    mock_listing.condition_score.value = "green"
    mock_listing.shipping_ratio_flag = False
    mock_listing.listing_url = "https://olx.bg/1"
    mock_listing.photos = []
    mock_listing.compatible_models = ["Multistrada 1260 Enduro"]
    mock_listing.compatibility_confidence.value = "verify"
    mock_listing.oem_part_number = ""
    mock_listing.condition_raw = "Good"
    mock_listing.condition_notes = "OK"
    mock_listing.description = "Good"
    mock_listing.currency_original = "EUR"
    mock_listing.date_listed = "2026-04-14"
    mock_listing.date_found = "2026-04-14"

    config_path = str(tmp_path / "config.yaml")
    Path(config_path).write_text("""
bike:
  default_model: "Multistrada 1260 Enduro"
  year_range: [2019, 2021]
  also_compatible: ["Multistrada 1260"]
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
  1: [mock]
  2: []
  3: []
""")

    with patch("src.cli.SearchOrchestrator") as MockOrch:
        instance = MockOrch.return_value
        instance.run = AsyncMock(return_value=[mock_listing])
        instance.last_errors = {}

        reports_dir = str(tmp_path / "reports")
        asyncio.run(run_search(
            query="clutch lever",
            config_path=config_path,
            reports_dir=reports_dir,
            adapters={},
        ))

    captured = capsys.readouterr()
    assert "clutch lever" in captured.out.lower() or "1" in captured.out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_cli.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write CLI entry point**

```python
# src/cli.py
import asyncio
import json
import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

from src.core.config import load_config
from src.core.search import SearchOrchestrator
from src.core.types import SearchFilters
from src.db.database import Database
from src.reports.html_report import generate_html_report
from src.reports.terminal_report import format_terminal_report
from src.watch.manager import WatchManager


PROJECT_ROOT = Path(__file__).parent.parent


def _get_adapters() -> dict:
    adapters = {}
    ebay_app_id = os.environ.get("EBAY_APP_ID")
    ebay_cert_id = os.environ.get("EBAY_CERT_ID")
    if ebay_app_id and ebay_cert_id:
        from src.adapters.ebay import EbayAdapter
        adapters["ebay_eu"] = EbayAdapter(app_id=ebay_app_id, cert_id=ebay_cert_id)
    return adapters


async def run_search(
    query: str,
    config_path: str | None = None,
    reports_dir: str | None = None,
    max_total_price: float | None = None,
    tiers: list[int] | None = None,
    sources: list[str] | None = None,
    adapters: dict | None = None,
) -> str:
    if config_path is None:
        config_path = str(PROJECT_ROOT / "config" / "config.yaml")
    if reports_dir is None:
        reports_dir = str(PROJECT_ROOT / "reports")

    config = load_config(config_path)

    if adapters is None:
        adapters = _get_adapters()

    orchestrator = SearchOrchestrator(config=config, adapters=adapters)

    filters = SearchFilters(
        query=query,
        max_total_price=Decimal(str(max_total_price)) if max_total_price else None,
        tiers=tiers or config.search.default_tiers,
        sources=sources or [],
    )

    listings = await orchestrator.run(filters)

    # Generate reports
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    safe_query = query.replace(" ", "-").replace("/", "-")[:50]
    report_path = str(Path(reports_dir) / f"{timestamp}_{safe_query}.html")

    generate_html_report(listings, query=query, output_path=report_path)

    # Terminal output
    output = format_terminal_report(listings, query=query, report_path=report_path)
    print(output)

    # Report adapter errors
    if orchestrator.last_errors:
        print("\nAdapter errors:")
        for name, error in orchestrator.last_errors.items():
            print(f"  {name}: {error}")

    return report_path


async def run_watch_list(config_path: str | None = None, db_path: str | None = None) -> str:
    if config_path is None:
        config_path = str(PROJECT_ROOT / "config" / "config.yaml")
    if db_path is None:
        db_path = str(PROJECT_ROOT / "data" / "ducati_parts.db")

    db = Database(db_path)
    db.initialize()
    mgr = WatchManager(db)

    watches = mgr.list_all()
    if not watches:
        return "No watches configured."

    lines = ["Active watches:"]
    for w in watches:
        status = "active" if w["active"] else "paused"
        last = w["last_checked"] or "never"
        lines.append(
            f"  {w['id']}. [{status}] \"{w['query']}\" | "
            f"Budget: {w['max_total_price']:.2f} EUR | Last check: {last}"
        )

    output = "\n".join(lines)
    print(output)
    return output
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_cli.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/cli.py test_scripts/test_cli.py
git commit -m "feat: add CLI entry point for search and watch list operations"
```

---

### Task 17: Claude Code Skill Definition

**Files:**
- Create: `.claude/skills/ducati-parts/SKILL.md`

- [ ] **Step 1: Write the SKILL.md**

```markdown
---
name: ducati-parts
description: Find used Ducati Multistrada 1260 Enduro parts across European marketplaces. Search on-demand, manage watch lists, check compatibility.
---

# Ducati Parts Finder

You help the user find used parts for their Ducati Multistrada 1260 Enduro across European marketplaces.

## Setup

Working directory: `/Users/thanos/Work/Repos/ducati-parts`
Always activate the venv before running Python: `source .venv/bin/activate`

## Capabilities

### On-Demand Search

When the user asks to find a part (e.g., "find me a clutch lever", "search for exhaust"):

1. Determine the part name from the user's request
2. Check the parts catalog for compatibility info:
   ```bash
   cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -c "
   from src.catalog.compatibility import CompatibilityResolver
   from src.db.database import Database
   db = Database('data/ducati_parts.db')
   db.initialize()
   resolver = CompatibilityResolver(db)
   matches = resolver.resolve_by_name('<PART_NAME>')
   for m in matches:
       print(f\"OEM: {m['oem_number']} | {m['part_name']} | Enduro-specific: {m['enduro_specific']} | Fits: {m['compatible_models']}\")
   "
   ```
3. Run the search:
   ```bash
   cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -c "
   import asyncio
   from src.cli import run_search
   asyncio.run(run_search(
       query='<SEARCH_QUERY>',
       max_total_price=<BUDGET_OR_None>,
       tiers=<TIERS_OR_None>,
   ))
   "
   ```
4. Present the terminal summary to the user
5. Mention the HTML report path for detailed review

### Query Translation

Before searching, translate the user's query into search terms for each platform's language. The search orchestrator handles adapter routing, but you should expand the query to include:
- The bike model name
- Compatible model names (for shared parts)
- OEM part number if known from catalog

Example: User says "clutch lever" -> search with "clutch lever multistrada 1260" and include "Multistrada 1260 Enduro" + "Multistrada 1260" for shared parts.

### Watch List Management

- **Create watch:** Extract query, budget, and optional tier preferences from user request. Run:
  ```bash
  cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -c "
  from src.db.database import Database
  from src.watch.manager import WatchManager
  db = Database('data/ducati_parts.db')
  db.initialize()
  mgr = WatchManager(db)
  wid = mgr.create(query='<QUERY>', max_total_price=<BUDGET>, target_models=[<MODELS>])
  print(f'Watch created: ID {wid}')
  "
  ```

- **List watches:** `asyncio.run(run_watch_list())`

- **Pause/resume/remove:** Use `mgr.pause(ID)`, `mgr.resume(ID)`, `mgr.remove(ID)`

- **Update budget:** `mgr.update_budget(ID, NEW_AMOUNT)`

### Install/Uninstall Cron

When user creates their first watch, offer to install the scheduler:
```bash
cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -c "
from src.watch.scheduler import install_schedule
path = install_schedule(interval_hours=4)
print(f'Scheduler installed at {path}')
"
```

### Bike Switching

If the user asks to switch to a different bike model, update the config. The default is Multistrada 1260 Enduro. Active watches remain on their original model.

### Compatibility Queries

When the user asks "does X fit my bike?" or "is Y compatible?":
1. Check catalog by OEM number or name
2. Report whether it's Enduro-specific or shared
3. If not in catalog, suggest checking manually and offer to add it

## Search Tiers

- **Tier 1** (cheapest, always searched): Bulgaria, Romania, Hungary, Poland, Czech Republic, Slovakia, Croatia, Slovenia
- **Tier 2** (default): Italy (Subito), eBay EU, moto breaker sites
- **Tier 3** (opt-in): Germany, France, Spain, UK (UK has customs)

Default searches Tier 1 + 2. User can say "search everywhere" for all tiers or "cheap countries only" for Tier 1 only.

## Condition Scoring

Results are scored green/yellow/red. You assess condition from listing descriptions and photos:
- **Green:** Seller states good/excellent condition, photos show clean part
- **Yellow:** Vague description, no photos, or unclear condition
- **Red:** Mentions wear/scratches but functional

Never auto-exclude yellow or red -- present all to the user for final decision.

## Important Notes

- Only used parts, never new
- All prices in EUR (converted automatically)
- Shipping destination: Athens, Greece 15562
- Flag listings where shipping > 50% of part price
- EU sellers = no customs. UK = customs warning
- Missing .env keys will raise exceptions -- no fallbacks
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/ducati-parts/SKILL.md
git commit -m "feat: add Claude Code skill definition for Ducati parts finder"
```

---

## Phase 8: Playwright Browser Adapter Base

Builds the shared Playwright browser automation base that all non-API adapters inherit from. Individual site adapters are added incrementally after this.

---

### Task 18: Playwright Base Adapter

**Files:**
- Create: `src/adapters/playwright_base.py`
- Create: `test_scripts/test_playwright_base.py`

- [ ] **Step 1: Write the failing test**

```python
# test_scripts/test_playwright_base.py
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.adapters.base import AdapterHealthCheck
from src.core.types import RawListing, SearchFilters


class TestPlaywrightAdapter(PlaywrightBaseAdapter):
    source_name = "test_pw"
    language = "en"
    country = "GB"
    currency = "GBP"
    base_url = "https://example.com"

    async def _extract_listings(self, page, query: str) -> list[RawListing]:
        return [
            RawListing(
                source_id="pw1", source=self.source_name, title="Test part",
                description="Good", price=20.0, currency=self.currency,
                shipping_price=None, seller_country=self.country,
                condition_label="Good", photos=[], listing_url="https://example.com/1",
            )
        ]

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/search?q={query}"


def test_playwright_adapter_has_required_attrs():
    adapter = TestPlaywrightAdapter()
    assert adapter.source_name == "test_pw"
    assert adapter.base_url == "https://example.com"


def test_playwright_adapter_builds_search_url():
    adapter = TestPlaywrightAdapter()
    url = adapter._build_search_url("clutch lever")
    assert "clutch lever" in url
    assert "example.com" in url
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_playwright_base.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write implementation**

```python
# src/adapters/playwright_base.py
import asyncio
from abc import abstractmethod

from playwright.async_api import async_playwright, Page, Browser

from src.adapters.base import BaseAdapter, AdapterHealthCheck
from src.core.types import RawListing, SearchFilters


class PlaywrightBaseAdapter(BaseAdapter):
    base_url: str
    _browser: Browser | None = None

    async def _get_browser(self) -> Browser:
        if self._browser is None or not self._browser.is_connected():
            pw = await async_playwright().start()
            self._browser = await pw.chromium.launch(headless=True)
        return self._browser

    async def search(self, query: str, filters: SearchFilters) -> list[RawListing]:
        browser = await self._get_browser()
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            locale=self.language,
        )
        page = await context.new_page()

        try:
            url = self._build_search_url(query)
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)  # Respectful delay
            results = await self._extract_listings(page, query)
            return results
        finally:
            await context.close()

    async def health_check(self) -> AdapterHealthCheck:
        try:
            browser = await self._get_browser()
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(self.base_url, wait_until="domcontentloaded", timeout=15000)
            await context.close()
            return AdapterHealthCheck(healthy=True, message=f"{self.source_name} reachable")
        except Exception as e:
            return AdapterHealthCheck(healthy=False, message=str(e))

    @abstractmethod
    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        ...

    @abstractmethod
    def _build_search_url(self, query: str) -> str:
        ...

    async def close(self) -> None:
        if self._browser and self._browser.is_connected():
            await self._browser.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_playwright_base.py -v`
Expected: All 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/playwright_base.py test_scripts/test_playwright_base.py
git commit -m "feat: add Playwright base adapter for browser-automated marketplace scraping"
```

---

### Task 19: OLX Adapter (Bulgaria, Romania, Poland)

**Files:**
- Create: `src/adapters/olx.py`
- Create: `test_scripts/test_olx_adapter.py`

- [ ] **Step 1: Write the failing test**

```python
# test_scripts/test_olx_adapter.py
from src.adapters.olx import OlxBgAdapter, OlxRoAdapter, OlxPlAdapter


def test_olx_bg_search_url():
    adapter = OlxBgAdapter()
    url = adapter._build_search_url("лост съединител мултистрада")
    assert "olx.bg" in url
    assert "мултистрада" in url or "search" in url


def test_olx_ro_search_url():
    adapter = OlxRoAdapter()
    url = adapter._build_search_url("maneta ambreiaj multistrada")
    assert "olx.ro" in url


def test_olx_pl_search_url():
    adapter = OlxPlAdapter()
    url = adapter._build_search_url("dzwignia sprzegla multistrada")
    assert "olx.pl" in url


def test_olx_bg_properties():
    adapter = OlxBgAdapter()
    assert adapter.source_name == "olx_bg"
    assert adapter.country == "BG"
    assert adapter.currency == "BGN"


def test_olx_ro_properties():
    adapter = OlxRoAdapter()
    assert adapter.source_name == "olx_ro"
    assert adapter.country == "RO"
    assert adapter.currency == "RON"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_olx_adapter.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write implementation**

```python
# src/adapters/olx.py
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

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/ads/q-{quote(query)}/"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        cards = await page.query_selector_all("[data-cy='l-card']")

        for card in cards[:50]:
            try:
                title_el = await card.query_selector("h6")
                title = await title_el.inner_text() if title_el else ""

                price_el = await card.query_selector("[data-testid='ad-price']")
                price_text = await price_el.inner_text() if price_el else "0"
                price = self._parse_price(price_text)

                link_el = await card.query_selector("a")
                href = await link_el.get_attribute("href") if link_el else ""
                listing_url = f"{self.base_url}{href}" if href and not href.startswith("http") else href

                img_el = await card.query_selector("img")
                photo_url = await img_el.get_attribute("src") if img_el else ""
                photos = [photo_url] if photo_url else []

                location_el = await card.query_selector("[data-testid='location-date']")
                location = await location_el.inner_text() if location_el else ""

                results.append(RawListing(
                    source_id=href.split("/")[-1].split(".")[0] if href else str(len(results)),
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
                ))
            except Exception:
                continue

        return results

    @staticmethod
    def _parse_price(text: str) -> float:
        cleaned = "".join(c for c in text if c.isdigit() or c in ".,")
        cleaned = cleaned.replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0


class OlxRoAdapter(PlaywrightBaseAdapter):
    source_name = "olx_ro"
    language = "ro"
    country = "RO"
    currency = "RON"
    base_url = "https://www.olx.ro"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/oferte/q-{quote(query)}/"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        cards = await page.query_selector_all("[data-cy='l-card']")

        for card in cards[:50]:
            try:
                title_el = await card.query_selector("h6")
                title = await title_el.inner_text() if title_el else ""

                price_el = await card.query_selector("[data-testid='ad-price']")
                price_text = await price_el.inner_text() if price_el else "0"
                price = OlxBgAdapter._parse_price(price_text)

                link_el = await card.query_selector("a")
                href = await link_el.get_attribute("href") if link_el else ""
                listing_url = f"{self.base_url}{href}" if href and not href.startswith("http") else href

                img_el = await card.query_selector("img")
                photo_url = await img_el.get_attribute("src") if img_el else ""
                photos = [photo_url] if photo_url else []

                results.append(RawListing(
                    source_id=href.split("/")[-1].split(".")[0] if href else str(len(results)),
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
                ))
            except Exception:
                continue

        return results


class OlxPlAdapter(PlaywrightBaseAdapter):
    source_name = "olx_pl"
    language = "pl"
    country = "PL"
    currency = "PLN"
    base_url = "https://www.olx.pl"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/oferty/q-{quote(query)}/"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        cards = await page.query_selector_all("[data-cy='l-card']")

        for card in cards[:50]:
            try:
                title_el = await card.query_selector("h6")
                title = await title_el.inner_text() if title_el else ""

                price_el = await card.query_selector("[data-testid='ad-price']")
                price_text = await price_el.inner_text() if price_el else "0"
                price = OlxBgAdapter._parse_price(price_text)

                link_el = await card.query_selector("a")
                href = await link_el.get_attribute("href") if link_el else ""
                listing_url = f"{self.base_url}{href}" if href and not href.startswith("http") else href

                img_el = await card.query_selector("img")
                photo_url = await img_el.get_attribute("src") if img_el else ""
                photos = [photo_url] if photo_url else []

                results.append(RawListing(
                    source_id=href.split("/")[-1].split(".")[0] if href else str(len(results)),
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
                ))
            except Exception:
                continue

        return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_olx_adapter.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/olx.py test_scripts/test_olx_adapter.py
git commit -m "feat: add OLX adapters for Bulgaria, Romania, and Poland"
```

---

### Task 20: Subito.it Adapter

**Files:**
- Create: `src/adapters/subito.py`
- Create: `test_scripts/test_subito_adapter.py`

- [ ] **Step 1: Write the failing test**

```python
# test_scripts/test_subito_adapter.py
from src.adapters.subito import SubitoAdapter


def test_subito_search_url():
    adapter = SubitoAdapter()
    url = adapter._build_search_url("leva frizione multistrada 1260")
    assert "subito.it" in url
    assert "multistrada" in url or "q=" in url


def test_subito_properties():
    adapter = SubitoAdapter()
    assert adapter.source_name == "subito_it"
    assert adapter.country == "IT"
    assert adapter.currency == "EUR"
    assert adapter.language == "it"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_subito_adapter.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write implementation**

```python
# src/adapters/subito.py
from urllib.parse import quote

from playwright.async_api import Page

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing


class SubitoAdapter(PlaywrightBaseAdapter):
    source_name = "subito_it"
    language = "it"
    country = "IT"
    currency = "EUR"
    base_url = "https://www.subito.it"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/annunci-italia/vendita/usato/?q={quote(query)}"

    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]:
        results: list[RawListing] = []
        cards = await page.query_selector_all("[class*='ItemCard']")
        if not cards:
            cards = await page.query_selector_all(".items__item")

        for card in cards[:50]:
            try:
                title_el = await card.query_selector("h2, [class*='title']")
                title = await title_el.inner_text() if title_el else ""

                price_el = await card.query_selector("[class*='price'], p[class*='Price']")
                price_text = await price_el.inner_text() if price_el else "0"
                price = self._parse_price(price_text)

                link_el = await card.query_selector("a")
                href = await link_el.get_attribute("href") if link_el else ""
                listing_url = href if href.startswith("http") else f"{self.base_url}{href}"

                img_el = await card.query_selector("img")
                photo_url = await img_el.get_attribute("src") if img_el else ""
                photos = [photo_url] if photo_url and "placeholder" not in photo_url else []

                source_id = href.split("/")[-1].split(".")[0] if href else str(len(results))

                results.append(RawListing(
                    source_id=source_id,
                    source=self.source_name,
                    title=title.strip(),
                    description="",
                    price=price,
                    currency=self.currency,
                    shipping_price=None,
                    seller_country=self.country,
                    condition_label="",
                    photos=photos,
                    listing_url=listing_url,
                ))
            except Exception:
                continue

        return results

    @staticmethod
    def _parse_price(text: str) -> float:
        cleaned = "".join(c for c in text if c.isdigit() or c in ".,")
        cleaned = cleaned.replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/test_subito_adapter.py -v`
Expected: All 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/subito.py test_scripts/test_subito_adapter.py
git commit -m "feat: add Subito.it adapter for Italian marketplace"
```

---

### Task 21: Remaining Browser Adapters (Skeleton)

Each remaining adapter follows the exact same pattern as OLX and Subito. This task creates the skeleton implementations that need site-specific CSS selectors refined during live testing.

**Files:**
- Create: `src/adapters/kleinanzeigen.py`
- Create: `src/adapters/leboncoin.py`
- Create: `src/adapters/wallapop.py`
- Create: `src/adapters/allegro.py`
- Create: `src/adapters/jofogas.py`
- Create: `src/adapters/bazos.py`
- Create: `src/adapters/njuskalo.py`
- Create: `src/adapters/bolha.py`
- Create: `src/adapters/facebook.py`
- Create: `src/adapters/moto_breakers.py`

Each adapter must:
1. Extend `PlaywrightBaseAdapter`
2. Set correct `source_name`, `language`, `country`, `currency`, `base_url`
3. Implement `_build_search_url(query)` with correct URL pattern
4. Implement `_extract_listings(page, query)` with site-specific CSS selectors
5. Include a `_parse_price` method for locale-specific number formats

- [ ] **Step 1: Create all adapter files following the OLX/Subito pattern**

Each file follows the same structure. The CSS selectors will need refinement during live testing, but the URL patterns and properties should be correct.

- [ ] **Step 2: Create basic property tests for each adapter**

Similar to `test_olx_adapter.py` -- verify `source_name`, `country`, `currency`, and `_build_search_url`.

- [ ] **Step 3: Commit**

```bash
git add src/adapters/*.py test_scripts/test_*_adapter.py
git commit -m "feat: add skeleton browser adapters for all remaining European marketplaces"
```

---

## Phase 9: Project Documentation & Final Wiring

### Task 22: Issues File & Project Design Doc

**Files:**
- Create: `Issues - Pending Items.md`
- Create: `docs/design/project-design.md`

- [ ] **Step 1: Create Issues file**

```markdown
# Issues - Pending Items

## Pending

### High Priority

1. **Facebook adapter fragility** - Facebook actively blocks automation. The Facebook adapter will require periodic maintenance as selectors and anti-bot measures change. Consider email notification fallback from Facebook Groups.

2. **CSS selector validation** - All Playwright-based adapters have initial CSS selectors that need validation against live sites. Each adapter should be tested manually against its target platform.

3. **OEM part number database expansion** - The seed data covers ~17 parts. The catalog needs expanding with more OEM numbers as the user discovers compatible parts.

### Medium Priority

4. **Currency rate caching** - ECB rates are fetched on every search. Should cache rates for 24 hours to reduce API calls.

5. **Shipping estimate refinement** - Current estimates are rough ranges. Could be improved with actual shipping calculator APIs from major carriers (DHL, DPD, etc.).

### Low Priority

6. **eBay additional image extraction** - Currently only extracts the primary listing image. The Browse API supports fetching additional images.

## Completed

(none yet)
```

- [ ] **Step 2: Create project-design.md**

Copy the spec content from `docs/superpowers/specs/2026-04-14-ducati-parts-finder-design.md` to `docs/design/project-design.md` as the canonical project design document.

- [ ] **Step 3: Commit**

```bash
git add "Issues - Pending Items.md" docs/design/project-design.md
git commit -m "docs: add issues tracker and project design document"
```

---

### Task 23: Adapter Registration & End-to-End Wiring

**Files:**
- Create: `src/adapters/registry.py`
- Modify: `src/cli.py`

- [ ] **Step 1: Write adapter registry**

```python
# src/adapters/registry.py
import os

from src.adapters.base import BaseAdapter
from src.adapters.ebay import EbayAdapter
from src.adapters.olx import OlxBgAdapter, OlxRoAdapter, OlxPlAdapter
from src.adapters.subito import SubitoAdapter


def build_adapter_registry() -> dict[str, BaseAdapter]:
    adapters: dict[str, BaseAdapter] = {}

    # eBay (API-based, requires credentials)
    ebay_app_id = os.environ.get("EBAY_APP_ID")
    ebay_cert_id = os.environ.get("EBAY_CERT_ID")
    if ebay_app_id and ebay_cert_id:
        adapters["ebay_eu"] = EbayAdapter(app_id=ebay_app_id, cert_id=ebay_cert_id)

    # Tier 1: Cheap Eastern EU
    adapters["olx_bg"] = OlxBgAdapter()
    adapters["olx_ro"] = OlxRoAdapter()
    adapters["olx_pl"] = OlxPlAdapter()  # also allegro_pl

    # Tier 2: Moderate
    adapters["subito_it"] = SubitoAdapter()

    # Additional adapters registered here as they are built:
    # adapters["allegro_pl"] = AllegroAdapter()
    # adapters["jofogas_hu"] = JofogasAdapter()
    # adapters["bazos_cz"] = BazosCzAdapter()
    # adapters["bazos_sk"] = BazosSkAdapter()
    # adapters["njuskalo_hr"] = NjuskaloAdapter()
    # adapters["bolha_si"] = BolhaAdapter()
    # adapters["kleinanzeigen_de"] = KleinanzeigenAdapter()
    # adapters["leboncoin_fr"] = LeboncoinAdapter()
    # adapters["wallapop_es"] = WallapopAdapter()

    return adapters
```

- [ ] **Step 2: Update CLI to use registry**

In `src/cli.py`, replace the `_get_adapters()` function:

```python
from src.adapters.registry import build_adapter_registry

def _get_adapters() -> dict:
    return build_adapter_registry()
```

- [ ] **Step 3: Seed the database on first run**

Add to `src/cli.py` in `run_search`:

```python
# Initialize catalog if needed
from src.catalog.seed_data import seed_database
seed_path = str(PROJECT_ROOT / "data" / "seed" / "multistrada_1260_enduro.json")
if Path(seed_path).exists():
    db = Database(str(PROJECT_ROOT / "data" / "ducati_parts.db"))
    db.initialize()
    seed_database(db, seed_path)
```

- [ ] **Step 4: Commit**

```bash
git add src/adapters/registry.py src/cli.py
git commit -m "feat: add adapter registry and wire end-to-end search pipeline"
```

---

### Task 24: Run Full Test Suite

- [ ] **Step 1: Run all tests**

Run: `cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -m pytest test_scripts/ -v`
Expected: All tests PASS

- [ ] **Step 2: Fix any failures**

If any tests fail, fix the root cause and re-run.

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "chore: ensure full test suite passes"
```
