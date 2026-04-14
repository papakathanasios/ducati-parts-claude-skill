# Ducati Used Parts Finder -- Design Specification

**Date:** 2026-04-14
**Status:** Draft
**Bike:** Ducati Multistrada 1260 Enduro (2019-2021)

## Overview

A Claude Code skill local to `/Users/thanos/Work/Repos/ducati-parts/` that finds used motorcycle parts across European marketplaces at competitive prices. The skill prioritizes cheaper Eastern EU markets first, estimates shipping to Athens (15562), assesses part condition using AI, and monitors watch lists on a schedule with macOS notifications.

## Requirements

- Search used parts (only used, never new) across 15+ European marketplaces
- Default bike: Ducati Multistrada 1260 Enduro, switchable to other Ducati models on demand
- Handle part compatibility: some parts are Enduro-specific, others shared with Multistrada 1260
- Filter by total cost (part + shipping), with a warning when shipping exceeds 50% of part price
- Assess condition via multi-stage pipeline: keyword exclusion, label normalization, AI photo/description analysis
- Present results as terminal summary + rich HTML report
- Support persistent watch lists with cron-based monitoring and macOS native notifications
- Support free text queries, OEM part numbers, and category browsing
- Translate queries into 10+ languages to match each platform's locale
- All EU countries -- no customs. Non-EU (UK) flagged with customs/VAT warning

## Architecture

```
+-----------------------------------------------------+
|                  Claude Code Skill                   |
|          (.claude/skills/ducati-parts/SKILL.md)      |
|                                                      |
|  - Natural language query understanding              |
|  - Multi-language search term generation             |
|  - Condition assessment (descriptions + photos)      |
|  - Compatibility cross-referencing                   |
|  - Conversational refinement                         |
+----------------+------------------------+------------+
                 | invokes via Bash       | reads results
                 v                        v
+------------------------------------------------------+
|                   Python Backend                      |
|                   (src/)                              |
|                                                      |
|  +-------------+  +--------------+  +-------------+  |
|  | Source       |  | Parts        |  | Report      |  |
|  | Adapters     |  | Catalog      |  | Generator   |  |
|  |              |  |              |  |             |  |
|  | - eBay API   |  | - OEM nums   |  | - HTML      |  |
|  | - OLX        |  | - Compat map |  | - Terminal  |  |
|  | - Subito     |  | - Categories |  | - JSON      |  |
|  | - Klein.     |  |              |  |             |  |
|  | - Leboncoin  |  |              |  |             |  |
|  | - Allegro    |  |              |  |             |  |
|  | - Facebook   |  |              |  |             |  |
|  | - Jofogas    |  |              |  |             |  |
|  | - Bazos      |  |              |  |             |  |
|  | - Njuskalo   |  |              |  |             |  |
|  | - Bolha      |  |              |  |             |  |
|  | - Wallapop   |  |              |  |             |  |
|  | - Moto sites |  |              |  |             |  |
|  +-------------+  +--------------+  +-------------+  |
|                                                      |
|  +-------------+  +--------------+  +-------------+  |
|  | Watch List   |  | Shipping     |  | Notifier    |  |
|  | Manager      |  | Estimator    |  |             |  |
|  |              |  |              |  | - macOS     |  |
|  | - SQLite DB  |  | - EU rules   |  |   native    |  |
|  | - Seen items |  | - Cost calc  |  |             |  |
|  | - Cron jobs  |  | - 15562 dest |  |             |  |
|  +-------------+  +--------------+  +-------------+  |
+------------------------------------------------------+
```

## Data Model

### Listing

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique ID (source + listing ID, e.g., `ebay_12345`) |
| `source` | string | Which marketplace |
| `title` | string | Listing title as posted |
| `description` | string | Full listing description |
| `part_price` | decimal | Part price in EUR (converted if needed) |
| `shipping_price` | decimal | Shipping cost to Athens 15562 (estimated if not stated) |
| `total_price` | decimal | part_price + shipping_price |
| `shipping_ratio_flag` | boolean | True if shipping > 50% of part price |
| `currency_original` | string | Original listing currency |
| `seller_country` | string | ISO country code |
| `is_eu` | boolean | Whether seller is in EU (no customs) |
| `condition_raw` | string | Seller's stated condition |
| `condition_score` | enum | green / yellow / red |
| `condition_notes` | string | AI reasoning for the score |
| `photos` | list[string] | URLs to listing photos |
| `listing_url` | string | Direct link to the listing |
| `compatible_models` | list[string] | Which Ducati models this fits |
| `compatibility_confidence` | enum | definite / likely / verify |
| `oem_part_number` | string | If identified |
| `date_listed` | datetime | When the listing was posted |
| `date_found` | datetime | When our system found it |

### Watch

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Auto-increment |
| `query` | string | What to search for |
| `part_category` | string | Optional category filter |
| `oem_number` | string | Optional OEM number |
| `max_total_price` | decimal | Budget cap (part + shipping) |
| `target_models` | list[string] | Which bike models to search |
| `sources` | list[string] | Which marketplaces to check (or "all") |
| `active` | boolean | Whether this watch is running |
| `created_at` | datetime | When the watch was created |
| `last_checked` | datetime | Last cron run |

### SeenListing

| Field | Type | Description |
|-------|------|-------------|
| `listing_id` | string | Same as Listing.id |
| `watch_id` | integer | Which watch found it |
| `first_seen` | datetime | When first discovered |
| `notified` | boolean | Whether notification was sent |

### PartsCatalog

| Field | Type | Description |
|-------|------|-------------|
| `oem_number` | string | Ducati OEM part number |
| `part_name` | string | Human-readable name |
| `category` | string | Part category |
| `compatible_models` | list[string] | Which models it fits |
| `enduro_specific` | boolean | True if Enduro-only part |
| `search_aliases` | list[string] | Alternative names / terms across languages |

## Source Adapters

Each adapter implements a common interface:

```
search(query: str, filters: SearchFilters) -> list[RawListing]
estimate_shipping(seller_location: str) -> decimal
get_listing_details(listing_url: str) -> RawListing
```

### eBay (API-based)

- **API:** eBay Browse API (OAuth client credentials)
- **Markets:** ebay.it, ebay.de, ebay.fr, ebay.es, ebay.co.uk, ebay.com
- **Shipping:** API returns shipping cost to destination postal code directly
- **Rate limits:** 5,000 calls/day on free tier

### Browser-automated adapters (Playwright)

All non-API sources use headless Chrome via Playwright. Each adapter navigates the platform in its native language.

| Adapter | Platform | Language | Country | Currency |
|---------|----------|----------|---------|----------|
| `olx.py` | OLX.bg, OLX.ro, OLX.pl | BG/RO/PL | BG, RO, PL | BGN, RON, PLN |
| `subito.py` | Subito.it | IT | IT | EUR |
| `kleinanzeigen.py` | Kleinanzeigen.de | DE | DE | EUR |
| `leboncoin.py` | Leboncoin.fr | FR | FR | EUR |
| `wallapop.py` | Wallapop.es | ES | ES | EUR |
| `facebook.py` | Facebook Marketplace + Groups | Multi | Multi | Multi |
| `allegro.py` | Allegro.pl | PL | PL | PLN |
| `jofogas.py` | Jofogas.hu | HU | HU | HUF |
| `bazos.py` | Bazos.cz, Bazos.sk | CZ/SK | CZ, SK | CZK, EUR |
| `njuskalo.py` | Njuskalo.hr | HR | HR | EUR |
| `bolha.py` | Bolha.com | SL | SI | EUR |
| `moto_breakers.py` | Specialized moto dismantler sites | EN/IT | Various | Various |

### Multi-language query expansion

When the user types "clutch lever", the skill generates search terms in all supported languages:

- English: "clutch lever multistrada 1260"
- Italian: "leva frizione multistrada 1260"
- German: "Kupplungshebel multistrada 1260"
- French: "levier embrayage multistrada 1260"
- Spanish: "maneta embrague multistrada 1260"
- Bulgarian: "съединител лост Мултистрада 1260"
- Romanian: "maneta ambreiaj Multistrada 1260"
- Hungarian: "kuplung kar Multistrada 1260"
- Polish: "dzwignia sprzegla Multistrada 1260"
- Czech: "paka spojky Multistrada 1260"
- Croatian: "rucica kvacila Multistrada 1260"

Each adapter receives the query in its platform's language. Claude handles translation as part of the skill layer.

### Search priority tiers

**Tier 1 -- Always search (cheapest + closest to Greece):**

| Platform | Country | Rationale |
|----------|---------|-----------|
| OLX.bg, Bazar.bg | Bulgaria | Neighbor, BGN prices, 5-10 EUR shipping |
| OLX.ro, Autovit.ro | Romania | Very close, RON prices, 6-12 EUR shipping |
| Jofogas.hu, Hardverapro.hu | Hungary | HUF prices, reasonable shipping |
| OLX.pl, Allegro.pl | Poland | PLN prices, large moto community |
| Bazos.cz | Czech Republic | CZK prices |
| Njuskalo.hr | Croatia | Neighbor, EUR but Balkan pricing |
| Bolha.com | Slovenia | Close, EUR but cheaper market |
| Bazos.sk | Slovakia | EUR but Eastern EU pricing |
| Facebook groups | All above | Catches private sellers in these regions |

**Tier 2 -- Search by default (moderate prices, high volume):**

| Platform | Country | Rationale |
|----------|---------|-----------|
| Subito.it | Italy | Close to Greece, huge Ducati market |
| eBay (.it, .de, .fr, .es) | EU-wide | Largest volume, good search API |
| Specialized moto breakers | Various | Good condition data, OEM numbers |

**Tier 3 -- Opt-in only (expensive markets):**

| Platform | Country | Rationale |
|----------|---------|-----------|
| Kleinanzeigen.de | Germany | High prices |
| Leboncoin.fr | France | Higher pricing |
| Wallapop.es | Spain | Moderate-high + far from Greece |
| UK sites | UK | Expensive + post-Brexit customs/VAT |

Default search runs Tier 1 + Tier 2. User can override per search.

## Condition Assessment Pipeline

### Stage 1: Hard exclusion (automated keyword filter)

Blocklist applied to title + description across all supported languages. Keywords: broken, cracked, for parts, damaged, bent, rusted, scrap (and translations). Any match = auto-excluded.

### Stage 2: Condition label normalization

Map platform-specific condition labels to common scale: excellent, good, fair, unknown. Labels indicating "for parts/repair" feed back to Stage 1 exclusion.

### Stage 3: AI condition scoring (Claude)

For listings passing Stage 1, Claude reads the listing title, description, and photos to assign:

| Score | Meaning | Criteria |
|-------|---------|----------|
| Green | Likely good condition | Positive description, clear photos showing clean part, seller states good/excellent |
| Yellow | Unclear, manual review | Vague description, no photos, mixed signals, condition not stated |
| Red | Risky but not excluded | Mentions wear/scratches but functional, photos show cosmetic damage |

Listings with zero photos always score yellow with note "No photos -- ask seller for images."

### Stage 4: Results grouping

HTML report groups by condition score: green first (sorted by total price), then yellow, then red. Each listing shows Claude's reasoning.

## Cost Filtering

**Primary filter:** Total cost cap (part_price + shipping_price). Set per search or per watch.

**Soft warning:** When shipping_price > 50% of part_price, the listing is flagged with a shipping ratio warning. Not excluded, but visually marked in results.

**Currency conversion:** All non-EUR prices converted via ECB reference rates (free API, updated daily).

**Shipping estimation:**

- eBay: API provides actual shipping cost to postal code
- Other platforms: Country-based estimate ranges

| Seller country | Estimated shipping to Athens 15562 |
|----------------|-----------------------------------|
| Bulgaria | 5-10 EUR |
| Romania | 6-12 EUR |
| Croatia | 8-15 EUR |
| Slovenia | 10-16 EUR |
| Hungary | 10-18 EUR |
| Italy | 8-15 EUR |
| Poland | 12-22 EUR |
| Czech Republic | 14-22 EUR |
| Slovakia | 12-20 EUR |
| Germany | 10-20 EUR |
| France | 12-22 EUR |
| Spain | 12-25 EUR |
| UK | 15-30 EUR + customs/VAT |

**EU rule:** All EU countries = no customs charges. Non-EU (UK, potentially others) get flagged with customs/VAT warning added to total cost estimate.

## Results Presentation

### Terminal summary

Quick overview printed in Claude Code session:
- Total listings found, how many are new
- Top 3 results with source, total price, condition score
- Path to full HTML report

### HTML report

Rich report opened in browser, containing:
- Thumbnail photos per listing
- Condition score with color coding and AI reasoning
- Price breakdown: part price, shipping (actual or estimated), total
- Shipping ratio warning where applicable
- Seller country and EU status
- Compatibility confidence tag
- Direct clickable link to listing
- Sorted by condition score, then total price ascending
- Filter controls for condition, price range, source, country

Reports saved to `/ducati-parts/reports/YYYY-MM-DD_<query>.html`.

## Watch List & Monitoring

### Watch management (conversational)

- Create: "watch for a clutch lever under 40 EUR"
- List: "show my watches"
- Pause: "pause the exhaust watch"
- Remove: "remove the clutch lever watch"
- Update: "change the radiator guard budget to 80 EUR"

### Cron execution

macOS `launchd` plist runs `watch_runner.py` every 4 hours (configurable). For each active watch:

1. Run search across configured source tiers
2. Deduplicate against SeenListing table
3. For new listings: save to DB, generate mini HTML report, fire macOS notification

### macOS notification

Via `osascript`, showing:
- Number of new listings
- Best deal (lowest total price)
- Click to open HTML report in default browser

### Lifecycle

- `launchd` plist auto-installed when first watch is created
- Auto-removed when all watches are deactivated
- Stale listings (>30 days) marked as stale, not re-notified

## Part Compatibility

### Default bike

Ducati Multistrada 1260 Enduro (2019-2021). Hardcoded as default, switchable via conversation ("switch bike to Monster 821").

### Enduro-specific parts (NOT shared with standard 1260)

- Exhaust system (Akrapovic slip-on, OEM headers)
- Skid plate / engine guard
- Center stand
- Rally seat
- Spoked wheels
- Crash bars / frame protectors
- Windscreen (taller Enduro version)
- Suspension (longer travel, Sachs vs Marzocchi)

### Shared with Multistrada 1260 (all variants)

- Clutch/brake levers
- Brake pads and discs
- Mirrors
- Chain and sprockets
- Foot pegs
- Handlebars and grips
- Lights and indicators
- ECU / electronics
- Radiator and cooling

### Compatibility resolution

1. OEM part number cross-reference (definite match when available)
2. Broad search with compatibility tagging (definite / likely / verify)
3. Catalog grows as user confirms compatibility through use

## Skill Interface

### Invocation

Project-local Claude Code skill at `.claude/skills/ducati-parts/SKILL.md`. Activates when working in the `/ducati-parts/` directory.

### Interaction patterns

- **On-demand search:** "find me a clutch lever" -- runs search, returns terminal summary + HTML report
- **Conversational refinement:** "also check germany" / "show me only green under 20 EUR" / "does the 1200 version fit?"
- **Watch management:** "watch for an Akrapovic exhaust, budget 400" / "show my watches" / "pause the exhaust watch"
- **Bike switching:** "switch bike to Monster 821" -- changes target model, keeps existing watches on original bike
- **Compatibility queries:** "does the 1200 windscreen fit the 1260 enduro?"

## Project Structure

```
/Users/thanos/Work/Repos/ducati-parts/
+-- .claude/
|   +-- skills/
|       +-- ducati-parts/
|           +-- SKILL.md
+-- src/
|   +-- adapters/
|   |   +-- __init__.py
|   |   +-- base.py
|   |   +-- ebay.py
|   |   +-- olx.py
|   |   +-- subito.py
|   |   +-- kleinanzeigen.py
|   |   +-- leboncoin.py
|   |   +-- wallapop.py
|   |   +-- facebook.py
|   |   +-- allegro.py
|   |   +-- jofogas.py
|   |   +-- bazos.py
|   |   +-- njuskalo.py
|   |   +-- bolha.py
|   |   +-- moto_breakers.py
|   +-- catalog/
|   |   +-- __init__.py
|   |   +-- models.py
|   |   +-- compatibility.py
|   |   +-- seed_data.py
|   +-- core/
|   |   +-- __init__.py
|   |   +-- search.py
|   |   +-- condition.py
|   |   +-- shipping.py
|   |   +-- currency.py
|   |   +-- dedup.py
|   +-- watch/
|   |   +-- __init__.py
|   |   +-- manager.py
|   |   +-- runner.py
|   |   +-- notifier.py
|   +-- reports/
|   |   +-- __init__.py
|   |   +-- html_report.py
|   |   +-- terminal_report.py
|   |   +-- templates/
|   |       +-- report.html
|   +-- db/
|       +-- __init__.py
|       +-- database.py
|       +-- migrations/
+-- data/
|   +-- ducati_parts.db               # gitignored
|   +-- seed/
|       +-- multistrada_1260_enduro.json
+-- reports/                          # gitignored
+-- config/
|   +-- config.yaml
|   +-- launchd/
|       +-- com.ducati-parts.watcher.plist
+-- .env                              # gitignored
+-- .gitignore
+-- pyproject.toml
+-- docs/
|   +-- design/
|       +-- project-design.md
+-- Issues - Pending Items.md
```

## Configuration

### config.yaml

```yaml
bike:
  default_model: "Multistrada 1260 Enduro"
  year_range: [2019, 2021]
  also_compatible:
    - "Multistrada 1260"
    - "Multistrada 1260 S"
    - "Multistrada 1260 Pikes Peak"

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
    - allegro_pl
    - jofogas_hu
    - bazos_cz
    - bazos_sk
    - njuskalo_hr
    - bolha_si
    - facebook_eastern_eu
  2:
    - subito_it
    - ebay_eu
    - moto_breakers
  3:
    - kleinanzeigen_de
    - leboncoin_fr
    - wallapop_es
    - facebook_western_eu
    - uk_sites
```

### Environment variables (.env)

```
EBAY_APP_ID=<required>
EBAY_CERT_ID=<required>
```

Missing keys raise exceptions -- no fallback values.

## Dependencies

| Package | Purpose |
|---------|---------|
| `playwright` | Browser automation for non-API sources |
| `httpx` | Async HTTP client for eBay API + ECB rates |
| `beautifulsoup4` | HTML parsing for listing content extraction |
| `jinja2` | HTML report templating |
| `pyyaml` | Config file parsing |
| `python-dotenv` | .env file loading |
| `Pillow` | Photo thumbnail processing for reports |

No ORM. Direct SQLite via Python's built-in `sqlite3` module.

## Known Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Facebook blocks automation | Largest private seller pool lost | Build adapter last, accept periodic breakage. Email notifications from groups as manual fallback |
| Platform layout changes | Adapter stops returning results | Each adapter has health check. Cron logs failures. Skill reports broken adapters |
| Shipping estimates approximate | Total cost could be off | Mark estimated vs actual clearly. Use ranges not false precision |
| Photo analysis misses damage | Bad condition score | Always advisory, never auto-buy. Yellow default when uncertain |
| OEM database incomplete | Missed compatibility | Broad search catches what OEM lookup misses. Catalog grows over time |
| Rate limiting on platforms | Searches slow or fail | Respectful delays. Tier system limits scope per search |
| eBay API registration | Setup friction | One-time setup with clear instructions. Free tier sufficient |
