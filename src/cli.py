import asyncio
import json
import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

from src.adapters.registry import build_adapter_registry
from src.catalog.seed_data import seed_database
from src.core.config import load_config
from src.core.search import SearchOrchestrator
from src.core.types import SearchFilters
from src.db.database import Database
from src.reports.html_report import generate_html_report
from src.reports.terminal_report import format_terminal_report
from src.watch.manager import WatchManager

PROJECT_ROOT = Path(__file__).parent.parent


def _init_db_and_seed() -> None:
    """Initialize the database and seed the parts catalog if the seed file exists."""
    db_path = str(PROJECT_ROOT / "data" / "ducati_parts.db")
    seed_path = PROJECT_ROOT / "data" / "seed_parts.json"

    db = Database(db_path)
    db.initialize()

    if seed_path.exists():
        seed_database(db, str(seed_path))


async def run_search(
    query,
    config_path=None,
    reports_dir=None,
    max_total_price=None,
    tiers=None,
    sources=None,
    adapters=None,
) -> str:
    if config_path is None:
        config_path = str(PROJECT_ROOT / "config" / "config.yaml")
    if reports_dir is None:
        reports_dir = str(PROJECT_ROOT / "reports")

    config = load_config(config_path)

    # Initialize DB and seed catalog on first run
    _init_db_and_seed()

    if adapters is None:
        adapters = build_adapter_registry()

    orchestrator = SearchOrchestrator(config=config, adapters=adapters)
    filters = SearchFilters(
        query=query,
        max_total_price=Decimal(str(max_total_price)) if max_total_price else None,
        tiers=tiers or config.search.default_tiers,
        sources=sources or [],
    )

    listings = await orchestrator.run(filters)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    safe_query = query.replace(" ", "-").replace("/", "-")[:50]
    report_path = str(Path(reports_dir) / f"{timestamp}_{safe_query}.html")

    generate_html_report(listings, query=query, output_path=report_path)
    output = format_terminal_report(listings, query=query, report_path=report_path)
    print(output)

    if orchestrator.last_errors:
        print("\nAdapter errors:")
        for name, error in orchestrator.last_errors.items():
            print(f"  {name}: {error}")

    return report_path


async def run_watch_list(config_path=None, db_path=None) -> str:
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
            f'  {w["id"]}. [{status}] "{w["query"]}" '
            f'| Budget: {w["max_total_price"]:.2f} EUR '
            f"| Last check: {last}"
        )

    output = "\n".join(lines)
    print(output)
    return output
