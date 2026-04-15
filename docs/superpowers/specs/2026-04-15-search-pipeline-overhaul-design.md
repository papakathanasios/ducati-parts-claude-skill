# Search Pipeline Overhaul -- Design Specification

**Date:** 2026-04-15
**Status:** Approved
**Scope:** Fix search pipeline data flow, improve performance/reliability, expand coverage

## Problem Statement

The ducati-parts search pipeline has several systemic issues that prevent it from returning useful results:

1. Currency conversion exists (`CurrencyConverter`) but is never called -- price filtering in EUR is meaningless for non-EUR adapters (BGN, PLN, HUF, CZK, RON)
2. No query translation -- all 13 adapters receive raw English queries, missing listings in Bulgarian, Hungarian, Polish, etc.
3. Relevance filter drops valid results -- `_is_relevant()` checks English query words against local-language listing text
4. Adapters execute sequentially -- 13 adapters at ~4s each = ~50s per search instead of ~5s
5. No per-adapter timeout -- one hanging adapter blocks the entire search
6. No currency rate caching -- ECB API called on every search
7. Browser processes accumulate -- Playwright instances never cleaned up
8. OEM catalog has only ~17 parts
9. CSS selectors unvalidated against live sites
10. No server-side price hints to reduce noise from high-volume sources

## Approach

Pipeline-First (Approach 1): Fix data flow end-to-end first so existing adapters produce useful results, then address performance and coverage. Each fix is independently testable.

## Section 1: Search Pipeline Data Flow

### 1a. Currency Conversion Integration

**File:** `src/core/search.py`

Wire `CurrencyConverter` into `SearchOrchestrator`:

- Add `self.currency_converter = CurrencyConverter()` in `__init__()`
- Call `await self.currency_converter.fetch_rates()` once at the start of `run()`, before dispatching adapters
- After receiving `RawListing` results, convert `raw.price` from `raw.currency` to EUR via `converter.convert()`
- The `part_price` field on `Listing` becomes EUR-normalized
- Shipping estimates from `ShippingEstimator` are already in EUR
- `total_price` (part + shipping) is now comparable across all adapters
- `max_total_price` filter becomes meaningful for non-EUR listings

**Error handling:** If ECB fetch fails, log a warning and set a `_rates_available` flag to False. When processing listings, if rates are unavailable, keep `part_price` in the original currency and set `currency_original` to indicate unconverted prices. The `max_total_price` filter is skipped for unconverted listings (they pass through unfiltered) so the user sees them rather than getting no results. The terminal and HTML reports already show `currency_original`, making unconverted prices visible.

### 1b. Query Translation Engine

**New file:** `src/core/query_expansion.py`

A static dictionary mapping common motorcycle part terms to 11 languages:

```
Languages: en, bg, ro, hu, pl, cz, sk, hr, sl, it, de, fr, es
```

**Dictionary structure:**
```python
TERM_TRANSLATIONS: dict[str, dict[str, str]] = {
    "exhaust": {"bg": "ауспух", "it": "scarico", "de": "Auspuff", ...},
    "clutch": {"bg": "съединител", "it": "frizione", "de": "Kupplung", ...},
    ...
}
```

**Function:** `expand_query(query: str, target_language: str, overrides: dict[str, str] | None = None) -> str`

1. Tokenize the query into words
2. For each word, check if it exists in `TERM_TRANSLATIONS`
3. If yes, replace with the `target_language` translation
4. Keep model names untranslated ("Multistrada", "1260", "Ducati", "Enduro") -- sellers use original model names universally
5. If `overrides` dict is provided (from Claude skill layer during interactive use), those translations take precedence over the static dictionary
6. Return the translated query string

**Integration with orchestrator:** In `SearchOrchestrator.run()`, before dispatching to each adapter, call `expand_query(filters.query, adapter.language)`. Each adapter receives a query in its platform's language.

**Initial vocabulary:** ~30-40 common motorcycle part terms covering:
- Drivetrain: exhaust, clutch, chain, sprocket, gearbox
- Brakes: brake, lever, disc, pad, caliper
- Body: fairing, windscreen, seat, mirror, tank
- Suspension: fork, shock, spring, linkage
- Electrical: light, indicator, ECU, instrument, battery
- Cooling: radiator, hose, fan, thermostat
- Consumables: filter, spark plug, gasket

**Watch/cron compatibility:** The static dictionary works without Claude in the loop. Watch runs via `watch_runner.py` get translations automatically.

**Skill layer enhancement:** `SearchFilters` gains an optional `translations: dict[str, str] | None` field. When the skill invokes `run_search()` interactively, Claude can pass per-language translations that override the static dictionary for unusual parts.

### 1c. Relevance Filter Fix

**File:** `src/core/search.py`, function `_is_relevant()`

**Current behavior:** Checks if English query words appear in listing title/description. Drops listings in other languages even when the adapter correctly found them.

**New behavior:**

- Accept both the original query and the translated query as parameters
- A listing is relevant if it matches significant words (>= 3 chars) from EITHER the original OR translated query
- Model identifiers ("Ducati", "Multistrada", "1260") are always checked regardless of language, since sellers universally use original model names
- Signature becomes: `_is_relevant(title: str, description: str, original_query: str, translated_query: str) -> bool`

## Section 2: Performance & Reliability

### 2a. Parallel Adapter Execution

**File:** `src/core/search.py`, `SearchOrchestrator.run()`

**Current:** Lines 55-60 await each adapter coroutine sequentially in a for loop.

**Fix:** Replace with `asyncio.gather()`:

```python
coros = [adapter.search(query, filters) for name, adapter in selected_adapters]
results = await asyncio.gather(*coros, return_exceptions=True)
```

For each result:
- If it's a `list[RawListing]`, extend `raw_results`
- If it's an `Exception`, record in `self.last_errors`

This reduces search time from ~50s (13 x ~4s) to ~5s (slowest single adapter).

### 2b. Per-Adapter Timeout

**File:** `src/core/search.py`

Wrap each adapter call in `asyncio.wait_for()`:

```python
timeout = self.config.search.adapter_timeout_seconds  # default: 30
```

If an adapter exceeds the timeout, it's recorded as a timeout error in `self.last_errors` and the remaining results are unaffected.

**Config:** New field `adapter_timeout_seconds: int` in `SearchConfig` within `config.yaml`, default 30.

### 2c. Currency Rate Caching

**File:** `src/core/currency.py`

Add `_rates_fetched_at: datetime | None` to `CurrencyConverter`. In `fetch_rates()`:

- If `_rates_fetched_at` is not None and less than 24 hours ago, return immediately (use cached rates)
- Otherwise, fetch from ECB and update `_rates_fetched_at`

ECB updates rates once daily around 16:00 CET, so 24h cache is safe. In-memory only -- no file/DB cache needed. The converter instance lives for the duration of a search session.

### 2d. Adapter Cleanup

**File:** `src/cli.py`

After `orchestrator.run()` completes, clean up Playwright resources:

```python
try:
    listings = await orchestrator.run(filters)
finally:
    for adapter in adapters.values():
        if hasattr(adapter, 'close'):
            await adapter.close()
```

This ensures browser processes are terminated even if the search errors out.

## Section 3: Coverage & Data Quality

### 3a. OEM Catalog Expansion

**File:** `data/seed_parts.json`

Expand from ~17 parts to ~40 parts. Each entry includes:
- `oem_number`: Ducati OEM part number (where known, empty string if unknown)
- `part_name`: Human-readable name
- `category`: Part category (drivetrain, brakes, body, etc.)
- `compatible_models`: List of Ducati models it fits
- `enduro_specific`: Boolean flag
- `search_aliases`: Multi-language terms that feed into the query expansion dictionary

**New parts to add:**

Enduro-specific:
- Exhaust headers, slip-on muffler
- Skid plate / engine guard
- Center stand
- Rally seat
- Spoked wheel set (front/rear)
- Crash bars / frame protectors
- Tall windscreen (Enduro version)
- Sachs suspension (fork/shock)

Shared with Multistrada 1260:
- Brake pads (front/rear), brake discs, brake calipers
- Mirrors (left/right)
- Chain and sprocket kit
- Foot pegs
- Handlebars, grips
- Radiator, coolant hoses
- Headlight, tail light, indicators
- Instrument cluster
- Fuel pump, throttle body
- ECU

Consumables:
- Air filter, oil filter
- Spark plugs
- Clutch plates / friction discs

### 3b. Live Smoke Test Script

**New file:** `test_scripts/smoke_test_live.py`

A manual test script (not CI) that validates adapters against live sites:

1. Instantiates each adapter from the registry
2. Runs a known-good broad query ("Ducati Multistrada") per adapter
3. Checks `len(results) > 0`
4. Outputs a results table:

```
Adapter          Status   Results   Time
─────────────────────────────────────────
olx_bg           OK       12        3.2s
olx_ro           EMPTY    0         4.1s
subito_it        OK       8         2.8s
...
```

5. For EMPTY/ERROR adapters, reports which step failed (page load, selector match, parsing)

Run manually to detect selector rot. Not automated in CI since it depends on live third-party sites.

### 3c. Price Hint Pass-Through

**File:** `src/core/types.py` (SearchFilters), adapter implementations

Add `max_price_hint: Decimal | None` to `SearchFilters`. The orchestrator populates it from `max_total_price` minus estimated average shipping for the adapter's country.

Adapters that support server-side price filtering use the hint:
- **eBay:** `price` filter parameter in Browse API
- **OLX variants:** URL price range parameters (e.g., `search[filter_float_price:to]=500`)
- **Subito:** URL price parameter
- **Others:** Ignore the hint (no server-side filtering support)

This is a best-effort optimization. The orchestrator still applies `max_total_price` filtering at the end -- the hint just reduces the volume of irrelevant results fetched.

## Files Changed

| File | Change Type |
|------|-------------|
| `src/core/search.py` | Modified -- currency conversion, parallel execution, timeout, relevance filter, query expansion |
| `src/core/currency.py` | Modified -- rate caching |
| `src/core/query_expansion.py` | New -- translation dictionary and expand_query() |
| `src/core/types.py` | Modified -- SearchFilters gains translations and max_price_hint fields |
| `src/core/config.py` | Modified -- SearchConfig gains adapter_timeout_seconds |
| `src/cli.py` | Modified -- adapter cleanup |
| `config/config.yaml` | Modified -- adapter_timeout_seconds default |
| `data/seed_parts.json` | Modified -- expanded catalog |
| `test_scripts/smoke_test_live.py` | New -- live adapter validation |

## Testing Strategy

- **Unit tests:** query_expansion (term replacement, model name preservation, override behavior), currency caching (time-based expiry), relevance filter (bilingual matching)
- **Integration tests:** SearchOrchestrator with mock adapters returning non-EUR prices, parallel execution with mixed success/failure adapters
- **Smoke tests:** `smoke_test_live.py` against real sites (manual, periodic)

## Out of Scope

- AI-powered condition scoring (Stage 3 in the design spec) -- requires Claude API integration, separate effort
- Facebook adapter repair -- explicitly disabled, known fragility
- MotoBreakers adapter -- explicitly disabled, needs separate research
- eBay credential setup -- blocked on account review
- Watch system changes -- works correctly, just needs the pipeline fixes to flow through
