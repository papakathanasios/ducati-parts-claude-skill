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

                    if not results:
                        await suggest_selectors(page)

                    await browser.close()
        else:
            print("Adapter does not implement _get_selectors() -- skipping per-selector breakdown.")
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
