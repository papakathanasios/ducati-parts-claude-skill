# Adapter Diagnostics and Selector Fix

**Date:** 2026-04-15
**Status:** Approved
**Addresses Issues:** CSS selector validation (#1), JS-heavy specialist adapters (#6), Specialist adapter selector validation (#7)

## Problem

~35 Playwright-based adapters use hand-guessed CSS selectors that may not match actual site markup. The current smoke test (`smoke_test_live.py`) reports OK/EMPTY/ERROR but provides no diagnostic information to determine *why* an adapter fails. Fixing broken selectors requires manually loading each site in a browser and inspecting the DOM — slow and error-prone.

Additionally, adapters labeled "JS-heavy" (BMotor, MaleDucati) were assumed to need longer timeouts, but manual testing confirmed results load instantly. The real issue is incorrect selectors and interaction patterns, not timing.

## Solution

Three-phase approach:

1. **Enhanced smoke test** — add diagnostic capture (screenshots + DOM snapshots) and HTML reporting to the existing smoke test
2. **Selector tester tool** — standalone tool for interactive CSS selector development and testing against live sites
3. **Selector fix pass** — use the diagnostic tools to inspect real markup and fix every broken adapter

## Phase 1: Enhanced Smoke Test

### File: `test_scripts/smoke_test_live.py` (extend existing)

### New CLI Flags

| Flag | Description |
|------|-------------|
| `--diagnose` | Force screenshot + DOM capture for all adapters (not just failing) |
| `--report` | Generate HTML diagnostic report (default: `diagnostics/report.html`) |
| `--query "text"` | Override the default "Ducati Multistrada" search term |

### Diagnostic Capture

Triggered automatically on EMPTY/ERROR results, or for all adapters when `--diagnose` is used:

- **Screenshot:** `diagnostics/screenshots/<adapter_name>.png`
- **DOM snapshot:** `diagnostics/dom/<adapter_name>.html`
- Each run creates a timestamped subfolder: `diagnostics/2026-04-15_143000/screenshots/`, `diagnostics/2026-04-15_143000/dom/`

### PlaywrightBaseAdapter Changes

Add a `search_with_diagnostics()` method that wraps `search()` but keeps the page open long enough to capture screenshot + DOM before closing. This avoids changing the core `search()` contract.

```python
async def search_with_diagnostics(
    self, query: str, filters: SearchFilters, capture_dir: Path
) -> tuple[list[RawListing], Path | None, Path | None]:
    """Run search and optionally capture screenshot + DOM snapshot."""
    # ... same flow as search() but captures before page.close()
```

### HTML Diagnostic Report

Single-page Jinja2 report showing:

- Table of all adapters: name, status (OK/EMPTY/ERROR/TIMEOUT), result count, elapsed time
- For failing adapters: inline screenshot thumbnail + link to full DOM dump
- Generated via Jinja2 (already a project dependency from `html_report.py`)

## Phase 2: Selector Tester Tool

### File: `test_scripts/selector_tester.py` (new)

### Purpose

Fast feedback loop for developing and fixing CSS selectors against live sites.

### Usage

```bash
# Direct mode: test a selector against a URL
uv run python test_scripts/selector_tester.py --url https://www.bmotor.hu --selector ".product-item"

# Adapter mode: run full adapter flow, then test its selectors
uv run python test_scripts/selector_tester.py --adapter bmotor --query "Multistrada"
```

### Two Modes

1. **Direct mode** (`--url` + `--selector`): Load a URL, test a CSS selector, show match count and element previews
2. **Adapter mode** (`--adapter` + `--query`): Run the adapter's full search flow (including AJAX interaction), then test its selectors against the resulting page

### Output

- Match count for each selector the adapter uses
- First 5 matched elements: tag, classes, truncated inner text
- Screenshot saved to `diagnostics/screenshots/<name>_selector_test.png`
- If zero matches: suggest alternative selectors by scanning the DOM for common product-card patterns (elements containing price-like text + links)

### Adapter Selector Introspection

Add an optional `_get_selectors()` method to adapters that returns the CSS selectors they use. Adapters that don't implement it skip the per-selector breakdown and just report overall result count.

```python
# In PlaywrightBaseAdapter (optional override)
def _get_selectors(self) -> dict[str, list[str]]:
    """Return CSS selectors used by this adapter, keyed by purpose."""
    return {}

# Example override in BMotorAdapter
def _get_selectors(self) -> dict[str, list[str]]:
    return {
        "search_input": [
            "input.disableAutocomplete[type='text']",
            "input[placeholder*='keres']",
            "#search input[type='text']",
        ],
        "product_cards": [
            "#results a[href]",
            ".search-results a[href]",
            ".product-item",
            ".product-card",
        ],
        "title": [
            "a[href*='/ducati']",
            "a[href*='/product']",
            "h2 a", "h3 a",
        ],
        "price": [
            "[class*='price']",
            ".price",
            ".product-price",
        ],
    }
```

## Phase 3: Selector Fix Pass

### Process

1. Run `uv run python test_scripts/smoke_test_live.py --diagnose --report`
2. Review `diagnostics/report.html` — identify all EMPTY/ERROR adapters
3. For each broken adapter, run `selector_tester.py --adapter <name>` to inspect the live DOM
4. Update CSS selectors in `_extract_listings()` and `_parse_card()` to match actual markup
5. For AJAX adapters (BMotor, MaleDucati), also fix search interaction selectors (input field, submit button)
6. Re-run smoke test to confirm fixes

### Scope of Selector Fixes

- Product card container selectors
- Title/link selectors
- Price selectors
- Image selectors
- Search input/button selectors (AJAX adapters only)

### Out of Scope

- Adapter architecture changes (`PlaywrightBaseAdapter`, `search()` contract, `RawListing` structure)
- Core search flow (goto, wait, dismiss cookies, extract)
- Timeout values (sites confirmed to load instantly)
- Adding new adapters

### Deliverables

- All adapters returning results on the smoke test, or confirmed to genuinely have no matching parts
- Updated `Issues - Pending Items.md` — items 1, 6, 7 marked completed

## File Changes Summary

| File | Change |
|------|--------|
| `test_scripts/smoke_test_live.py` | Add `--diagnose`, `--report`, `--query` flags; diagnostic capture logic; HTML report generation |
| `src/adapters/playwright_base.py` | Add `search_with_diagnostics()` method; add optional `_get_selectors()` |
| `test_scripts/selector_tester.py` | New file — selector testing tool |
| `test_scripts/templates/diagnostic_report.html` | New file — Jinja2 template for diagnostic report |
| `src/adapters/*.py` | Selector fixes per adapter (Phase 3) |
| `Issues - Pending Items.md` | Mark resolved items as completed |
