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
