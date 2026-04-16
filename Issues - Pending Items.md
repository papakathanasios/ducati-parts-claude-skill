# Issues - Pending Items

## Pending

### High Priority

1. **Kleinanzeigen SSL cert error** - kleinanzeigen.de returns ERR_CERT_AUTHORITY_INVALID. Likely needs system cert store or Playwright cert handling. Was previously working.

### Medium Priority

2. **Site access blocked** - Several adapters are blocked by WAF/bot detection: allegro (tiny DOM, bot block), ital_allparts (Cloudflare), motoye (403 Forbidden), forza_moto (site down/redirect).

3. **Shipping estimate refinement** - Current estimates are rough ranges. Could be improved with actual shipping calculator APIs from major carriers (DHL, DPD, etc.).

4. **eBay additional image extraction** - Currently only extracts the primary listing image. The Browse API supports fetching additional images.

5. **MotoBreakers adapter** - Disabled, needs separate research on site structure and scraping approach.

6. **DucatiParts.cz domain redirect** - ducatiparts.cz now redirects to eshop.krejbichmeccanica.cz. Adapter updated to use the new domain and custom `/vyhledavani?code=` search endpoint. Monitor for further domain changes.

7. **Batch smoke test timeouts** - Some adapters (wallapop, ducbikeparts, motogrotto, duc_store, cheshire_breakers) timeout in batch mode but work individually. Resource contention with 36 parallel browsers.

### Low Priority

8. **Adapters with no "Ducati Multistrada" results** - jofogas, motodesguace_ferrer, desguaces_pedros, colchester_breakers, fresiamoto, ducatiparts_cz return empty for this specific query. May work with other queries.

## Completed

12. **CSS selector validation and fix sweep** - Fixed 9 adapters with broken selectors/URLs: OLX (bg/ro/pl) title selector, BMotor search URL + ShopRenter selectors, MaleDucati Hungarian CMS selectors, Dezosmoto PrestaShop 1.6 selectors, Speckmoto Magento URL + selectors, DucatiMondo Magento URL + selectors, MotorradteileHannover JTL-Shop search param, DucStore ePages URL + selectors. Smoke test improved from 15/36 OK to 20/36 OK. (2026-04-16)

13. **Diagnostic tooling** - Added search_with_diagnostics(), smoke test --diagnose/--report flags, selector_tester.py tool, Jinja2 HTML diagnostic report. (2026-04-15)

11. **23 specialist Ducati adapters added** - Breakers and Ducati-only shops across IT (5), DE (4), FR (4), ES (3), UK (4), HU (2), CZ (1). All registered in registry.py and config.yaml tiers. 183 unit tests passing. Live smoke test confirmed 5+ adapters returning results. (2026-04-15)

7. **Currency rate caching** - ECB rates now cached for 24 hours in-memory via `CurrencyConverter._rates_fetched_at`. (2026-04-15, search-pipeline-overhaul)

8. **OEM part number database expansion** - Seed catalog expanded from 17 to 34 parts with enduro-specific and shared parts. (2026-04-15, search-pipeline-overhaul)

9. **Search pipeline data flow** - Currency conversion wired into orchestrator, multi-language query expansion (30 terms, 12 languages), bilingual relevance filter, parallel adapter execution with per-adapter timeout. (2026-04-15, search-pipeline-overhaul)

10. **Adapter resource cleanup** - Playwright browser processes now cleaned up via try/finally in CLI after search completes. (2026-04-15, search-pipeline-overhaul)
