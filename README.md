# Ducati Parts Finder

A Claude Code skill that finds used Ducati parts across 15+ European marketplaces, prioritizing cheap Eastern EU sources for cost arbitrage. The target bike model is configurable via the `BIKE_MODEL` environment variable (defaults to Multistrada 1260 Enduro).

## What It Does

- **Searches 15+ marketplaces** across Europe for used motorcycle parts
- **Prioritizes cheap countries** (Bulgaria, Romania, Hungary, Poland) where parts cost significantly less
- **Estimates total cost** (part + shipping to Athens, Greece) and flags expensive shipping
- **Assesses part condition** with multi-language keyword filtering and green/yellow/red scoring
- **Checks compatibility** via OEM part number cross-referencing between Multistrada 1260 and 1260 Enduro
- **Watch lists** with macOS native notifications when matching parts appear
- **Reports** in terminal summary and rich HTML with photos, filtering, and condition color coding

## Marketplace Coverage

### Tier 1 -- Cheap Eastern EU (searched by default)
OLX Bulgaria, OLX Romania, OLX Poland, Allegro (PL), Jofogas (HU), Bazos (CZ/SK), Njuskalo (HR), Bolha (SI)

### Tier 2 -- Moderate (searched by default)
Subito.it (IT), eBay EU (IT/DE/FR/ES/GB), Moto Breakers (GB)

### Tier 3 -- Expensive Western EU (opt-in)
Kleinanzeigen (DE), Leboncoin (FR), Wallapop (ES), Facebook Marketplace

## Setup

### Prerequisites

- Python 3.12+
- [UV](https://docs.astral.sh/uv/) package manager
- [Playwright](https://playwright.dev/python/) browsers (for scraping)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (to use as a skill)

### Installation

```bash
cd ducati-parts
uv sync
source .venv/bin/activate
playwright install chromium
```

### Configuration

1. Copy `.env.example` to `.env` and configure:
   ```
   # Required: which Ducati model to search for
   BIKE_MODEL=Multistrada 1260 Enduro

   # Optional: eBay API credentials (other adapters work without it)
   EBAY_APP_ID=your_app_id
   EBAY_CERT_ID=your_cert_id
   ```

2. Edit `config/config.yaml` to adjust shipping destination, tier preferences, or watch interval. The `BIKE_MODEL` env var overrides the `bike.default_model` value in the YAML config.

## Usage

### As a Claude Code Skill

The skill is installed at `.claude/skills/ducati-parts/SKILL.md`. When working in this directory, Claude Code can:

- **Search:** "Find me a clutch lever" / "Search for exhaust under 200 EUR"
- **Watch:** "Watch for a windscreen under 150 EUR" / "List my watches"
- **Compatibility:** "Does the 1260 exhaust fit the Enduro?"
- **Tiers:** "Search cheap countries only" / "Search everywhere"

### Programmatic

```python
import asyncio
from src.cli import run_search

# Search for a part
asyncio.run(run_search(
    query="clutch lever multistrada 1260",
    max_total_price=100,  # EUR budget cap
    tiers=[1, 2],         # search tiers
))
```

### Watch Lists

```python
from src.db.database import Database
from src.watch.manager import WatchManager

db = Database("data/ducati_parts.db")
db.initialize()
mgr = WatchManager(db)

# Create a watch
mgr.create(query="windscreen multistrada enduro", max_total_price=150.0)

# Install scheduled checks (every 4 hours via launchd)
from src.watch.scheduler import install_schedule
install_schedule(interval_hours=4)
```

## Architecture

```
src/
  adapters/       # Marketplace adapters (eBay API + Playwright scrapers)
    registry.py   # Central adapter registration
    ebay.py       # eBay Browse API (OAuth2)
    olx.py        # OLX BG/RO/PL
    subito.py     # Subito.it
    ...           # 10 more skeleton adapters
  core/
    config.py     # YAML config loader
    types.py      # Listing, SearchFilters, enums
    search.py     # Search orchestrator (tier routing, filtering, dedup)
    shipping.py   # Shipping cost estimation by country
    currency.py   # ECB rate conversion
    condition.py  # Multi-language condition filtering
  catalog/
    compatibility.py  # OEM cross-reference resolver
    seed_data.py      # Parts catalog seeder
  db/
    database.py   # SQLite layer (listings, watches, seen, catalog)
  reports/
    terminal_report.py  # Terminal summary formatter
    html_report.py      # Jinja2 HTML report generator
  watch/
    manager.py    # Watch CRUD
    runner.py     # Cron entry point
    notifier.py   # macOS native notifications
    scheduler.py  # launchd plist management
  cli.py          # CLI entry point
```

## Testing

```bash
source .venv/bin/activate
python -m pytest test_scripts/ -v
```

174 tests covering all core modules, adapters, and integrations.

## Key Design Decisions

- **Total cost filtering:** Budget caps apply to part + shipping combined, not just part price
- **No ORM:** Direct `sqlite3` for simplicity and control
- **Pluggable adapters:** eBay uses its Browse API; everything else uses Playwright headless Chrome
- **Skeleton adapters:** CSS selectors for browser-based scrapers need refinement against live sites
- **No config fallbacks:** Missing configuration raises exceptions rather than silently defaulting
- **EU preferred:** UK listings include a customs warning; non-EU sellers are excluded

## License

See [LICENSE](LICENSE).
