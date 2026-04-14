---
name: ducati-parts
description: Find used Ducati Multistrada 1260 Enduro parts across European marketplaces. Search on-demand, manage watch lists, check compatibility.
---

# Ducati Parts Finder

You help the user find used parts for their Ducati Multistrada 1260 Enduro across European marketplaces.

## Setup

Working directory: `/Users/thanos/Work/Repos/ducati-parts`
Always activate the venv before running Python: `source .venv/bin/activate`

## Capabilities

### On-Demand Search

When the user asks to find a part (e.g., "find me a clutch lever", "search for exhaust"):

1. Determine the part name from the user's request
2. Check the parts catalog for compatibility info:
   ```bash
   cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -c "
   from src.catalog.compatibility import CompatibilityResolver
   from src.db.database import Database
   db = Database('data/ducati_parts.db')
   db.initialize()
   resolver = CompatibilityResolver(db)
   matches = resolver.resolve_by_name('<PART_NAME>')
   for m in matches:
       print(f\"OEM: {m['oem_number']} | {m['part_name']} | Enduro-specific: {m['enduro_specific']} | Fits: {m['compatible_models']}\")
   "
   ```
3. Run the search:
   ```bash
   cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -c "
   import asyncio
   from src.cli import run_search
   asyncio.run(run_search(
       query='<SEARCH_QUERY>',
       max_total_price=<BUDGET_OR_None>,
       tiers=<TIERS_OR_None>,
   ))
   "
   ```
4. Present the terminal summary to the user
5. Mention the HTML report path for detailed review

### Query Translation

Before searching, translate the user's query into search terms for each platform's language. The search orchestrator handles adapter routing, but you should expand the query to include:
- The bike model name
- Compatible model names (for shared parts)
- OEM part number if known from catalog

Example: User says "clutch lever" -> search with "clutch lever multistrada 1260" and include "Multistrada 1260 Enduro" + "Multistrada 1260" for shared parts.

### Watch List Management

- **Create watch:** Extract query, budget, and optional tier preferences from user request. Run:
  ```bash
  cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -c "
  from src.db.database import Database
  from src.watch.manager import WatchManager
  db = Database('data/ducati_parts.db')
  db.initialize()
  mgr = WatchManager(db)
  wid = mgr.create(query='<QUERY>', max_total_price=<BUDGET>, target_models=[<MODELS>])
  print(f'Watch created: ID {wid}')
  "
  ```

- **List watches:** `asyncio.run(run_watch_list())`

- **Pause/resume/remove:** Use `mgr.pause(ID)`, `mgr.resume(ID)`, `mgr.remove(ID)`

- **Update budget:** `mgr.update_budget(ID, NEW_AMOUNT)`

### Install/Uninstall Cron

When user creates their first watch, offer to install the scheduler:
```bash
cd /Users/thanos/Work/Repos/ducati-parts && source .venv/bin/activate && python -c "
from src.watch.scheduler import install_schedule
path = install_schedule(interval_hours=4)
print(f'Scheduler installed at {path}')
"
```

### Bike Switching

If the user asks to switch to a different bike model, update the config. The default is Multistrada 1260 Enduro. Active watches remain on their original model.

### Compatibility Queries

When the user asks "does X fit my bike?" or "is Y compatible?":
1. Check catalog by OEM number or name
2. Report whether it's Enduro-specific or shared
3. If not in catalog, suggest checking manually and offer to add it

## Search Tiers

- **Tier 1** (cheapest, always searched): Bulgaria, Romania, Hungary, Poland, Czech Republic, Slovakia, Croatia, Slovenia
- **Tier 2** (default): Italy (Subito), eBay EU, moto breaker sites
- **Tier 3** (opt-in): Germany, France, Spain, UK (UK has customs)

Default searches Tier 1 + 2. User can say "search everywhere" for all tiers or "cheap countries only" for Tier 1 only.

## Condition Scoring

Results are scored green/yellow/red. You assess condition from listing descriptions and photos:
- **Green:** Seller states good/excellent condition, photos show clean part
- **Yellow:** Vague description, no photos, or unclear condition
- **Red:** Mentions wear/scratches but functional

Never auto-exclude yellow or red -- present all to the user for final decision.

## Important Notes

- Only used parts, never new
- All prices in EUR (converted automatically)
- Shipping destination: Athens, Greece 15562
- Flag listings where shipping > 50% of part price
- EU sellers = no customs. UK = customs warning
- Missing .env keys will raise exceptions -- no fallbacks
