# Graph Report - .  (2026-04-15)

## Corpus Check
- 96 files · ~51,240 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 644 nodes · 1295 edges · 46 communities detected
- Extraction: 58% EXTRACTED · 42% INFERRED · 0% AMBIGUOUS · INFERRED: 543 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Specialist Adapters|Specialist Adapters]]
- [[_COMMUNITY_Playwright & Marketplace Adapters|Playwright & Marketplace Adapters]]
- [[_COMMUNITY_Core Framework & Config|Core Framework & Config]]
- [[_COMMUNITY_Search Pipeline & Domain Logic|Search Pipeline & Domain Logic]]
- [[_COMMUNITY_Project Architecture & Issues|Project Architecture & Issues]]
- [[_COMMUNITY_Database & Catalog|Database & Catalog]]
- [[_COMMUNITY_OLX Adapter Tests|OLX Adapter Tests]]
- [[_COMMUNITY_Subito Adapter Tests|Subito Adapter Tests]]
- [[_COMMUNITY_Condition Filter Tests|Condition Filter Tests]]
- [[_COMMUNITY_Base Adapter Tests|Base Adapter Tests]]
- [[_COMMUNITY_Era Moto Ricambi Adapter|Era Moto Ricambi Adapter]]
- [[_COMMUNITY_SpeckMoto Adapter|SpeckMoto Adapter]]
- [[_COMMUNITY_MotoGrotto Adapter|MotoGrotto Adapter]]
- [[_COMMUNITY_DucBikeParts Adapter|DucBikeParts Adapter]]
- [[_COMMUNITY_MotoRicambi Adapter|MotoRicambi Adapter]]
- [[_COMMUNITY_Colchester Breakers Adapter|Colchester Breakers Adapter]]
- [[_COMMUNITY_BMotor Adapter|BMotor Adapter]]
- [[_COMMUNITY_DesmoMarket Adapter|DesmoMarket Adapter]]
- [[_COMMUNITY_DucStore Adapter|DucStore Adapter]]
- [[_COMMUNITY_DGarageParts Adapter|DGarageParts Adapter]]
- [[_COMMUNITY_Registry Tests|Registry Tests]]
- [[_COMMUNITY_Database Tests|Database Tests]]
- [[_COMMUNITY_Watch Manager Tests|Watch Manager Tests]]
- [[_COMMUNITY_Shipping Tests|Shipping Tests]]
- [[_COMMUNITY_Catalog Tests|Catalog Tests]]
- [[_COMMUNITY_Terminal Report Tests|Terminal Report Tests]]
- [[_COMMUNITY_macOS Notifier|macOS Notifier]]
- [[_COMMUNITY_HTML Report Tests|HTML Report Tests]]
- [[_COMMUNITY_eBay Adapter Tests|eBay Adapter Tests]]
- [[_COMMUNITY_Used Italian Parts Adapter|Used Italian Parts Adapter]]
- [[_COMMUNITY_Watch Scheduler|Watch Scheduler]]
- [[_COMMUNITY_Bike Models|Bike Models]]
- [[_COMMUNITY_Catalog & Compatibility|Catalog & Compatibility]]
- [[_COMMUNITY_Graph Hub Nodes|Graph Hub Nodes]]
- [[_COMMUNITY_Deduplication|Deduplication]]
- [[_COMMUNITY_Adapter Registry Builder|Adapter Registry Builder]]
- [[_COMMUNITY_HTML Report Generator|HTML Report Generator]]
- [[_COMMUNITY_Terminal Report Formatter|Terminal Report Formatter]]
- [[_COMMUNITY_Reporting Module|Reporting Module]]
- [[_COMMUNITY_Package Root|Package Root]]
- [[_COMMUNITY_Core Package Init|Core Package Init]]
- [[_COMMUNITY_Catalog Package Init|Catalog Package Init]]
- [[_COMMUNITY_Adapters Package Init|Adapters Package Init]]
- [[_COMMUNITY_DB Package Init|DB Package Init]]
- [[_COMMUNITY_Watch Package Init|Watch Package Init]]
- [[_COMMUNITY_Reports Package Init|Reports Package Init]]

## God Nodes (most connected - your core abstractions)
1. `RawListing` - 96 edges
2. `PlaywrightBaseAdapter` - 87 edges
3. `Database` - 37 edges
4. `TestEurParsePrice` - 30 edges
5. `TestGbpParsePrice` - 30 edges
6. `TestCzkParsePrice` - 30 edges
7. `TestUsedItalianPartsExtractPrice` - 30 edges
8. `SearchFilters` - 30 edges
9. `TestHufParsePrice` - 29 edges
10. `TestMotorradteileParsePrice` - 29 edges

## Surprising Connections (you probably didn't know these)
- `TERM_TRANSLATIONS Dictionary` --semantically_similar_to--> `Query Translation Engine Design`  [INFERRED] [semantically similar]
  src/core/query_expansion.py → docs/superpowers/specs/2026-04-15-search-pipeline-overhaul-design.md
- `Listing Data Model` --conceptually_related_to--> `Listing`  [INFERRED]
  docs/design/project-design.md → src/core/types.py
- `Condition Assessment Pipeline` --conceptually_related_to--> `ConditionScore`  [INFERRED]
  docs/design/project-design.md → src/core/types.py
- `Adapter Interface Contract` --conceptually_related_to--> `MockAdapter (test)`  [INFERRED]
  docs/design/project-design.md → test_scripts/test_search.py
- `Price Hint Pass-Through Design` --conceptually_related_to--> `SearchFilters`  [EXTRACTED]
  docs/superpowers/specs/2026-04-15-search-pipeline-overhaul-design.md → src/core/types.py

## Hyperedges (group relationships)
- **Search Pipeline Data Flow** — search_SearchOrchestrator, currency_CurrencyConverter, query_expansion_expand_query, search__is_relevant, types_SearchFilters, types_RawListing, types_Listing [EXTRACTED 1.00]
- **Pipeline Overhaul: Problem-Solution Mapping** — spec_overhaul_problem, spec_overhaul_currency_integration, spec_overhaul_query_expansion, spec_overhaul_relevance_fix, spec_overhaul_parallel, spec_overhaul_timeout, spec_overhaul_rate_caching, spec_overhaul_cleanup [EXTRACTED 1.00]
- **Explicit-over-Implicit Design Philosophy** — no_orm_decision, no_config_fallbacks, total_cost_filtering, eu_preferred_policy [INFERRED 0.75]
- **Adapter Health Issue Cluster** — issue_css_selector_validation, issue_js_heavy_adapters, issue_specialist_selector_validation, issue_facebook_fragility, issue_motobreakers [INFERRED 0.80]
- **Search Pipeline Data Flow** — search_orchestrator, currency_converter, query_expansion, condition_filter, shipping_estimator, adapter_registry [INFERRED 0.85]

## Communities

### Community 0 - "Specialist Adapters"
Cohesion: 0.03
Nodes (42): CheshireBreakersAdapter, _parse_price(), Cheshire Bike Breakers adapter (cheshirebikebreakers.com).  25 years experience., DesguacesPedrosAdapter, _parse_price(), Desguaces Pedros adapter – Spanish motorcycle breaker (desguacespedros.es).  Pre, DezosmotoAdapter, DucatiMondoAdapter (+34 more)

### Community 1 - "Playwright & Marketplace Adapters"
Cohesion: 0.03
Nodes (53): AllegroAdapter, _parse_price(), Allegro.pl adapter – Polish marketplace., _BazosBase, BazosCzAdapter, BazosSkAdapter, _parse_price(), Bazos adapters – Czech (bazos.cz) and Slovak (bazos.sk) classifieds. (+45 more)

### Community 2 - "Core Framework & Config"
Cohesion: 0.09
Nodes (46): ABC, AdapterHealthCheck, BaseAdapter, AppConfig, BikeConfig, ConditionConfig, load_config(), SearchConfig (+38 more)

### Community 3 - "Search Pipeline & Domain Logic"
Cohesion: 0.06
Nodes (38): _init_db_and_seed(), run_search(), run_watch_list(), ConditionFilter, NormalizedCondition, CurrencyConverter, ECB Rate Fetching, 24-Hour Rate Caching (+30 more)

### Community 4 - "Project Architecture & Issues"
Cohesion: 0.05
Nodes (41): Adapter Registry, BIKE_MODEL Environment Variable, Completed: Currency Rate Caching, Completed: Adapter Resource Cleanup, Completed: Search Pipeline Data Flow, Completed: 23 Specialist Ducati Adapters, ConditionFilter, Cost Arbitrage Strategy (+33 more)

### Community 5 - "Database & Catalog"
Cohesion: 0.1
Nodes (10): CompatibilityResolver, Return the catalog row for the given OEM number, or None., Return all catalog rows where part_name, search_aliases, or category         mat, Return True/False for the enduro_specific flag, or None if the part         is n, Look up parts in the PartsCatalog table by OEM number or name query., Database, load_seed_data(), Insert seed data into the PartsCatalog table. (+2 more)

### Community 6 - "OLX Adapter Tests"
Cohesion: 0.12
Nodes (0): 

### Community 7 - "Subito Adapter Tests"
Cohesion: 0.14
Nodes (0): 

### Community 8 - "Condition Filter Tests"
Cohesion: 0.17
Nodes (0): 

### Community 9 - "Base Adapter Tests"
Cohesion: 0.31
Nodes (6): BaseAdapter, BrokenAdapter, FakeAdapter, test_adapter_health_check(), test_adapter_properties(), test_fake_adapter_search()

### Community 10 - "Era Moto Ricambi Adapter"
Cohesion: 0.38
Nodes (3): EraMotoRicambiAdapter, _parse_price(), Era Moto Ricambi adapter – Italian motorcycle breaker (shop.eramotoricambi.it).

### Community 11 - "SpeckMoto Adapter"
Cohesion: 0.38
Nodes (3): _parse_price(), Speck Moto Pieces adapter – French motorcycle breaker (speckmotospieces.com).  P, SpeckMotoAdapter

### Community 12 - "MotoGrotto Adapter"
Cohesion: 0.38
Nodes (3): MotoGrottoAdapter, _parse_price(), Moto Grotto adapter – UK motorcycle breaker (motogrotto.co.uk).  WooCommerce sit

### Community 13 - "DucBikeParts Adapter"
Cohesion: 0.38
Nodes (3): DucBikePartsAdapter, _parse_price(), DucBikeParts adapter – German Ducati specialist (ducbikeparts.de).  WooCommerce

### Community 14 - "MotoRicambi Adapter"
Cohesion: 0.38
Nodes (3): MotoricambiAdapter, _parse_price(), Motoricambi Cerignola adapter – Italian motorcycle breaker (motoricambicerignola

### Community 15 - "Colchester Breakers Adapter"
Cohesion: 0.38
Nodes (3): ColchesterBreakersAdapter, _parse_price(), Colchester Motorcycle Breakers adapter (colchesterbreakers.co.uk).  Custom site.

### Community 16 - "BMotor Adapter"
Cohesion: 0.38
Nodes (3): BMotorAdapter, _parse_price(), BMotor adapter – Hungarian motorcycle breaker (bmotor.hu).  Budapest-based. Sear

### Community 17 - "DesmoMarket Adapter"
Cohesion: 0.38
Nodes (3): DesmoMarketAdapter, _parse_price(), Desmo Market adapter – Italian Ducati-only breaker (desmomarket.com).  WooCommer

### Community 18 - "DucStore Adapter"
Cohesion: 0.38
Nodes (3): DucStoreAdapter, _parse_price(), Duc-Store adapter – German Ducati specialist (duc-store.de).  Odoo-based e-comme

### Community 19 - "DGarageParts Adapter"
Cohesion: 0.38
Nodes (3): DGaragePartsAdapter, _parse_price(), DGarage Parts adapter – Italian Ducati specialist (dgarageparts.com).  Shopify s

### Community 20 - "Registry Tests"
Cohesion: 0.33
Nodes (4): Without EBAY_APP_ID / EBAY_CERT_ID env vars, eBay should not be registered., With both eBay env vars set, eBay should be registered., test_registry_excludes_ebay_without_credentials(), test_registry_includes_ebay_with_credentials()

### Community 21 - "Database Tests"
Cohesion: 0.33
Nodes (0): 

### Community 22 - "Watch Manager Tests"
Cohesion: 0.33
Nodes (0): 

### Community 23 - "Shipping Tests"
Cohesion: 0.33
Nodes (0): 

### Community 24 - "Catalog Tests"
Cohesion: 0.4
Nodes (0): 

### Community 25 - "Terminal Report Tests"
Cohesion: 0.6
Nodes (3): _make_listing(), test_format_terminal_report_shows_top_3(), test_format_terminal_report_with_results()

### Community 26 - "macOS Notifier"
Cohesion: 0.5
Nodes (4): _escape(), Send a macOS notification using osascript / display notification., Escape backslashes and double quotes for AppleScript strings., send_macos_notification()

### Community 27 - "HTML Report Tests"
Cohesion: 0.67
Nodes (2): _make_listing(), test_generate_html_report_creates_file()

### Community 28 - "eBay Adapter Tests"
Cohesion: 0.5
Nodes (0): 

### Community 29 - "Used Italian Parts Adapter"
Cohesion: 0.5
Nodes (2): _extract_price(), Used Italian Parts adapter – German Ducati specialist (used-italian-parts.de).

### Community 30 - "Watch Scheduler"
Cohesion: 0.5
Nodes (0): 

### Community 31 - "Bike Models"
Cohesion: 0.67
Nodes (1): BikeModel

### Community 32 - "Catalog & Compatibility"
Cohesion: 0.67
Nodes (3): CompatibilityResolver, Completed: OEM Part Number Database Expansion, src/catalog/

### Community 33 - "Graph Hub Nodes"
Cohesion: 1.0
Nodes (3): Knowledge Graph Report, PlaywrightBaseAdapter (God Node), RawListing (God Node)

### Community 34 - "Deduplication"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "Adapter Registry Builder"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "HTML Report Generator"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Terminal Report Formatter"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "Reporting Module"
Cohesion: 1.0
Nodes (2): HTML Report Generator, src/reports/

### Community 39 - "Package Root"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Core Package Init"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Catalog Package Init"
Cohesion: 1.0
Nodes (0): 

### Community 42 - "Adapters Package Init"
Cohesion: 1.0
Nodes (0): 

### Community 43 - "DB Package Init"
Cohesion: 1.0
Nodes (0): 

### Community 44 - "Watch Package Init"
Cohesion: 1.0
Nodes (0): 

### Community 45 - "Reports Package Init"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **33 isolated node(s):** `Without EBAY_APP_ID / EBAY_CERT_ID env vars, eBay should not be registered.`, `With both eBay env vars set, eBay should be registered.`, `FailingAdapter (test)`, `_MODEL_TOKENS (untranslatable set)`, `_COMPOUND_TERMS` (+28 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Deduplication`** (2 nodes): `deduplicate()`, `dedup.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Adapter Registry Builder`** (2 nodes): `build_adapter_registry()`, `registry.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `HTML Report Generator`** (2 nodes): `generate_html_report()`, `html_report.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Terminal Report Formatter`** (2 nodes): `terminal_report.py`, `format_terminal_report()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Reporting Module`** (2 nodes): `HTML Report Generator`, `src/reports/`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Package Root`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Core Package Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Catalog Package Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Adapters Package Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `DB Package Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Watch Package Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Reports Package Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RawListing` connect `Playwright & Marketplace Adapters` to `Specialist Adapters`, `Core Framework & Config`, `Search Pipeline & Domain Logic`, `Base Adapter Tests`, `Era Moto Ricambi Adapter`, `SpeckMoto Adapter`, `MotoGrotto Adapter`, `DucBikeParts Adapter`, `MotoRicambi Adapter`, `Colchester Breakers Adapter`, `BMotor Adapter`, `DesmoMarket Adapter`, `DucStore Adapter`, `DGarageParts Adapter`, `Used Italian Parts Adapter`?**
  _High betweenness centrality (0.328) - this node is a cross-community bridge._
- **Why does `PlaywrightBaseAdapter` connect `Playwright & Marketplace Adapters` to `Specialist Adapters`, `Core Framework & Config`, `Base Adapter Tests`, `Era Moto Ricambi Adapter`, `SpeckMoto Adapter`, `MotoGrotto Adapter`, `DucBikeParts Adapter`, `MotoRicambi Adapter`, `Colchester Breakers Adapter`, `BMotor Adapter`, `DesmoMarket Adapter`, `DucStore Adapter`, `DGarageParts Adapter`, `Used Italian Parts Adapter`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Why does `MockAdapter` connect `Core Framework & Config` to `Base Adapter Tests`, `Database & Catalog`, `Playwright & Marketplace Adapters`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Are the 92 inferred relationships involving `RawListing` (e.g. with `FakeAdapter` and `BrokenAdapter`) actually correct?**
  _`RawListing` has 92 INFERRED edges - model-reasoned connections that need verification._
- **Are the 79 inferred relationships involving `PlaywrightBaseAdapter` (e.g. with `TestPlaywrightAdapter` and `MotodesguaceFerrerAdapter`) actually correct?**
  _`PlaywrightBaseAdapter` has 79 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `Database` (e.g. with `MockAdapter` and `Return the path to the project's config.yaml.`) actually correct?**
  _`Database` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `TestEurParsePrice` (e.g. with `DesmoMarketAdapter` and `DGaragePartsAdapter`) actually correct?**
  _`TestEurParsePrice` has 23 INFERRED edges - model-reasoned connections that need verification._