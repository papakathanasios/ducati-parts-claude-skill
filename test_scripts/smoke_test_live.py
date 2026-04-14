"""Live smoke test for marketplace adapters.

Run manually to validate CSS selectors and connectivity against real sites.
NOT for CI -- depends on live third-party sites.

Usage:
    uv run python test_scripts/smoke_test_live.py
    uv run python test_scripts/smoke_test_live.py --adapter olx_bg subito_it
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.adapters.registry import build_adapter_registry
from src.core.types import SearchFilters

QUERY = "Ducati Multistrada"


async def test_adapter(name: str, adapter, filters: SearchFilters) -> dict:
    start = time.monotonic()
    try:
        results = await asyncio.wait_for(
            adapter.search(QUERY, filters),
            timeout=30,
        )
        elapsed = time.monotonic() - start
        return {
            "name": name,
            "status": "OK" if results else "EMPTY",
            "count": len(results),
            "time": f"{elapsed:.1f}s",
            "error": None,
        }
    except asyncio.TimeoutError:
        elapsed = time.monotonic() - start
        return {
            "name": name,
            "status": "TIMEOUT",
            "count": 0,
            "time": f"{elapsed:.1f}s",
            "error": "Exceeded 30s timeout",
        }
    except Exception as e:
        elapsed = time.monotonic() - start
        return {
            "name": name,
            "status": "ERROR",
            "count": 0,
            "time": f"{elapsed:.1f}s",
            "error": str(e)[:80],
        }


async def main(adapter_names: list[str] | None = None) -> None:
    adapters = build_adapter_registry()

    if adapter_names:
        adapters = {k: v for k, v in adapters.items() if k in adapter_names}
        missing = set(adapter_names) - set(adapters.keys())
        if missing:
            print(f"Unknown adapters: {', '.join(missing)}")
            print(f"Available: {', '.join(build_adapter_registry().keys())}")
            sys.exit(1)

    filters = SearchFilters(query=QUERY)

    print(f'Smoke testing {len(adapters)} adapters with query: "{QUERY}"')
    print(f"{'Adapter':<20} {'Status':<10} {'Results':<10} {'Time':<10} {'Error'}")
    print("-" * 80)

    results = []
    for name, adapter in adapters.items():
        result = await test_adapter(name, adapter, filters)
        results.append(result)
        error_str = result["error"] or ""
        print(f"{result['name']:<20} {result['status']:<10} {result['count']:<10} {result['time']:<10} {error_str}")

        if hasattr(adapter, 'close'):
            try:
                await adapter.close()
            except Exception:
                pass

    ok = sum(1 for r in results if r["status"] == "OK")
    empty = sum(1 for r in results if r["status"] == "EMPTY")
    errors = sum(1 for r in results if r["status"] in ("ERROR", "TIMEOUT"))
    print("-" * 80)
    print(f"Summary: {ok} OK, {empty} EMPTY, {errors} ERROR/TIMEOUT out of {len(results)} adapters")

    if empty > 0:
        print("\nEMPTY adapters may have broken CSS selectors. Inspect the live page and update _extract_listings().")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live smoke test for marketplace adapters")
    parser.add_argument("--adapter", nargs="+", help="Test specific adapters only")
    args = parser.parse_args()
    asyncio.run(main(args.adapter))
