"""Watch runner -- entry point for cron / launchd invocations.

Loads configuration, iterates over active watches, runs searches,
deduplicates against SeenListing, generates HTML reports, and sends
macOS notifications for new hits.
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from src.core.config import load_config, AppConfig
from src.core.search import SearchOrchestrator
from src.core.types import Listing, SearchFilters
from src.db.database import Database
from src.reports.html_report import generate_html_report
from src.watch.manager import WatchManager
from src.watch.notifier import send_macos_notification

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = str(PROJECT_ROOT / "config" / "config.yaml")
DB_PATH = str(PROJECT_ROOT / "data" / "ducati_parts.db")
REPORTS_DIR = PROJECT_ROOT / "reports"


async def _run_watch(
    watch: dict,
    orchestrator: SearchOrchestrator,
    db: Database,
    config: AppConfig,
) -> None:
    """Process a single watch: search, dedupe, report, notify."""
    watch_id = watch["id"]
    query = watch["query"]

    filters = SearchFilters(
        query=query,
        max_total_price=Decimal(str(watch["max_total_price"])),
        target_models=watch.get("target_models", []),
        sources=watch.get("sources", []),
        oem_number=watch.get("oem_number") or None,
        part_category=watch.get("part_category") or None,
    )

    logger.info("Watch %d: searching for '%s'", watch_id, query)

    try:
        listings = await orchestrator.run(filters)
    except Exception:
        logger.exception("Watch %d: search failed", watch_id)
        return

    new_listings: list[Listing] = []
    for listing in listings:
        if not db.is_listing_seen(listing.id, watch_id):
            db.mark_listing_seen(listing.id, watch_id)
            new_listings.append(listing)

    db.update_watch_last_checked(watch_id)

    if not new_listings:
        logger.info("Watch %d: no new listings", watch_id)
        return

    logger.info("Watch %d: %d new listings found", watch_id, len(new_listings))

    # Generate HTML report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = query.replace(" ", "_").replace("/", "_")
    report_filename = f"watch_{watch_id}_{safe_query}_{timestamp}.html"
    report_path = str(REPORTS_DIR / report_filename)
    generate_html_report(new_listings, query, report_path)
    logger.info("Watch %d: report saved to %s", watch_id, report_path)

    # Find the best listing by total price
    best = min(new_listings, key=lambda l: l.total_price)

    # Send macOS notification
    if config.watch.notification == "macos":
        send_macos_notification(
            title="Ducati Parts Finder",
            message=f'{len(new_listings)} new listing{"s" if len(new_listings) != 1 else ""} for "{query}"',
            subtitle=f"Best: {best.total_price} {best.currency_original} total ({best.source})",
            open_url=best.listing_url,
        )

    # Mark all new listings as notified
    for listing in new_listings:
        db.mark_listing_notified(listing.id, watch_id)


def main() -> None:
    """Entry point for cron / launchd."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = load_config(CONFIG_PATH)
    db = Database(DB_PATH)
    db.initialize()

    mgr = WatchManager(db)
    watches = mgr.list_active()

    if not watches:
        logger.info("No active watches")
        return

    logger.info("Processing %d active watches", len(watches))

    # Build adapters dict -- import available adapters dynamically
    adapters: dict = {}
    try:
        from src.adapters.ebay import EbayAdapter
        adapters["ebay_eu"] = EbayAdapter()
    except Exception:
        logger.warning("Could not load EbayAdapter")

    orchestrator = SearchOrchestrator(config, adapters)

    for watch in watches:
        asyncio.run(_run_watch(watch, orchestrator, db, config))

    logger.info("Watch run complete")


if __name__ == "__main__":
    main()
