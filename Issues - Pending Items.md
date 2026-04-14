# Issues - Pending Items

## Pending

### High Priority

1. **Facebook adapter fragility** - Facebook actively blocks automation. The Facebook adapter will require periodic maintenance as selectors and anti-bot measures change. Consider email notification fallback from Facebook Groups.

2. **CSS selector validation** - All Playwright-based adapters have initial CSS selectors that need validation against live sites. Run `test_scripts/smoke_test_live.py` to detect selector rot.

### Medium Priority

3. **Shipping estimate refinement** - Current estimates are rough ranges. Could be improved with actual shipping calculator APIs from major carriers (DHL, DPD, etc.).

4. **eBay additional image extraction** - Currently only extracts the primary listing image. The Browse API supports fetching additional images.

5. **MotoBreakers adapter** - Disabled, needs separate research on site structure and scraping approach.

## Completed

7. **Currency rate caching** - ECB rates now cached for 24 hours in-memory via `CurrencyConverter._rates_fetched_at`. (2026-04-15, search-pipeline-overhaul)

8. **OEM part number database expansion** - Seed catalog expanded from 17 to 34 parts with enduro-specific and shared parts. (2026-04-15, search-pipeline-overhaul)

9. **Search pipeline data flow** - Currency conversion wired into orchestrator, multi-language query expansion (30 terms, 12 languages), bilingual relevance filter, parallel adapter execution with per-adapter timeout. (2026-04-15, search-pipeline-overhaul)

10. **Adapter resource cleanup** - Playwright browser processes now cleaned up via try/finally in CLI after search completes. (2026-04-15, search-pipeline-overhaul)
