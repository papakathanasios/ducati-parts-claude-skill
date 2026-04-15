"""Smoke test: slip-on exhaust search across specialist adapters.

Searches for Ducati Multistrada 1260 Enduro exhaust parts and validates
that results are exhaust-related and compatible with the bike.

Usage:
    uv run python test_scripts/smoke_test_exhaust.py
    uv run python test_scripts/smoke_test_exhaust.py --adapter desmomarket motoricambi
"""

import argparse
import asyncio
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.adapters.registry import build_adapter_registry
from src.core.types import SearchFilters

QUERY = "slip-on exhaust Ducati Multistrada 1260 Enduro"

# Keywords that indicate an exhaust part (multilingual)
EXHAUST_KEYWORDS = [
    # English
    "exhaust", "slip-on", "slip on", "slipon", "muffler", "silencer",
    "termignoni", "akrapovic", "akrapovič", "arrow", "leovince",
    "leo vince", "remus", "sc-project", "sc project", "scarico",
    "quat-d", "zard", "hp corse",
    # Italian
    "scarico", "terminale", "marmitta", "silenziatore",
    # German
    "auspuff", "endtopf", "schalldämpfer",
    # French
    "echappement", "échappement", "pot", "silencieux",
    # Spanish
    "escape", "tubo de escape",
    # Hungarian
    "kipufogó", "kipufogo",
    # Czech
    "výfuk", "vyfuk",
]

# Keywords that indicate it's NOT an exhaust (false positives to filter)
NON_EXHAUST_KEYWORDS = [
    "gasket kit", "sensor only", "lambda only", "hanger only",
    "bracket only", "clamp only",
]

# Multistrada 1260 compatible model identifiers
COMPATIBLE_MODELS = [
    "1260", "multistrada",
]


def is_exhaust_related(title: str) -> bool:
    """Check if a listing title is exhaust-related."""
    lower = title.lower()
    return any(kw in lower for kw in EXHAUST_KEYWORDS)


def is_compatible(title: str) -> bool:
    """Check if listing mentions a compatible model."""
    lower = title.lower()
    # If no model mentioned at all, assume potentially compatible
    has_model_ref = any(m in lower for m in ["monster", "panigale", "scrambler",
                                              "streetfighter", "hypermotard",
                                              "diavel", "supersport", "848", "1098",
                                              "1199", "1299", "749", "999", "916"])
    if has_model_ref:
        return False  # Mentions a different model
    return True


async def run_exhaust_test(adapter_names: list[str] | None = None) -> None:
    adapters = build_adapter_registry()

    # Only test specialist adapters by default
    specialist_keys = [
        # Italian
        "desmomarket", "dgarageparts", "fresiamoto", "motoricambi", "eramotoricambi",
        # German
        "used_italian_parts", "ducbikeparts", "motorradteile_hannover", "duc_store",
        # French
        "ital_allparts", "forza_moto", "dezosmoto", "speckmoto",
        # Spanish
        "motodesguace_ferrer", "motoye", "desguaces_pedros",
        # UK
        "ducatimondo", "motogrotto", "colchester_breakers", "cheshire_breakers",
        # Hungary
        "bmotor", "maleducati",
        # Czech
        "ducatiparts_cz",
    ]

    if adapter_names:
        test_adapters = {k: v for k, v in adapters.items() if k in adapter_names}
    else:
        test_adapters = {k: v for k, v in adapters.items() if k in specialist_keys}

    filters = SearchFilters(query=QUERY)

    print(f"Exhaust Smoke Test - {len(test_adapters)} specialist adapters")
    print(f'Query: "{QUERY}"')
    print("=" * 100)

    total_results = 0
    exhaust_results = 0
    compatible_results = 0
    all_listings = []

    for name, adapter in test_adapters.items():
        start = time.monotonic()
        try:
            results = await asyncio.wait_for(
                adapter.search(QUERY, filters),
                timeout=45,
            )
            elapsed = time.monotonic() - start

            exhaust_count = sum(1 for r in results if is_exhaust_related(r.title))
            compat_count = sum(1 for r in results if is_exhaust_related(r.title) and is_compatible(r.title))

            status = "OK" if results else "EMPTY"
            print(f"\n{name:<25} [{status}] {len(results)} results, "
                  f"{exhaust_count} exhaust-related, {compat_count} compatible ({elapsed:.1f}s)")

            for r in results:
                is_ex = is_exhaust_related(r.title)
                is_co = is_compatible(r.title) if is_ex else False
                marker = "  [EXHAUST]" if is_ex else "  [OTHER]"
                if is_ex and is_co:
                    marker = "  [EXHAUST+COMPAT]"
                print(f"    {marker} {r.title[:70]} | {r.price} {r.currency}")

            total_results += len(results)
            exhaust_results += exhaust_count
            compatible_results += compat_count
            all_listings.extend(results)

        except asyncio.TimeoutError:
            elapsed = time.monotonic() - start
            print(f"\n{name:<25} [TIMEOUT] ({elapsed:.1f}s)")
        except Exception as e:
            elapsed = time.monotonic() - start
            print(f"\n{name:<25} [ERROR] {str(e)[:60]} ({elapsed:.1f}s)")
        finally:
            if hasattr(adapter, "close"):
                try:
                    await adapter.close()
                except Exception:
                    pass

    print("\n" + "=" * 100)
    print(f"SUMMARY: {total_results} total results, {exhaust_results} exhaust-related, "
          f"{compatible_results} compatible with Multistrada 1260")

    if total_results > 0:
        exhaust_pct = (exhaust_results / total_results * 100) if total_results else 0
        print(f"Exhaust relevance: {exhaust_pct:.0f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exhaust smoke test for specialist adapters")
    parser.add_argument("--adapter", nargs="+", help="Test specific adapters only")
    args = parser.parse_args()
    asyncio.run(run_exhaust_test(args.adapter))
