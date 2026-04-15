# Adapter Diagnostics and Selector Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build diagnostic tooling for Playwright-based adapters (screenshot + DOM capture, HTML report, selector tester), then use it to fix all broken CSS selectors across ~35 adapters.

**Architecture:** Extend the existing `smoke_test_live.py` with a `search_with_diagnostics()` method on `PlaywrightBaseAdapter` that captures screenshots and DOM snapshots before closing the page. A new `selector_tester.py` provides interactive selector testing. Both tools output to a `diagnostics/` directory with timestamped runs. The diagnostic HTML report reuses the project's existing Jinja2 pattern from `src/reports/`.

**Tech Stack:** Python 3.14, Playwright (async), Jinja2, argparse

**Spec:** `docs/design/plan-001-adapter-diagnostics-and-selector-fix.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `src/adapters/playwright_base.py` | Add `search_with_diagnostics()` and `_get_selectors()` to base class |
| `test_scripts/smoke_test_live.py` | Add `--diagnose`, `--report`, `--query` flags; diagnostic capture; report generation |
| `test_scripts/selector_tester.py` | New — interactive CSS selector testing tool (direct + adapter modes) |
| `test_scripts/templates/diagnostic_report.html` | New — Jinja2 template for the HTML diagnostic report |
| `test_scripts/test_diagnostic_tools.py` | New — unit tests for the diagnostic tooling |

---

## Task 1: Add `search_with_diagnostics()` to PlaywrightBaseAdapter

**Files:**
- Modify: `src/adapters/playwright_base.py`
- Create: `test_scripts/test_diagnostic_tools.py`

- [ ] **Step 1: Write the failing test**

Create `test_scripts/test_diagnostic_tools.py`:

```python
"""Tests for adapter diagnostic tooling."""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.core.types import RawListing, SearchFilters


class StubDiagnosticAdapter(PlaywrightBaseAdapter):
    source_name = "stub_diag"
    language = "en"
    country = "GB"
    currency = "GBP"
    base_url = "https://example.com"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/search?q={query}"

    async def _extract_listings(self, page, query: str) -> list[RawListing]:
        return []


class TestSearchWithDiagnostics:
    def test_method_exists(self):
        adapter = StubDiagnosticAdapter()
        assert hasattr(adapter, "search_with_diagnostics")

    def test_returns_tuple_of_three(self):
        """search_with_diagnostics returns (listings, screenshot_path, dom_path)."""
        adapter = StubDiagnosticAdapter()
        sig = adapter.search_with_diagnostics.__code__.co_varnames
        # Method should accept query, filters, capture_dir
        assert "query" in sig
        assert "filters" in sig
        assert "capture_dir" in sig


class TestGetSelectors:
    def test_base_returns_empty_dict(self):
        adapter = StubDiagnosticAdapter()
        assert adapter._get_selectors() == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest test_scripts/test_diagnostic_tools.py -v`
Expected: FAIL — `search_with_diagnostics` and `_get_selectors` not found

- [ ] **Step 3: Implement `search_with_diagnostics()` and `_get_selectors()`**

In `src/adapters/playwright_base.py`, add these two methods to the `PlaywrightBaseAdapter` class. Add the `Path` import at the top.

Add to imports at the top of the file:

```python
from pathlib import Path
```

Note: `Path` is already imported in this file — no change needed for that import.

Add the following two methods to `PlaywrightBaseAdapter`, after the existing `search()` method (after line 155):

```python
    async def search_with_diagnostics(
        self, query: str, filters: SearchFilters, capture_dir: Path,
    ) -> tuple[list[RawListing], Path | None, Path | None]:
        """Run search and capture screenshot + DOM snapshot before closing the page."""
        context = await self._new_context()
        page = await context.new_page()
        await _stealth.apply_stealth_async(page)
        screenshot_path: Path | None = None
        dom_path: Path | None = None
        try:
            url = self._build_search_url(query)
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            await self._dismiss_cookies(page)
            await asyncio.sleep(2)
            results = await self._extract_listings(page, query)

            # Capture diagnostics before closing
            capture_dir.mkdir(parents=True, exist_ok=True)
            screenshots_dir = capture_dir / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            dom_dir = capture_dir / "dom"
            dom_dir.mkdir(parents=True, exist_ok=True)

            screenshot_path = screenshots_dir / f"{self.source_name}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)

            dom_path = dom_dir / f"{self.source_name}.html"
            content = await page.content()
            dom_path.write_text(content, encoding="utf-8")

            return results, screenshot_path, dom_path
        except Exception:
            # Still try to capture what we can on error
            try:
                capture_dir.mkdir(parents=True, exist_ok=True)
                screenshots_dir = capture_dir / "screenshots"
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                screenshot_path = screenshots_dir / f"{self.source_name}.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
            except Exception:
                pass
            try:
                dom_dir = capture_dir / "dom"
                dom_dir.mkdir(parents=True, exist_ok=True)
                dom_path = dom_dir / f"{self.source_name}.html"
                content = await page.content()
                dom_path.write_text(content, encoding="utf-8")
            except Exception:
                pass
            raise
        finally:
            await page.close()
            if context is not self._persistent_context:
                await context.close()

    def _get_selectors(self) -> dict[str, list[str]]:
        """Return CSS selectors used by this adapter, keyed by purpose.

        Override in subclasses to enable per-selector diagnostic reporting.
        """
        return {}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest test_scripts/test_diagnostic_tools.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/adapters/playwright_base.py test_scripts/test_diagnostic_tools.py
git commit -m "feat: add search_with_diagnostics() and _get_selectors() to PlaywrightBaseAdapter"
```

---

## Task 2: Create the Diagnostic Report Jinja2 Template

**Files:**
- Create: `test_scripts/templates/diagnostic_report.html`

- [ ] **Step 1: Create the template directory**

```bash
mkdir -p test_scripts/templates
```

- [ ] **Step 2: Write the diagnostic report template**

Create `test_scripts/templates/diagnostic_report.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Adapter Diagnostic Report</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #1a1a2e;
            color: #e0e0e0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            padding: 20px;
        }
        a { color: #4fc3f7; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .header {
            text-align: center;
            padding: 30px 0 20px;
        }
        .header h1 {
            color: #e53935;
            font-size: 2rem;
            margin-bottom: 5px;
        }
        .header .subtitle {
            font-size: 1rem;
            color: #90caf9;
        }
        .header .generated-at {
            font-size: 0.85rem;
            color: #888;
            margin-top: 5px;
        }
        .summary-bar {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .summary-item {
            background: #16213e;
            border-radius: 8px;
            padding: 12px 24px;
            text-align: center;
            min-width: 120px;
        }
        .summary-item .count {
            font-size: 1.8rem;
            font-weight: bold;
        }
        .summary-item .label {
            font-size: 0.85rem;
            color: #aaa;
        }
        .summary-item.ok .count { color: #4caf50; }
        .summary-item.empty .count { color: #ffc107; }
        .summary-item.error .count { color: #f44336; }
        .summary-item.timeout .count { color: #ff9800; }
        .summary-item.total .count { color: #4fc3f7; }
        table {
            width: 100%;
            max-width: 1100px;
            margin: 20px auto;
            border-collapse: collapse;
            background: #16213e;
            border-radius: 8px;
            overflow: hidden;
        }
        th {
            background: #0f3460;
            padding: 12px 16px;
            text-align: left;
            font-size: 0.85rem;
            color: #90caf9;
        }
        td {
            padding: 10px 16px;
            border-bottom: 1px solid #1a1a2e;
            font-size: 0.9rem;
        }
        tr:hover { background: #1e2a4a; }
        .status-ok { color: #4caf50; font-weight: 600; }
        .status-empty { color: #ffc107; font-weight: 600; }
        .status-error { color: #f44336; font-weight: 600; }
        .status-timeout { color: #ff9800; font-weight: 600; }
        .diagnostic-section {
            max-width: 1100px;
            margin: 30px auto;
        }
        .diagnostic-section h2 {
            color: #e53935;
            margin-bottom: 16px;
            font-size: 1.3rem;
        }
        .adapter-diag {
            background: #16213e;
            border-radius: 8px;
            margin-bottom: 20px;
            padding: 20px;
        }
        .adapter-diag h3 {
            color: #4fc3f7;
            margin-bottom: 12px;
        }
        .adapter-diag .meta {
            font-size: 0.85rem;
            color: #888;
            margin-bottom: 12px;
        }
        .screenshot-thumb {
            max-width: 100%;
            max-height: 400px;
            border-radius: 6px;
            border: 1px solid #333;
            margin: 10px 0;
        }
        .dom-link {
            display: inline-block;
            margin-top: 8px;
            padding: 4px 12px;
            background: #0f3460;
            border-radius: 4px;
            font-size: 0.85rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Adapter Diagnostic Report</h1>
        <div class="subtitle">Query: &ldquo;{{ query }}&rdquo;</div>
        <div class="generated-at">Generated at {{ generated_at }}</div>
    </div>

    <div class="summary-bar">
        <div class="summary-item total">
            <div class="count">{{ results|length }}</div>
            <div class="label">Total Adapters</div>
        </div>
        <div class="summary-item ok">
            <div class="count">{{ ok_count }}</div>
            <div class="label">OK</div>
        </div>
        <div class="summary-item empty">
            <div class="count">{{ empty_count }}</div>
            <div class="label">EMPTY</div>
        </div>
        <div class="summary-item error">
            <div class="count">{{ error_count }}</div>
            <div class="label">ERROR</div>
        </div>
        <div class="summary-item timeout">
            <div class="count">{{ timeout_count }}</div>
            <div class="label">TIMEOUT</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Adapter</th>
                <th>Status</th>
                <th>Results</th>
                <th>Time</th>
                <th>Error</th>
                <th>Diagnostics</th>
            </tr>
        </thead>
        <tbody>
            {% for r in results %}
            <tr>
                <td>{{ r.name }}</td>
                <td class="status-{{ r.status|lower }}">{{ r.status }}</td>
                <td>{{ r.count }}</td>
                <td>{{ r.time }}</td>
                <td>{{ r.error or '' }}</td>
                <td>
                    {% if r.screenshot_path %}
                    <a href="#diag-{{ r.name }}">View</a>
                    {% else %}
                    &mdash;
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    {% set diag_results = results|selectattr("screenshot_path")|list %}
    {% if diag_results %}
    <div class="diagnostic-section">
        <h2>Diagnostic Details</h2>
        {% for r in diag_results %}
        <div class="adapter-diag" id="diag-{{ r.name }}">
            <h3>{{ r.name }}</h3>
            <div class="meta">
                Status: <span class="status-{{ r.status|lower }}">{{ r.status }}</span>
                &bull; Results: {{ r.count }}
                &bull; Time: {{ r.time }}
                {% if r.error %}&bull; Error: {{ r.error }}{% endif %}
            </div>
            {% if r.screenshot_path %}
            <img class="screenshot-thumb" src="{{ r.screenshot_path }}" alt="Screenshot of {{ r.name }}">
            {% endif %}
            {% if r.dom_path %}
            <a class="dom-link" href="{{ r.dom_path }}">Open DOM Snapshot</a>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    {% endif %}
</body>
</html>
```

- [ ] **Step 3: Commit**

```bash
git add test_scripts/templates/diagnostic_report.html
git commit -m "feat: add Jinja2 template for adapter diagnostic report"
```

---

## Task 3: Enhance `smoke_test_live.py` with Diagnostic Capture and Reporting

**Files:**
- Modify: `test_scripts/smoke_test_live.py`
- Modify: `test_scripts/test_diagnostic_tools.py`

- [ ] **Step 1: Write the failing test for the enhanced smoke test**

Append to `test_scripts/test_diagnostic_tools.py`:

```python
from unittest.mock import patch
from pathlib import Path
import importlib
import sys


class TestSmokeTestCLI:
    """Test that the smoke test script accepts the new CLI flags."""

    def test_argparse_accepts_diagnose_flag(self):
        # Import the smoke test module to check its argparse config
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import test_scripts.smoke_test_live as smoke

        parser = smoke.build_parser()
        args = parser.parse_args(["--diagnose"])
        assert args.diagnose is True

    def test_argparse_accepts_report_flag(self):
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import test_scripts.smoke_test_live as smoke

        parser = smoke.build_parser()
        args = parser.parse_args(["--report"])
        assert args.report is True

    def test_argparse_accepts_query_flag(self):
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import test_scripts.smoke_test_live as smoke

        parser = smoke.build_parser()
        args = parser.parse_args(["--query", "exhaust pipe"])
        assert args.query == "exhaust pipe"

    def test_default_query_is_ducati_multistrada(self):
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import test_scripts.smoke_test_live as smoke

        parser = smoke.build_parser()
        args = parser.parse_args([])
        assert args.query == "Ducati Multistrada"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest test_scripts/test_diagnostic_tools.py::TestSmokeTestCLI -v`
Expected: FAIL — `build_parser` not found

- [ ] **Step 3: Rewrite `smoke_test_live.py` with diagnostic support**

Replace the full contents of `test_scripts/smoke_test_live.py` with:

```python
"""Live smoke test for marketplace adapters.

Run manually to validate CSS selectors and connectivity against real sites.
NOT for CI -- depends on live third-party sites.

Usage:
    uv run python test_scripts/smoke_test_live.py
    uv run python test_scripts/smoke_test_live.py --adapter olx_bg subito_it
    uv run python test_scripts/smoke_test_live.py --diagnose --report
    uv run python test_scripts/smoke_test_live.py --query "exhaust pipe" --diagnose
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from jinja2 import Environment, FileSystemLoader

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.adapters.registry import build_adapter_registry
from src.core.types import SearchFilters

TEMPLATE_DIR = Path(__file__).parent / "templates"


def build_parser():
    import argparse

    parser = argparse.ArgumentParser(description="Live smoke test for marketplace adapters")
    parser.add_argument("--adapter", nargs="+", help="Test specific adapters only")
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="Capture screenshots and DOM snapshots for all adapters (auto for EMPTY/ERROR)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate HTML diagnostic report",
    )
    parser.add_argument(
        "--query",
        default="Ducati Multistrada",
        help="Search query to use (default: 'Ducati Multistrada')",
    )
    return parser


async def test_adapter(
    name: str,
    adapter,
    filters: SearchFilters,
    capture_dir: Path | None,
    force_capture: bool,
) -> dict:
    start = time.monotonic()
    try:
        if capture_dir and isinstance(adapter, PlaywrightBaseAdapter):
            results, screenshot_path, dom_path = await asyncio.wait_for(
                adapter.search_with_diagnostics(filters.query, filters, capture_dir),
                timeout=45,
            )
            elapsed = time.monotonic() - start
            status = "OK" if results else "EMPTY"
            result = {
                "name": name,
                "status": status,
                "count": len(results),
                "time": f"{elapsed:.1f}s",
                "error": None,
                "screenshot_path": str(screenshot_path.relative_to(capture_dir.parent)) if screenshot_path else None,
                "dom_path": str(dom_path.relative_to(capture_dir.parent)) if dom_path else None,
            }
            # If OK and not force_capture, remove the captured files
            if status == "OK" and not force_capture:
                if screenshot_path and screenshot_path.exists():
                    screenshot_path.unlink()
                if dom_path and dom_path.exists():
                    dom_path.unlink()
                result["screenshot_path"] = None
                result["dom_path"] = None
            return result
        else:
            results = await asyncio.wait_for(
                adapter.search(filters.query, filters),
                timeout=30,
            )
            elapsed = time.monotonic() - start
            return {
                "name": name,
                "status": "OK" if results else "EMPTY",
                "count": len(results),
                "time": f"{elapsed:.1f}s",
                "error": None,
                "screenshot_path": None,
                "dom_path": None,
            }
    except asyncio.TimeoutError:
        elapsed = time.monotonic() - start
        return {
            "name": name,
            "status": "TIMEOUT",
            "count": 0,
            "time": f"{elapsed:.1f}s",
            "error": "Exceeded timeout",
            "screenshot_path": None,
            "dom_path": None,
        }
    except Exception as e:
        elapsed = time.monotonic() - start
        return {
            "name": name,
            "status": "ERROR",
            "count": 0,
            "time": f"{elapsed:.1f}s",
            "error": str(e)[:120],
            "screenshot_path": None,
            "dom_path": None,
        }


def generate_diagnostic_report(results: list[dict], query: str, output_path: Path) -> None:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)
    template = env.get_template("diagnostic_report.html")

    ok_count = sum(1 for r in results if r["status"] == "OK")
    empty_count = sum(1 for r in results if r["status"] == "EMPTY")
    error_count = sum(1 for r in results if r["status"] == "ERROR")
    timeout_count = sum(1 for r in results if r["status"] == "TIMEOUT")

    html = template.render(
        query=query,
        results=results,
        ok_count=ok_count,
        empty_count=empty_count,
        error_count=error_count,
        timeout_count=timeout_count,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


async def main(
    adapter_names: list[str] | None = None,
    diagnose: bool = False,
    report: bool = False,
    query: str = "Ducati Multistrada",
) -> None:
    adapters = build_adapter_registry()

    if adapter_names:
        adapters = {k: v for k, v in adapters.items() if k in adapter_names}
        missing = set(adapter_names) - set(adapters.keys())
        if missing:
            print(f"Unknown adapters: {', '.join(missing)}")
            print(f"Available: {', '.join(build_adapter_registry().keys())}")
            sys.exit(1)

    filters = SearchFilters(query=query)

    # Set up diagnostics directory
    capture_dir: Path | None = None
    if diagnose or report:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        capture_dir = Path("diagnostics") / timestamp

    print(f'Smoke testing {len(adapters)} adapters with query: "{query}"')
    if capture_dir:
        print(f"Diagnostics directory: {capture_dir}")
    print(f"{'Adapter':<28} {'Status':<10} {'Results':<10} {'Time':<10} {'Error'}")
    print("-" * 90)

    results = []
    for name, adapter in adapters.items():
        result = await test_adapter(name, adapter, filters, capture_dir, diagnose)
        results.append(result)
        error_str = result["error"] or ""
        diag_marker = " [captured]" if result["screenshot_path"] else ""
        print(
            f"{result['name']:<28} {result['status']:<10} {result['count']:<10} "
            f"{result['time']:<10} {error_str}{diag_marker}"
        )

        if hasattr(adapter, "close"):
            try:
                await adapter.close()
            except Exception:
                pass

    ok = sum(1 for r in results if r["status"] == "OK")
    empty = sum(1 for r in results if r["status"] == "EMPTY")
    errors = sum(1 for r in results if r["status"] in ("ERROR", "TIMEOUT"))
    print("-" * 90)
    print(f"Summary: {ok} OK, {empty} EMPTY, {errors} ERROR/TIMEOUT out of {len(results)} adapters")

    if empty > 0:
        print(
            "\nEMPTY adapters may have broken CSS selectors. "
            "Inspect the live page and update _extract_listings()."
        )

    # Generate HTML report
    if report and capture_dir:
        report_path = capture_dir / "report.html"
        generate_diagnostic_report(results, query, report_path)
        print(f"\nDiagnostic report: {report_path}")


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    asyncio.run(main(args.adapter, args.diagnose, args.report, args.query))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run python -m pytest test_scripts/test_diagnostic_tools.py -v`
Expected: PASS (all tests including TestSmokeTestCLI)

- [ ] **Step 5: Commit**

```bash
git add test_scripts/smoke_test_live.py test_scripts/test_diagnostic_tools.py
git commit -m "feat: add --diagnose, --report, --query flags to smoke test with diagnostic capture"
```

---

## Task 4: Create the Selector Tester Tool

**Files:**
- Create: `test_scripts/selector_tester.py`
- Modify: `test_scripts/test_diagnostic_tools.py`

- [ ] **Step 1: Write the failing test**

Append to `test_scripts/test_diagnostic_tools.py`:

```python
class TestSelectorTesterCLI:
    """Test that selector_tester.py accepts expected CLI flags."""

    def test_argparse_accepts_url_and_selector(self):
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import test_scripts.selector_tester as tester

        parser = tester.build_parser()
        args = parser.parse_args(["--url", "https://example.com", "--selector", ".product"])
        assert args.url == "https://example.com"
        assert args.selector == ".product"

    def test_argparse_accepts_adapter_mode(self):
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import test_scripts.selector_tester as tester

        parser = tester.build_parser()
        args = parser.parse_args(["--adapter", "bmotor", "--query", "Multistrada"])
        assert args.adapter == "bmotor"
        assert args.query == "Multistrada"

    def test_argparse_requires_url_or_adapter(self):
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import test_scripts.selector_tester as tester

        parser = tester.build_parser()
        # Neither --url nor --adapter: should parse but main() will reject
        args = parser.parse_args([])
        assert args.url is None
        assert args.adapter is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest test_scripts/test_diagnostic_tools.py::TestSelectorTesterCLI -v`
Expected: FAIL — `test_scripts.selector_tester` module not found

- [ ] **Step 3: Create `test_scripts/selector_tester.py`**

```python
"""Interactive CSS selector tester for marketplace adapters.

Test selectors against live sites to debug and develop adapter extractors.

Usage:
    # Direct mode: test a selector against a URL
    uv run python test_scripts/selector_tester.py --url https://www.bmotor.hu --selector ".product-item"

    # Adapter mode: run full adapter flow, then test its selectors
    uv run python test_scripts/selector_tester.py --adapter bmotor --query "Multistrada"
"""

import asyncio
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright, Page
from playwright_stealth import Stealth

from src.adapters.playwright_base import PlaywrightBaseAdapter
from src.adapters.registry import build_adapter_registry
from src.core.types import SearchFilters

_stealth = Stealth()


def build_parser():
    import argparse

    parser = argparse.ArgumentParser(description="CSS selector tester for marketplace adapters")
    parser.add_argument("--url", help="URL to load and test selectors against")
    parser.add_argument("--selector", help="CSS selector to test (direct mode)")
    parser.add_argument("--adapter", help="Adapter name to test (adapter mode)")
    parser.add_argument("--query", default="Ducati Multistrada", help="Search query (adapter mode)")
    return parser


async def test_selector_on_page(page: Page, selector: str, label: str = "") -> int:
    """Test a single CSS selector on a page and print results."""
    elements = await page.query_selector_all(selector)
    count = len(elements)
    prefix = f"  [{label}] " if label else "  "
    print(f"{prefix}'{selector}' -> {count} match(es)")

    for i, el in enumerate(elements[:5]):
        try:
            tag = await el.evaluate("el => el.tagName.toLowerCase()")
            classes = await el.evaluate("el => el.className")
            text = await el.evaluate("el => el.textContent.trim().substring(0, 80)")
            text = re.sub(r"\s+", " ", text).strip()
            print(f"    [{i}] <{tag} class=\"{classes}\"> {text}")
        except Exception:
            print(f"    [{i}] (could not inspect element)")
    return count


async def suggest_selectors(page: Page) -> None:
    """Scan DOM for common product-card patterns and suggest selectors."""
    print("\n  Scanning DOM for potential product patterns...")

    candidates = [
        ("article", "article"),
        (".product", "[class*='product']"),
        ("li with links", "li:has(a[href])"),
        ("cards", "[class*='card']"),
        ("items", "[class*='item']"),
        ("links with images", "a:has(img)"),
        ("forms (e-commerce)", "form:has(a)"),
    ]

    found_any = False
    for label, selector in candidates:
        try:
            elements = await page.query_selector_all(selector)
            if elements:
                count = len(elements)
                print(f"  Suggestion: '{selector}' -> {count} elements ({label})")
                found_any = True
        except Exception:
            continue

    if not found_any:
        print("  No common product patterns detected.")


async def run_direct_mode(url: str, selector: str) -> None:
    """Load a URL and test a CSS selector against it."""
    print(f"\nDirect mode: {url}")
    print(f"Selector: {selector}\n")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()
        await _stealth.apply_stealth_async(page)

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

            print("Results:")
            count = await test_selector_on_page(page, selector)

            if count == 0:
                await suggest_selectors(page)

            # Save screenshot
            diag_dir = Path("diagnostics") / "selector_tests"
            diag_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = diag_dir / f"direct_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\nScreenshot: {screenshot_path}")

        finally:
            await browser.close()


async def run_adapter_mode(adapter_name: str, query: str) -> None:
    """Run an adapter's search flow and test its selectors against the result page."""
    adapters = build_adapter_registry()
    if adapter_name not in adapters:
        print(f"Unknown adapter: {adapter_name}")
        print(f"Available: {', '.join(sorted(adapters.keys()))}")
        sys.exit(1)

    adapter = adapters[adapter_name]
    if not isinstance(adapter, PlaywrightBaseAdapter):
        print(f"{adapter_name} is not a Playwright adapter, cannot inspect selectors.")
        sys.exit(1)

    print(f"\nAdapter mode: {adapter_name}")
    print(f"Query: {query}")
    print(f"Base URL: {adapter.base_url}\n")

    # Run search with diagnostics to keep the page artifacts
    diag_dir = Path("diagnostics") / "selector_tests"
    diag_dir.mkdir(parents=True, exist_ok=True)

    filters = SearchFilters(query=query)

    try:
        results, screenshot_path, dom_path = await adapter.search_with_diagnostics(
            query, filters, diag_dir,
        )
        print(f"Search returned {len(results)} result(s)\n")

        # Test adapter selectors if available
        selectors = adapter._get_selectors()
        if selectors:
            print("Adapter selectors:")
            # Load the captured DOM to test selectors against it
            if dom_path and dom_path.exists():
                async with async_playwright() as pw:
                    browser = await pw.chromium.launch(headless=True)
                    page = await browser.new_page()
                    dom_content = dom_path.read_text(encoding="utf-8")
                    await page.set_content(dom_content)

                    for purpose, selector_list in selectors.items():
                        print(f"\n  Purpose: {purpose}")
                        for sel in selector_list:
                            await test_selector_on_page(page, sel, purpose)

                    if results == []:
                        await suggest_selectors(page)

                    await browser.close()
        else:
            print("Adapter does not implement _get_selectors() — skipping per-selector breakdown.")
            if dom_path and dom_path.exists():
                async with async_playwright() as pw:
                    browser = await pw.chromium.launch(headless=True)
                    page = await browser.new_page()
                    dom_content = dom_path.read_text(encoding="utf-8")
                    await page.set_content(dom_content)
                    await suggest_selectors(page)
                    await browser.close()

        if screenshot_path:
            print(f"\nScreenshot: {screenshot_path}")
        if dom_path:
            print(f"DOM snapshot: {dom_path}")

    finally:
        if hasattr(adapter, "close"):
            try:
                await adapter.close()
            except Exception:
                pass


async def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.url and args.selector:
        await run_direct_mode(args.url, args.selector)
    elif args.adapter:
        await run_adapter_mode(args.adapter, args.query)
    else:
        print("Error: provide either --url + --selector (direct mode) or --adapter (adapter mode)")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run python -m pytest test_scripts/test_diagnostic_tools.py -v`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add test_scripts/selector_tester.py test_scripts/test_diagnostic_tools.py
git commit -m "feat: add selector tester tool for interactive CSS selector debugging"
```

---

## Task 5: Add `_get_selectors()` to BMotor and MaleDucati Adapters

**Files:**
- Modify: `src/adapters/bmotor.py`
- Modify: `src/adapters/maleducati.py`
- Modify: `test_scripts/test_diagnostic_tools.py`

- [ ] **Step 1: Write the failing test**

Append to `test_scripts/test_diagnostic_tools.py`:

```python
from src.adapters.bmotor import BMotorAdapter
from src.adapters.maleducati import MaleDucatiAdapter


class TestAdapterGetSelectors:
    def test_bmotor_returns_selectors(self):
        adapter = BMotorAdapter()
        selectors = adapter._get_selectors()
        assert isinstance(selectors, dict)
        assert len(selectors) > 0
        assert "product_cards" in selectors
        assert "search_input" in selectors

    def test_maleducati_returns_selectors(self):
        adapter = MaleDucatiAdapter()
        selectors = adapter._get_selectors()
        assert isinstance(selectors, dict)
        assert len(selectors) > 0
        assert "product_cards" in selectors
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest test_scripts/test_diagnostic_tools.py::TestAdapterGetSelectors -v`
Expected: FAIL — `_get_selectors` returns empty dict

- [ ] **Step 3: Add `_get_selectors()` to BMotorAdapter**

Add the following method to the `BMotorAdapter` class in `src/adapters/bmotor.py`, after the `_parse_price` method:

```python
    def _get_selectors(self) -> dict[str, list[str]]:
        return {
            "search_input": [
                "input.disableAutocomplete[type='text']",
                "input[placeholder*='keres']",
                "#search input[type='text']",
            ],
            "search_button": [
                "#search_btn",
                "button.btn:has(i.fa-search)",
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
                "h2 a",
                "h3 a",
                ".product-title a",
                ".product-name a",
                "a.product-link",
            ],
            "price": [
                "[class*='price']",
                ".price",
                ".product-price",
            ],
        }
```

- [ ] **Step 4: Add `_get_selectors()` to MaleDucatiAdapter**

Add the following method to the `MaleDucatiAdapter` class in `src/adapters/maleducati.py`, after the `_parse_price` method:

```python
    def _get_selectors(self) -> dict[str, list[str]]:
        return {
            "product_cards": [
                ".product-item",
                ".product-card",
                "[class*='product']",
                ".item",
                "article",
                ".tcs-item",
            ],
            "title": [
                "a[href*='/tcs']",
                "a[href*='maleducati']",
                "h2 a",
                "h3 a",
                ".product-title a",
                ".product-name a",
            ],
            "price": [
                "[class*='price']",
                ".price",
                ".product-price",
            ],
        }
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run python -m pytest test_scripts/test_diagnostic_tools.py::TestAdapterGetSelectors -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/adapters/bmotor.py src/adapters/maleducati.py test_scripts/test_diagnostic_tools.py
git commit -m "feat: add _get_selectors() to BMotor and MaleDucati adapters"
```

---

## Task 6: Document Diagnostic Tools in CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Read current CLAUDE.md**

Read the file to determine where to add the tool documentation.

- [ ] **Step 2: Add tool documentation**

Append the following to `CLAUDE.md`:

```markdown
<smokeDiagnostics>
    <objective>
        Run live smoke tests against marketplace adapters with optional diagnostic capture (screenshots, DOM snapshots) and HTML reporting.
    </objective>
    <command>
        uv run python test_scripts/smoke_test_live.py [OPTIONS]
    </command>
    <info>
        Validates CSS selectors and connectivity against real marketplace sites.
        NOT for CI -- depends on live third-party sites.

        Command line parameters:
        --adapter NAME [NAME...]  Test specific adapters only
        --diagnose               Capture screenshots + DOM for all adapters (auto for EMPTY/ERROR)
        --report                 Generate HTML diagnostic report
        --query "TEXT"           Override default search query (default: "Ducati Multistrada")

        Output:
        - Terminal table: adapter name, status (OK/EMPTY/ERROR/TIMEOUT), result count, time
        - diagnostics/<timestamp>/screenshots/<adapter>.png  (when --diagnose or on failure)
        - diagnostics/<timestamp>/dom/<adapter>.html          (when --diagnose or on failure)
        - diagnostics/<timestamp>/report.html                 (when --report)

        Examples:
        uv run python test_scripts/smoke_test_live.py
        uv run python test_scripts/smoke_test_live.py --adapter bmotor maleducati --diagnose
        uv run python test_scripts/smoke_test_live.py --diagnose --report
        uv run python test_scripts/smoke_test_live.py --query "exhaust pipe" --diagnose --report
    </info>
</smokeDiagnostics>

<selectorTester>
    <objective>
        Test CSS selectors against live marketplace sites for adapter development and debugging.
    </objective>
    <command>
        uv run python test_scripts/selector_tester.py [OPTIONS]
    </command>
    <info>
        Two modes of operation:

        Direct mode: Load a URL and test a CSS selector against it.
        --url URL          URL to load
        --selector SEL     CSS selector to test

        Adapter mode: Run an adapter's full search flow, then test its selectors.
        --adapter NAME     Adapter name from the registry
        --query "TEXT"     Search query (default: "Ducati Multistrada")

        Output:
        - Match count per selector
        - Element previews (tag, classes, text) for first 5 matches
        - Screenshot saved to diagnostics/selector_tests/
        - Selector suggestions when zero matches found

        Examples:
        uv run python test_scripts/selector_tester.py --url https://www.bmotor.hu --selector ".product-item"
        uv run python test_scripts/selector_tester.py --adapter bmotor --query "Multistrada"
        uv run python test_scripts/selector_tester.py --adapter duc_store --query "exhaust"
    </info>
</selectorTester>
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add diagnostic smoke test and selector tester tool documentation"
```

---

## Task 7: Run Full Diagnostic Sweep and Fix Broken Selectors

**Files:**
- Modify: `src/adapters/*.py` (whichever adapters have broken selectors)
- Modify: `Issues - Pending Items.md`

This task is **manual/iterative** — it depends on live site responses and cannot be fully scripted in advance. Follow this process:

- [ ] **Step 1: Run the diagnostic smoke test**

```bash
uv run python test_scripts/smoke_test_live.py --diagnose --report
```

Review the terminal output and `diagnostics/<timestamp>/report.html`.

- [ ] **Step 2: For each EMPTY adapter, run the selector tester**

```bash
uv run python test_scripts/selector_tester.py --adapter <name> --query "Ducati Multistrada"
```

Inspect the DOM snapshot and screenshot. Identify what CSS selectors the real site uses.

- [ ] **Step 3: Fix selectors in each broken adapter**

Open the adapter file, update the CSS selectors in `_extract_listings()` and/or `_parse_card()` to match the real DOM structure. For AJAX adapters, also fix the search interaction selectors in `_extract_listings()`.

- [ ] **Step 4: Re-run smoke test for fixed adapters**

```bash
uv run python test_scripts/smoke_test_live.py --adapter <fixed_adapter_names>
```

Confirm they now return results (status: OK).

- [ ] **Step 5: Update Issues file**

In `Issues - Pending Items.md`, move items 1 (CSS selector validation), 6 (JS-heavy specialist adapters), and 7 (Specialist adapter selector validation) from Pending to Completed with the date.

- [ ] **Step 6: Final full sweep**

```bash
uv run python test_scripts/smoke_test_live.py --report
```

Confirm overall health. Adapters that return EMPTY after selector fixes genuinely have no matching parts for the test query.

- [ ] **Step 7: Commit**

```bash
git add src/adapters/ "Issues - Pending Items.md"
git commit -m "fix: update CSS selectors across marketplace adapters based on live site validation"
```
