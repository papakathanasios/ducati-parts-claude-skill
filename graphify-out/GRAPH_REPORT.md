# Graph Report - .  (2026-04-15)

## Corpus Check
- Corpus is ~42,816 words - fits in a single context window. You may not need a graph.

## Summary
- 479 nodes · 867 edges · 45 communities detected
- Extraction: 64% EXTRACTED · 36% INFERRED · 0% AMBIGUOUS · INFERRED: 312 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Playwright Marketplace Adapters|Playwright Marketplace Adapters]]
- [[_COMMUNITY_Search & Config Pipeline|Search & Config Pipeline]]
- [[_COMMUNITY_Core Types & CLI Tests|Core Types & CLI Tests]]
- [[_COMMUNITY_Playwright Base & OLXBazos|Playwright Base & OLX/Bazos]]
- [[_COMMUNITY_Database & Catalog Layer|Database & Catalog Layer]]
- [[_COMMUNITY_eBay Adapter & Base Tests|eBay Adapter & Base Tests]]
- [[_COMMUNITY_OLX Adapter Tests|OLX Adapter Tests]]
- [[_COMMUNITY_Search Orchestrator Tests|Search Orchestrator Tests]]
- [[_COMMUNITY_Subito Adapter Tests|Subito Adapter Tests]]
- [[_COMMUNITY_Condition Filter Tests|Condition Filter Tests]]
- [[_COMMUNITY_Watch Manager|Watch Manager]]
- [[_COMMUNITY_Currency Tests|Currency Tests]]
- [[_COMMUNITY_Types Tests|Types Tests]]
- [[_COMMUNITY_Query Expansion Tests|Query Expansion Tests]]
- [[_COMMUNITY_Currency Converter|Currency Converter]]
- [[_COMMUNITY_Registry Tests|Registry Tests]]
- [[_COMMUNITY_Database Tests|Database Tests]]
- [[_COMMUNITY_Watch Tests|Watch Tests]]
- [[_COMMUNITY_Config Tests|Config Tests]]
- [[_COMMUNITY_Shipping Tests|Shipping Tests]]
- [[_COMMUNITY_Condition Scoring|Condition Scoring]]
- [[_COMMUNITY_Shipping Estimator|Shipping Estimator]]
- [[_COMMUNITY_Catalog Tests|Catalog Tests]]
- [[_COMMUNITY_Terminal Report Tests|Terminal Report Tests]]
- [[_COMMUNITY_macOS Notifier|macOS Notifier]]
- [[_COMMUNITY_HTML Report Tests|HTML Report Tests]]
- [[_COMMUNITY_Smoke Test Script|Smoke Test Script]]
- [[_COMMUNITY_eBay Tests|eBay Tests]]
- [[_COMMUNITY_Scheduler|Scheduler]]
- [[_COMMUNITY_Bike Models|Bike Models]]
- [[_COMMUNITY_Dedup Module|Dedup Module]]
- [[_COMMUNITY_Adapter Registry|Adapter Registry]]
- [[_COMMUNITY_HTML Report|HTML Report]]
- [[_COMMUNITY_Terminal Report|Terminal Report]]
- [[_COMMUNITY_Src Init|Src Init]]
- [[_COMMUNITY_Core Init|Core Init]]
- [[_COMMUNITY_Catalog Init|Catalog Init]]
- [[_COMMUNITY_Adapters Init|Adapters Init]]
- [[_COMMUNITY_DB Init|DB Init]]
- [[_COMMUNITY_Watch Init|Watch Init]]
- [[_COMMUNITY_Reports Init|Reports Init]]
- [[_COMMUNITY_Project Identity|Project Identity]]
- [[_COMMUNITY_Facebook Adapter Issue|Facebook Adapter Issue]]
- [[_COMMUNITY_Shipping Estimate Issue|Shipping Estimate Issue]]
- [[_COMMUNITY_MotoBreakers Issue|MotoBreakers Issue]]

## God Nodes (most connected - your core abstractions)
1. `RawListing` - 49 edges
2. `PlaywrightBaseAdapter` - 41 edges
3. `Database` - 38 edges
4. `SearchFilters` - 26 edges
5. `MockAdapter` - 24 edges
6. `AdapterHealthCheck` - 24 edges
7. `MockAdapter` - 23 edges
8. `WatchManager` - 22 edges
9. `BaseAdapter` - 21 edges
10. `SearchOrchestrator` - 19 edges

## Surprising Connections (you probably didn't know these)
- `TERM_TRANSLATIONS Dictionary` --semantically_similar_to--> `Query Translation Engine Design`  [INFERRED] [semantically similar]
  src/core/query_expansion.py → docs/superpowers/specs/2026-04-15-search-pipeline-overhaul-design.md
- `No Config Fallbacks Policy` --rationale_for--> `load_config()`  [INFERRED]
  README.md → src/core/config.py
- `Listing Data Model` --conceptually_related_to--> `Listing`  [INFERRED]
  docs/design/project-design.md → src/core/types.py
- `Live smoke test for marketplace adapters.  Run manually to validate CSS selector` --uses--> `SearchFilters`  [INFERRED]
  test_scripts/smoke_test_live.py → src/core/types.py
- `Watch Data Model` --conceptually_related_to--> `run_watch_list()`  [INFERRED]
  docs/design/project-design.md → src/cli.py

## Hyperedges (group relationships)
- **Search Pipeline Data Flow** — search_SearchOrchestrator, currency_CurrencyConverter, query_expansion_expand_query, search__is_relevant, types_SearchFilters, types_RawListing, types_Listing [EXTRACTED 1.00]
- **Pipeline Overhaul: Problem-Solution Mapping** — spec_overhaul_problem, spec_overhaul_currency_integration, spec_overhaul_query_expansion, spec_overhaul_relevance_fix, spec_overhaul_parallel, spec_overhaul_timeout, spec_overhaul_rate_caching, spec_overhaul_cleanup [EXTRACTED 1.00]
- **Configuration Hierarchy** — config_AppConfig, config_BikeConfig, config_ShippingConfig, config_SearchConfig, config_ConditionConfig, config_WatchConfig, config_load_config [EXTRACTED 1.00]

## Communities

### Community 0 - "Playwright Marketplace Adapters"
Cohesion: 0.04
Nodes (29): AllegroAdapter, _parse_price(), Allegro.pl adapter – Polish marketplace., BolhaAdapter, Bolha.com adapter – Slovenian classifieds marketplace.  Uses the same Styria Med, FacebookMarketplaceAdapter, Facebook Marketplace adapter – EU-wide marketplace.  NOTE: Facebook Marketplace, JofogasAdapter (+21 more)

### Community 1 - "Search & Config Pipeline"
Cohesion: 0.05
Nodes (56): _init_db_and_seed(), Initialize the database and seed the parts catalog if the seed file exists., run_search(), run_watch_list(), AppConfig, BikeConfig, ConditionConfig, SearchConfig (+48 more)

### Community 2 - "Core Types & CLI Tests"
Cohesion: 0.14
Nodes (40): AdapterHealthCheck, BaseAdapter, AppConfig, BikeConfig, ConditionConfig, load_config(), SearchConfig, ShippingConfig (+32 more)

### Community 3 - "Playwright Base & OLX/Bazos"
Cohesion: 0.08
Nodes (21): ABC, _BazosBase, BazosCzAdapter, BazosSkAdapter, _parse_price(), Bazos adapters – Czech (bazos.cz) and Slovak (bazos.sk) classifieds., Shared extraction logic for both bazos.cz and bazos.sk., NjuskaloAdapter (+13 more)

### Community 4 - "Database & Catalog Layer"
Cohesion: 0.1
Nodes (10): CompatibilityResolver, Return the catalog row for the given OEM number, or None., Return all catalog rows where part_name, search_aliases, or category         mat, Return True/False for the enduro_specific flag, or None if the part         is n, Look up parts in the PartsCatalog table by OEM number or name query., Database, load_seed_data(), Insert seed data into the PartsCatalog table. (+2 more)

### Community 5 - "eBay Adapter & Base Tests"
Cohesion: 0.18
Nodes (7): BaseAdapter, EbayAdapter, BrokenAdapter, FakeAdapter, test_adapter_health_check(), test_adapter_properties(), test_fake_adapter_search()

### Community 6 - "OLX Adapter Tests"
Cohesion: 0.12
Nodes (0): 

### Community 7 - "Search Orchestrator Tests"
Cohesion: 0.3
Nodes (11): _make_config(), MockAdapter, test_dedup_removes_duplicate_listings(), test_orchestrator_collects_results_from_adapters(), test_orchestrator_converts_non_eur_currency(), test_orchestrator_excludes_bad_condition(), test_orchestrator_filters_by_max_total_price(), test_orchestrator_handles_adapter_failure() (+3 more)

### Community 8 - "Subito Adapter Tests"
Cohesion: 0.14
Nodes (0): 

### Community 9 - "Condition Filter Tests"
Cohesion: 0.17
Nodes (0): 

### Community 10 - "Watch Manager"
Cohesion: 0.22
Nodes (2): _deserialize(), WatchManager

### Community 11 - "Currency Tests"
Cohesion: 0.22
Nodes (0): 

### Community 12 - "Types Tests"
Cohesion: 0.22
Nodes (0): 

### Community 13 - "Query Expansion Tests"
Cohesion: 0.25
Nodes (0): 

### Community 14 - "Currency Converter"
Cohesion: 0.29
Nodes (1): CurrencyConverter

### Community 15 - "Registry Tests"
Cohesion: 0.33
Nodes (4): Without EBAY_APP_ID / EBAY_CERT_ID env vars, eBay should not be registered., With both eBay env vars set, eBay should be registered., test_registry_excludes_ebay_without_credentials(), test_registry_includes_ebay_with_credentials()

### Community 16 - "Database Tests"
Cohesion: 0.33
Nodes (0): 

### Community 17 - "Watch Tests"
Cohesion: 0.33
Nodes (0): 

### Community 18 - "Config Tests"
Cohesion: 0.33
Nodes (0): 

### Community 19 - "Shipping Tests"
Cohesion: 0.33
Nodes (0): 

### Community 20 - "Condition Scoring"
Cohesion: 0.4
Nodes (3): ConditionFilter, NormalizedCondition, Enum

### Community 21 - "Shipping Estimator"
Cohesion: 0.4
Nodes (1): ShippingEstimator

### Community 22 - "Catalog Tests"
Cohesion: 0.4
Nodes (0): 

### Community 23 - "Terminal Report Tests"
Cohesion: 0.6
Nodes (3): _make_listing(), test_format_terminal_report_shows_top_3(), test_format_terminal_report_with_results()

### Community 24 - "macOS Notifier"
Cohesion: 0.5
Nodes (4): _escape(), Send a macOS notification using osascript / display notification., Escape backslashes and double quotes for AppleScript strings., send_macos_notification()

### Community 25 - "HTML Report Tests"
Cohesion: 0.67
Nodes (2): _make_listing(), test_generate_html_report_creates_file()

### Community 26 - "Smoke Test Script"
Cohesion: 0.67
Nodes (3): main(), Live smoke test for marketplace adapters.  Run manually to validate CSS selector, test_adapter()

### Community 27 - "eBay Tests"
Cohesion: 0.5
Nodes (0): 

### Community 28 - "Scheduler"
Cohesion: 0.5
Nodes (0): 

### Community 29 - "Bike Models"
Cohesion: 0.67
Nodes (1): BikeModel

### Community 30 - "Dedup Module"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Adapter Registry"
Cohesion: 1.0
Nodes (0): 

### Community 32 - "HTML Report"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Terminal Report"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "Src Init"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "Core Init"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Catalog Init"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Adapters Init"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "DB Init"
Cohesion: 1.0
Nodes (0): 

### Community 39 - "Watch Init"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Reports Init"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Project Identity"
Cohesion: 1.0
Nodes (1): Ducati Parts Finder

### Community 42 - "Facebook Adapter Issue"
Cohesion: 1.0
Nodes (1): Issue: Facebook Adapter Fragility

### Community 43 - "Shipping Estimate Issue"
Cohesion: 1.0
Nodes (1): Issue: Shipping Estimate Refinement

### Community 44 - "MotoBreakers Issue"
Cohesion: 1.0
Nodes (1): Issue: MotoBreakers Adapter Disabled

## Knowledge Gaps
- **29 isolated node(s):** `Without EBAY_APP_ID / EBAY_CERT_ID env vars, eBay should not be registered.`, `With both eBay env vars set, eBay should be registered.`, `Query expansion module for multilingual Ducati parts search.  Translates English`, `Expand *query* by translating known English part terms.      Parameters     ----`, `BikeModel` (+24 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Dedup Module`** (2 nodes): `deduplicate()`, `dedup.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Adapter Registry`** (2 nodes): `build_adapter_registry()`, `registry.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `HTML Report`** (2 nodes): `generate_html_report()`, `html_report.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Terminal Report`** (2 nodes): `terminal_report.py`, `format_terminal_report()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Src Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Core Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Catalog Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Adapters Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `DB Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Watch Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Reports Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Project Identity`** (1 nodes): `Ducati Parts Finder`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Facebook Adapter Issue`** (1 nodes): `Issue: Facebook Adapter Fragility`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Shipping Estimate Issue`** (1 nodes): `Issue: Shipping Estimate Refinement`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `MotoBreakers Issue`** (1 nodes): `Issue: MotoBreakers Adapter Disabled`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RawListing` connect `Core Types & CLI Tests` to `Playwright Marketplace Adapters`, `Playwright Base & OLX/Bazos`, `eBay Adapter & Base Tests`, `Search Orchestrator Tests`?**
  _High betweenness centrality (0.172) - this node is a cross-community bridge._
- **Why does `Database` connect `Database & Catalog Layer` to `Search & Config Pipeline`, `Core Types & CLI Tests`, `Watch Manager`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Why does `load_config()` connect `Core Types & CLI Tests` to `Search & Config Pipeline`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Are the 48 inferred relationships involving `RawListing` (e.g. with `FakeAdapter` and `BrokenAdapter`) actually correct?**
  _`RawListing` has 48 INFERRED edges - model-reasoned connections that need verification._
- **Are the 33 inferred relationships involving `PlaywrightBaseAdapter` (e.g. with `TestPlaywrightAdapter` and `OlxBgAdapter`) actually correct?**
  _`PlaywrightBaseAdapter` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `Database` (e.g. with `MockAdapter` and `Return the path to the project's config.yaml.`) actually correct?**
  _`Database` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `SearchFilters` (e.g. with `Live smoke test for marketplace adapters.  Run manually to validate CSS selector` and `FakeAdapter`) actually correct?**
  _`SearchFilters` has 25 INFERRED edges - model-reasoned connections that need verification._