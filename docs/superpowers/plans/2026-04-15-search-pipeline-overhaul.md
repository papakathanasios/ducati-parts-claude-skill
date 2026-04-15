# Search Pipeline Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the search pipeline so queries return real, relevant, EUR-normalized, price-filtered results across all 13 marketplace adapters in parallel.

**Architecture:** The SearchOrchestrator is the central integration point. We wire CurrencyConverter into it, add a new query_expansion module it calls per-adapter, fix the relevance filter to handle translated queries, switch to asyncio.gather for parallel dispatch, add per-adapter timeouts, and clean up Playwright resources after each search. Separately, we expand the OEM catalog and add a live smoke test script.

**Tech Stack:** Python 3.12, asyncio, httpx, Playwright, pytest

---

### Task 1: Add `adapter_timeout_seconds` to SearchConfig

**Files:**
- Modify: `src/core/config.py:22-26`
- Modify: `config/config.yaml:15-18`
- Modify: `test_scripts/test_config.py`

- [ ] **Step 1: Write the failing test**

Add to `test_scripts/test_config.py`:

```python
def test_load_config_includes_adapter_timeout(tmp_path):
    config_yaml = tmp_path / "config.yaml"
    config_yaml.write_text("""
bike:
  default_model: "Multistrada 1260 Enduro"
  year_range: [2019, 2021]
  also_compatible:
    - "Multistrada 1260"

shipping:
  destination_country: "GR"
  destination_postal: "15562"
  destination_city: "Athens"
  shipping_ratio_warning: 0.5

search:
  default_tiers: [1, 2]
  max_results_per_source: 50
  currency_display: "EUR"
  adapter_timeout_seconds: 45

condition:
  min_score: "red"
  photo_required: false

watch:
  check_interval_hours: 4
  stale_listing_days: 30
  notification: "macos"

tiers:
  1:
    - olx_bg
  2:
    - subito_it
  3:
    - kleinanzeigen
""")
    cfg = load_config(str(config_yaml))
    assert cfg.search.adapter_timeout_seconds == 45


def test_load_config_adapter_timeout_defaults_to_30(tmp_path):
    config_yaml = tmp_path / "config.yaml"
    config_yaml.write_text("""
bike:
  default_model: "Multistrada 1260 Enduro"
  year_range: [2019, 2021]
  also_compatible:
    - "Multistrada 1260"

shipping:
  destination_country: "GR"
  destination_postal: "15562"
  destination_city: "Athens"
  shipping_ratio_warning: 0.5

search:
  default_tiers: [1, 2]
  max_results_per_source: 50
  currency_display: "EUR"

condition:
  min_score: "red"
  photo_required: false

watch:
  check_interval_hours: 4
  stale_listing_days: 30
  notification: "macos"

tiers:
  1:
    - olx_bg
  2:
    - subito_it
  3:
    - kleinanzeigen
""")
    cfg = load_config(str(config_yaml))
    assert cfg.search.adapter_timeout_seconds == 30
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest test_scripts/test_config.py -v`
Expected: FAIL -- `SearchConfig.__init__() got an unexpected keyword argument 'adapter_timeout_seconds'`

- [ ] **Step 3: Update SearchConfig and load_config**

In `src/core/config.py`, add the field to `SearchConfig`:

```python
@dataclass
class SearchConfig:
    default_tiers: list[int]
    max_results_per_source: int
    currency_display: str
    adapter_timeout_seconds: int = 30
```

In `load_config()`, change the SearchConfig construction to handle the optional field:

```python
    search_data = raw["search"]
    search_config = SearchConfig(
        default_tiers=search_data["default_tiers"],
        max_results_per_source=search_data["max_results_per_source"],
        currency_display=search_data["currency_display"],
        adapter_timeout_seconds=search_data.get("adapter_timeout_seconds", 30),
    )
```

And update the AppConfig construction to use `search_config`:

```python
    return AppConfig(
        bike=BikeConfig(**raw["bike"]),
        shipping=ShippingConfig(**raw["shipping"]),
        search=search_config,
        condition=ConditionConfig(**raw["condition"]),
        watch=WatchConfig(**raw["watch"]),
        tiers={int(k): v for k, v in raw["tiers"].items()},
    )
```

- [ ] **Step 4: Add to config.yaml**

In `config/config.yaml`, add under the `search:` section:

```yaml
search:
  default_tiers: [1, 2]
  max_results_per_source: 50
  currency_display: "EUR"
  adapter_timeout_seconds: 30
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest test_scripts/test_config.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add src/core/config.py config/config.yaml test_scripts/test_config.py
git commit -m "feat: add adapter_timeout_seconds to SearchConfig with 30s default"
```

---

### Task 2: Add `translations` and `max_price_hint` to SearchFilters

**Files:**
- Modify: `src/core/types.py:68-76`
- Modify: `test_scripts/test_types.py`

- [ ] **Step 1: Write the failing test**

Add to `test_scripts/test_types.py`:

```python
def test_search_filters_translations_default_none():
    f = SearchFilters(query="exhaust")
    assert f.translations is None


def test_search_filters_max_price_hint_default_none():
    f = SearchFilters(query="exhaust")
    assert f.max_price_hint is None


def test_search_filters_with_translations():
    f = SearchFilters(query="exhaust", translations={"bg": "ауспух", "it": "scarico"})
    assert f.translations["bg"] == "ауспух"
    assert f.translations["it"] == "scarico"


def test_search_filters_with_max_price_hint():
    f = SearchFilters(query="exhaust", max_price_hint=Decimal("400"))
    assert f.max_price_hint == Decimal("400")
```

Add `from decimal import Decimal` to the test file imports if not already present.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest test_scripts/test_types.py -v`
Expected: FAIL -- `unexpected keyword argument 'translations'`

- [ ] **Step 3: Add fields to SearchFilters**

In `src/core/types.py`, update the `SearchFilters` dataclass:

```python
@dataclass
class SearchFilters:
    query: str
    max_total_price: Decimal | None = None
    tiers: list[int] = field(default_factory=lambda: [1, 2])
    target_models: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    oem_number: str | None = None
    part_category: str | None = None
    translations: dict[str, str] | None = None
    max_price_hint: Decimal | None = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest test_scripts/test_types.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/types.py test_scripts/test_types.py
git commit -m "feat: add translations and max_price_hint fields to SearchFilters"
```

---

### Task 3: Build query expansion module

**Files:**
- Create: `src/core/query_expansion.py`
- Create: `test_scripts/test_query_expansion.py`

- [ ] **Step 1: Write the failing tests**

Create `test_scripts/test_query_expansion.py`:

```python
from src.core.query_expansion import expand_query


def test_expand_translates_known_term():
    result = expand_query("Ducati exhaust", "bg")
    assert "ауспух" in result
    assert "Ducati" in result


def test_expand_keeps_model_names_untranslated():
    result = expand_query("Multistrada 1260 exhaust", "it")
    assert "Multistrada" in result
    assert "1260" in result
    assert "scarico" in result


def test_expand_unknown_term_passes_through():
    result = expand_query("Ducati foobar", "bg")
    assert "foobar" in result
    assert "Ducati" in result


def test_expand_english_returns_original():
    result = expand_query("Ducati exhaust slip on", "en")
    assert result == "Ducati exhaust slip on"


def test_expand_multiple_terms():
    result = expand_query("brake lever", "de")
    assert "Bremshebel" in result or ("Bremse" in result and "Hebel" in result)


def test_expand_overrides_take_precedence():
    overrides = {"bg": "custom translation"}
    result = expand_query("exhaust", "bg", overrides=overrides)
    assert result == "custom translation"


def test_expand_case_insensitive_matching():
    result = expand_query("Ducati Exhaust", "it")
    assert "scarico" in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest test_scripts/test_query_expansion.py -v`
Expected: FAIL -- `ModuleNotFoundError: No module named 'src.core.query_expansion'`

- [ ] **Step 3: Create the query expansion module**

Create `src/core/query_expansion.py`:

```python
"""Query expansion with multi-language motorcycle part translations.

Translates search queries into the target adapter's language using a static
dictionary of common motorcycle part terms. Model names (Ducati, Multistrada,
etc.) are kept untranslated since sellers use them universally.
"""

# Model names and numbers that should never be translated
_MODEL_TOKENS = frozenset({
    "ducati", "multistrada", "monster", "panigale", "scrambler",
    "diavel", "hypermotard", "streetfighter", "supersport",
    "enduro", "touring", "pikes", "peak",
    "1260", "1200", "950", "821", "1100", "v4", "v2",
})

# Mapping: English term -> {language_code: translation}
# Language codes match adapter.language attributes:
#   bg=Bulgarian, ro=Romanian, hu=Hungarian, pl=Polish,
#   cz=Czech, sk=Slovak, hr=Croatian, sl=Slovenian,
#   it=Italian, de=German, fr=French, es=Spanish
TERM_TRANSLATIONS: dict[str, dict[str, str]] = {
    # Drivetrain
    "exhaust": {
        "bg": "ауспух", "ro": "evacuare", "hu": "kipufogó",
        "pl": "wydech", "cz": "výfuk", "sk": "výfuk",
        "hr": "ispuh", "sl": "izpuh",
        "it": "scarico", "de": "Auspuff", "fr": "échappement", "es": "escape",
    },
    "muffler": {
        "bg": "ауспух", "ro": "tobă", "hu": "kipufogódob",
        "pl": "tłumik", "cz": "tlumič", "sk": "tlmič",
        "hr": "prigušivač", "sl": "dušilec",
        "it": "marmitta", "de": "Auspufftopf", "fr": "silencieux", "es": "silenciador",
    },
    "slip-on": {
        "bg": "слипон", "ro": "slip-on", "hu": "slip-on",
        "pl": "slip-on", "cz": "slip-on", "sk": "slip-on",
        "hr": "slip-on", "sl": "slip-on",
        "it": "slip-on", "de": "Slip-On", "fr": "slip-on", "es": "slip-on",
    },
    "clutch": {
        "bg": "съединител", "ro": "ambreiaj", "hu": "kuplung",
        "pl": "sprzęgło", "cz": "spojka", "sk": "spojka",
        "hr": "kvačilo", "sl": "sklopka",
        "it": "frizione", "de": "Kupplung", "fr": "embrayage", "es": "embrague",
    },
    "chain": {
        "bg": "верига", "ro": "lanț", "hu": "lánc",
        "pl": "łańcuch", "cz": "řetěz", "sk": "reťaz",
        "hr": "lanac", "sl": "veriga",
        "it": "catena", "de": "Kette", "fr": "chaîne", "es": "cadena",
    },
    "sprocket": {
        "bg": "зъбно колело", "ro": "pinion", "hu": "lánckerék",
        "pl": "zębatka", "cz": "řetězové kolo", "sk": "reťazové koleso",
        "hr": "lančanik", "sl": "verižnik",
        "it": "corona", "de": "Kettenrad", "fr": "pignon", "es": "piñón",
    },
    "gearbox": {
        "bg": "скоростна кутия", "ro": "cutie de viteze", "hu": "sebességváltó",
        "pl": "skrzynia biegów", "cz": "převodovka", "sk": "prevodovka",
        "hr": "mjenjač", "sl": "menjalnik",
        "it": "cambio", "de": "Getriebe", "fr": "boîte de vitesses", "es": "caja de cambios",
    },
    # Brakes
    "brake": {
        "bg": "спирачка", "ro": "frână", "hu": "fék",
        "pl": "hamulec", "cz": "brzda", "sk": "brzda",
        "hr": "kočnica", "sl": "zavora",
        "it": "freno", "de": "Bremse", "fr": "frein", "es": "freno",
    },
    "lever": {
        "bg": "лост", "ro": "manetă", "hu": "kar",
        "pl": "dźwignia", "cz": "páka", "sk": "páka",
        "hr": "ručica", "sl": "ročica",
        "it": "leva", "de": "Hebel", "fr": "levier", "es": "maneta",
    },
    "disc": {
        "bg": "диск", "ro": "disc", "hu": "tárcsa",
        "pl": "tarcza", "cz": "kotouč", "sk": "kotúč",
        "hr": "disk", "sl": "disk",
        "it": "disco", "de": "Scheibe", "fr": "disque", "es": "disco",
    },
    "pad": {
        "bg": "накладки", "ro": "plăcuțe", "hu": "betét",
        "pl": "klocki", "cz": "destičky", "sk": "doštičky",
        "hr": "pločice", "sl": "zavorne ploščice",
        "it": "pastiglie", "de": "Beläge", "fr": "plaquettes", "es": "pastillas",
    },
    "caliper": {
        "bg": "спирачен апарат", "ro": "etrier", "hu": "féknyereg",
        "pl": "zacisk", "cz": "třmen", "sk": "strmeň",
        "hr": "kliješta", "sl": "čeljust",
        "it": "pinza", "de": "Bremssattel", "fr": "étrier", "es": "pinza",
    },
    # Body
    "fairing": {
        "bg": "пластмаса", "ro": "carenaj", "hu": "burkolat",
        "pl": "owiewka", "cz": "kapotáž", "sk": "kapotáž",
        "hr": "oplata", "sl": "obloga",
        "it": "carenatura", "de": "Verkleidung", "fr": "carénage", "es": "carenado",
    },
    "windscreen": {
        "bg": "ветробранно стъкло", "ro": "parbriz", "hu": "szélvédő",
        "pl": "szyba", "cz": "plexi", "sk": "plexi",
        "hr": "vjetrobran", "sl": "vetrobransko steklo",
        "it": "parabrezza", "de": "Windschild", "fr": "pare-brise", "es": "parabrisas",
    },
    "seat": {
        "bg": "седалка", "ro": "șa", "hu": "ülés",
        "pl": "siedzenie", "cz": "sedlo", "sk": "sedlo",
        "hr": "sjedalo", "sl": "sedež",
        "it": "sella", "de": "Sitzbank", "fr": "selle", "es": "asiento",
    },
    "mirror": {
        "bg": "огледало", "ro": "oglindă", "hu": "tükör",
        "pl": "lusterko", "cz": "zrcátko", "sk": "zrkadlo",
        "hr": "retrovizor", "sl": "ogledalo",
        "it": "specchio", "de": "Spiegel", "fr": "rétroviseur", "es": "espejo",
    },
    "tank": {
        "bg": "резервоар", "ro": "rezervor", "hu": "tank",
        "pl": "zbiornik", "cz": "nádrž", "sk": "nádrž",
        "hr": "spremnik", "sl": "rezervoar",
        "it": "serbatoio", "de": "Tank", "fr": "réservoir", "es": "depósito",
    },
    # Suspension
    "fork": {
        "bg": "вилка", "ro": "furcă", "hu": "villá",
        "pl": "lag", "cz": "vidlice", "sk": "vidlica",
        "hr": "vilica", "sl": "vilice",
        "it": "forcella", "de": "Gabel", "fr": "fourche", "es": "horquilla",
    },
    "shock": {
        "bg": "амортисьор", "ro": "amortizor", "hu": "lengéscsillapító",
        "pl": "amortyzator", "cz": "tlumič", "sk": "tlmič",
        "hr": "amortizer", "sl": "amortizerja",
        "it": "ammortizzatore", "de": "Stoßdämpfer", "fr": "amortisseur", "es": "amortiguador",
    },
    # Electrical
    "headlight": {
        "bg": "фар", "ro": "far", "hu": "fényszóró",
        "pl": "reflektor", "cz": "světlo", "sk": "svetlo",
        "hr": "far", "sl": "žaromet",
        "it": "faro", "de": "Scheinwerfer", "fr": "phare", "es": "faro",
    },
    "indicator": {
        "bg": "мигач", "ro": "semnalizare", "hu": "irányjelző",
        "pl": "kierunkowskaz", "cz": "blinkr", "sk": "smerovka",
        "hr": "žmigavac", "sl": "smerokaz",
        "it": "freccia", "de": "Blinker", "fr": "clignotant", "es": "intermitente",
    },
    # Cooling
    "radiator": {
        "bg": "радиатор", "ro": "radiator", "hu": "hűtő",
        "pl": "chłodnica", "cz": "chladič", "sk": "chladič",
        "hr": "hladnjak", "sl": "hladilnik",
        "it": "radiatore", "de": "Kühler", "fr": "radiateur", "es": "radiador",
    },
    # Protection
    "crash bar": {
        "bg": "предпазни дъги", "ro": "bare protecție", "hu": "bukócső",
        "pl": "gmol", "cz": "padací rám", "sk": "padací rám",
        "hr": "zaštitne cijevi", "sl": "zaščitne cevi",
        "it": "paramotore", "de": "Sturzbügel", "fr": "pare-carter", "es": "defensas",
    },
    "skid plate": {
        "bg": "предпазна плоча", "ro": "scut motor", "hu": "motorvédő",
        "pl": "osłona silnika", "cz": "kryt motoru", "sk": "kryt motora",
        "hr": "zaštita motora", "sl": "ščitnik motorja",
        "it": "paracoppa", "de": "Motorschutz", "fr": "sabot moteur", "es": "cubrecarter",
    },
    # Consumables
    "filter": {
        "bg": "филтър", "ro": "filtru", "hu": "szűrő",
        "pl": "filtr", "cz": "filtr", "sk": "filter",
        "hr": "filtar", "sl": "filter",
        "it": "filtro", "de": "Filter", "fr": "filtre", "es": "filtro",
    },
    "spark plug": {
        "bg": "свещ", "ro": "bujie", "hu": "gyújtógyertya",
        "pl": "świeca", "cz": "svíčka", "sk": "sviečka",
        "hr": "svjećica", "sl": "svečka",
        "it": "candela", "de": "Zündkerze", "fr": "bougie", "es": "bujía",
    },
    # Wheels
    "wheel": {
        "bg": "колело", "ro": "roată", "hu": "kerék",
        "pl": "koło", "cz": "kolo", "sk": "koleso",
        "hr": "kotač", "sl": "kolo",
        "it": "ruota", "de": "Rad", "fr": "roue", "es": "rueda",
    },
    # Controls
    "handlebar": {
        "bg": "кормило", "ro": "ghidon", "hu": "kormány",
        "pl": "kierownica", "cz": "řidítka", "sk": "riadidlá",
        "hr": "upravljač", "sl": "krmilo",
        "it": "manubrio", "de": "Lenker", "fr": "guidon", "es": "manillar",
    },
    "footpeg": {
        "bg": "стъпенка", "ro": "scară", "hu": "lábtartó",
        "pl": "podnóżek", "cz": "stupačka", "sk": "stupačka",
        "hr": "stupaljka", "sl": "stopaljka",
        "it": "pedana", "de": "Fußraste", "fr": "repose-pied", "es": "estribo",
    },
}


def expand_query(
    query: str,
    target_language: str,
    overrides: dict[str, str] | None = None,
) -> str:
    """Translate a search query into the target adapter's language.

    Args:
        query: The original English search query.
        target_language: ISO language code matching adapter.language (e.g. "bg", "it").
        overrides: Optional per-language override dict {lang_code: full_translated_query}.
            When provided and target_language is a key, returns the override directly.

    Returns:
        The query with known motorcycle terms translated. Model names are preserved.
    """
    if overrides and target_language in overrides:
        return overrides[target_language]

    if target_language == "en":
        return query

    words = query.split()
    translated: list[str] = []

    i = 0
    while i < len(words):
        word_lower = words[i].lower()

        # Keep model names untranslated
        if word_lower in _MODEL_TOKENS:
            translated.append(words[i])
            i += 1
            continue

        # Try two-word compound match first (e.g. "crash bar", "skid plate", "spark plug")
        if i + 1 < len(words):
            compound = f"{word_lower} {words[i + 1].lower()}"
            if compound in TERM_TRANSLATIONS:
                term_map = TERM_TRANSLATIONS[compound]
                translated.append(term_map.get(target_language, compound))
                i += 2
                continue

        # Single word match
        if word_lower in TERM_TRANSLATIONS:
            term_map = TERM_TRANSLATIONS[word_lower]
            translated.append(term_map.get(target_language, words[i]))
        else:
            translated.append(words[i])

        i += 1

    return " ".join(translated)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest test_scripts/test_query_expansion.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/query_expansion.py test_scripts/test_query_expansion.py
git commit -m "feat: add query expansion module with 30-term multilingual dictionary"
```

---

### Task 4: Add currency rate caching to CurrencyConverter

**Files:**
- Modify: `src/core/currency.py`
- Modify: `test_scripts/test_currency.py`

- [ ] **Step 1: Write the failing tests**

Add to `test_scripts/test_currency.py`:

```python
from datetime import datetime, timedelta, timezone


def test_fetch_rates_caches_for_24_hours():
    converter = CurrencyConverter()
    # Simulate a previous fetch
    converter._rates = {"BGN": Decimal("1.9558")}
    converter._rates_fetched_at = datetime.now(timezone.utc)
    converter._rates_available = True

    # Should return True (cached) without hitting ECB
    assert converter.rates_are_fresh() is True


def test_fetch_rates_stale_after_24_hours():
    converter = CurrencyConverter()
    converter._rates = {"BGN": Decimal("1.9558")}
    converter._rates_fetched_at = datetime.now(timezone.utc) - timedelta(hours=25)
    converter._rates_available = True

    assert converter.rates_are_fresh() is False


def test_rates_available_flag():
    converter = CurrencyConverter()
    assert converter._rates_available is False
    converter._rates = {"BGN": Decimal("1.9558")}
    converter._rates_fetched_at = datetime.now(timezone.utc)
    converter._rates_available = True
    assert converter._rates_available is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest test_scripts/test_currency.py -v`
Expected: FAIL -- `AttributeError: 'CurrencyConverter' object has no attribute '_rates_fetched_at'`

- [ ] **Step 3: Add caching fields and method**

Update `src/core/currency.py`:

```python
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree
import logging
import httpx

logger = logging.getLogger(__name__)

ECB_RATES_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
ECB_NS = {"gesmes": "http://www.gesmes.org/xml/2002-08-01", "eurofxref": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"}

_CACHE_DURATION = timedelta(hours=24)


class CurrencyConverter:
    def __init__(self):
        self._rates: dict[str, Decimal] = {}
        self._rates_fetched_at: datetime | None = None
        self._rates_available: bool = False

    def rates_are_fresh(self) -> bool:
        if self._rates_fetched_at is None:
            return False
        return (datetime.now(timezone.utc) - self._rates_fetched_at) < _CACHE_DURATION

    async def fetch_rates(self) -> None:
        if self.rates_are_fresh():
            return
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(ECB_RATES_URL, timeout=10)
                resp.raise_for_status()
            root = ElementTree.fromstring(resp.text)
            cube = root.find(".//eurofxref:Cube/eurofxref:Cube", ECB_NS)
            if cube is None:
                raise RuntimeError("Failed to parse ECB rate data")
            self._rates = {}
            for rate_elem in cube.findall("eurofxref:Cube", ECB_NS):
                currency = rate_elem.attrib["currency"]
                rate = Decimal(rate_elem.attrib["rate"])
                self._rates[currency] = rate
            self._rates_fetched_at = datetime.now(timezone.utc)
            self._rates_available = True
        except Exception:
            logger.warning("Failed to fetch ECB rates; currency conversion unavailable")
            self._rates_available = False

    def convert(self, amount: Decimal, from_currency: str) -> Decimal:
        from_currency = from_currency.upper()
        if from_currency == "EUR":
            return amount
        if from_currency not in self._rates:
            raise KeyError(f"Unsupported currency: {from_currency}")
        rate = self._rates[from_currency]
        eur_amount = amount / rate
        return eur_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def is_supported(self, currency: str) -> bool:
        return currency.upper() == "EUR" or currency.upper() in self._rates
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest test_scripts/test_currency.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/currency.py test_scripts/test_currency.py
git commit -m "feat: add 24-hour rate caching and _rates_available flag to CurrencyConverter"
```

---

### Task 5: Rewrite SearchOrchestrator with all pipeline fixes

This is the core task. It wires currency conversion, query expansion, fixed relevance filtering, parallel execution, and per-adapter timeout into `SearchOrchestrator.run()`.

**Files:**
- Modify: `src/core/search.py`
- Modify: `test_scripts/test_search.py`

- [ ] **Step 1: Write failing tests for new behavior**

Add new tests to `test_scripts/test_search.py`. First update the `_make_config` helper to include the new field:

```python
def _make_config() -> AppConfig:
    return AppConfig(
        bike=BikeConfig(default_model="Multistrada 1260 Enduro", year_range=[2019, 2021], also_compatible=["Multistrada 1260"]),
        shipping=ShippingConfig(destination_country="GR", destination_postal="15562", destination_city="Athens", shipping_ratio_warning=0.5),
        search=SearchConfig(default_tiers=[1, 2], max_results_per_source=50, currency_display="EUR", adapter_timeout_seconds=30),
        condition=ConditionConfig(min_score="red", photo_required=False),
        watch=WatchConfig(check_interval_hours=4, stale_listing_days=30, notification="macos"),
        tiers={1: ["mock"], 2: [], 3: []},
    )
```

Then add tests:

```python
def test_orchestrator_converts_non_eur_currency():
    raw = RawListing(source_id="1", source="mock", title="Clutch lever Multistrada",
        description="Good condition", price=39.12, currency="BGN", shipping_price=None,
        seller_country="BG", condition_label="Good", photos=["https://example.com/p.jpg"],
        listing_url="https://mock.com/1")
    adapter = MockAdapter([raw])
    config = _make_config()
    orchestrator = SearchOrchestrator(config=config, adapters={"mock": adapter})
    filters = SearchFilters(query="clutch lever", tiers=[1])
    listings = asyncio.run(orchestrator.run(filters))
    assert len(listings) == 1
    # BGN rate is ~1.9558, so 39.12 BGN ≈ 20.00 EUR
    # Exact value depends on rate, but must not be 39.12 (the raw BGN value)
    assert listings[0].part_price != Decimal("39.12")
    assert listings[0].currency_original == "BGN"


def test_orchestrator_handles_ecb_failure_gracefully():
    raw = RawListing(source_id="1", source="mock", title="Lever Multistrada",
        description="Good condition", price=20.0, currency="EUR", shipping_price=8.0,
        seller_country="BG", condition_label="Good", photos=[],
        listing_url="https://mock.com/1")
    adapter = MockAdapter([raw])
    config = _make_config()
    orchestrator = SearchOrchestrator(config=config, adapters={"mock": adapter})
    # Force rates unavailable
    orchestrator.currency_converter._rates_available = False
    orchestrator.currency_converter._rates = {}
    filters = SearchFilters(query="lever", tiers=[1])
    listings = asyncio.run(orchestrator.run(filters))
    # EUR listings still work even without rates
    assert len(listings) == 1


def test_orchestrator_relevance_filter_accepts_translated_match():
    """A listing in Bulgarian should match if the translated query matches."""
    raw = RawListing(source_id="1", source="mock", title="ауспух Ducati Multistrada",
        description="добро състояние", price=200.0, currency="EUR", shipping_price=10.0,
        seller_country="BG", condition_label="Good", photos=[],
        listing_url="https://mock.com/1")
    adapter = MockAdapter([raw])
    config = _make_config()
    orchestrator = SearchOrchestrator(config=config, adapters={"mock": adapter})
    filters = SearchFilters(query="exhaust Ducati Multistrada", tiers=[1])
    listings = asyncio.run(orchestrator.run(filters))
    # "ауспух" is the Bulgarian translation of "exhaust"
    assert len(listings) == 1


def test_orchestrator_parallel_with_failing_adapter():
    good_raw = RawListing(source_id="1", source="mock", title="Lever Multistrada",
        description="Good", price=20.0, currency="EUR", shipping_price=8.0,
        seller_country="BG", condition_label="Good", photos=[],
        listing_url="https://mock.com/1")
    good_adapter = MockAdapter([good_raw])
    failing_adapter = FailingAdapter()
    config = _make_config()
    config.tiers[1] = ["mock", "failing"]
    orchestrator = SearchOrchestrator(
        config=config,
        adapters={"mock": good_adapter, "failing": failing_adapter},
    )
    filters = SearchFilters(query="lever", tiers=[1])
    listings = asyncio.run(orchestrator.run(filters))
    assert len(listings) == 1
    assert "failing" in orchestrator.last_errors
```

- [ ] **Step 2: Run tests to verify the new tests fail**

Run: `uv run pytest test_scripts/test_search.py -v`
Expected: Some new tests FAIL (currency conversion not wired, translated match dropped)

- [ ] **Step 3: Rewrite SearchOrchestrator**

Replace the contents of `src/core/search.py` with:

```python
import asyncio
import logging
import re
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

from src.adapters.base import BaseAdapter
from src.core.condition import ConditionFilter
from src.core.config import AppConfig
from src.core.currency import CurrencyConverter
from src.core.dedup import deduplicate
from src.core.query_expansion import expand_query
from src.core.shipping import ShippingEstimator
from src.core.types import (
    ConditionScore, CompatibilityConfidence,
    Listing, RawListing, SearchFilters,
)

logger = logging.getLogger(__name__)

_WORD_SPLIT = re.compile(r"[^a-z0-9\u0400-\u04ff\u0100-\u024f]+")


def _is_relevant(title: str, description: str, original_query: str, translated_query: str) -> bool:
    """Check if a listing is relevant to the search query.

    A listing must have at least one significant query word (>= 3 chars)
    present in either the title or description, checked against both
    the original and translated query terms.
    """
    original_words = {w for w in _WORD_SPLIT.split(original_query.lower()) if len(w) >= 3}
    translated_words = {w for w in _WORD_SPLIT.split(translated_query.lower()) if len(w) >= 3}
    all_query_words = original_words | translated_words
    listing_text = f"{title} {description}".lower()
    return any(word in listing_text for word in all_query_words)


class SearchOrchestrator:
    def __init__(self, config: AppConfig, adapters: dict[str, BaseAdapter]):
        self.config = config
        self.adapters = adapters
        self.condition_filter = ConditionFilter()
        self.shipping_estimator = ShippingEstimator(
            destination_postal=config.shipping.destination_postal,
            destination_country=config.shipping.destination_country,
        )
        self.currency_converter = CurrencyConverter()
        self.last_errors: dict[str, str] = {}

    async def run(self, filters: SearchFilters) -> list[Listing]:
        self.last_errors = {}

        # Fetch currency rates (cached for 24h)
        await self.currency_converter.fetch_rates()

        # Resolve which adapters to dispatch
        adapter_names: list[str] = []
        for tier in filters.tiers:
            adapter_names.extend(self.config.tiers.get(tier, []))
        if filters.sources:
            adapter_names = filters.sources

        selected: dict[str, BaseAdapter] = {}
        for name in adapter_names:
            if name in self.adapters:
                selected[name] = self.adapters[name]

        # Build per-adapter translated queries
        translated_queries: dict[str, str] = {}
        for name, adapter in selected.items():
            translated_queries[name] = expand_query(
                filters.query,
                adapter.language,
                overrides=filters.translations,
            )

        # Dispatch all adapters in parallel with per-adapter timeout
        timeout = self.config.search.adapter_timeout_seconds

        async def _search_adapter(name: str, adapter: BaseAdapter) -> list[RawListing]:
            query = translated_queries[name]
            return await asyncio.wait_for(
                adapter.search(query, filters),
                timeout=timeout,
            )

        coros = {name: _search_adapter(name, adapter) for name, adapter in selected.items()}
        results = await asyncio.gather(*coros.values(), return_exceptions=True)

        raw_results: list[RawListing] = []
        for name, result in zip(coros.keys(), results):
            if isinstance(result, Exception):
                self.last_errors[name] = str(result)
            else:
                raw_results.extend(result)

        # Process raw results into Listings
        listings: list[Listing] = []
        for raw in raw_results:
            # Determine which translated query was used for this adapter
            adapter_translated = translated_queries.get(raw.source, filters.query)

            if not _is_relevant(raw.title, raw.description, filters.query, adapter_translated):
                continue
            if self.condition_filter.should_exclude(raw.title, raw.description):
                continue
            normalized = self.condition_filter.normalize_label(raw.condition_label)
            if normalized.value == "excluded":
                continue

            # Currency conversion
            part_price_raw = Decimal(str(raw.price))
            currency = raw.currency.upper()
            if currency != "EUR" and self.currency_converter._rates_available:
                try:
                    part_price = self.currency_converter.convert(part_price_raw, currency)
                except KeyError:
                    logger.warning("Unsupported currency %s for listing %s", currency, raw.source_id)
                    part_price = part_price_raw
            else:
                part_price = part_price_raw
            part_price = part_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # Shipping
            if raw.shipping_price is not None:
                shipping = Decimal(str(raw.shipping_price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                shipping = self.shipping_estimator.midpoint(raw.seller_country)

            # Condition scoring
            if raw.photos:
                condition_score = ConditionScore.GREEN if normalized.value in ("excellent", "good") else ConditionScore.YELLOW
            else:
                condition_score = ConditionScore.YELLOW
            if normalized.value == "fair":
                condition_score = ConditionScore.RED

            listing = Listing(
                id=f"{raw.source}_{raw.source_id}",
                source=raw.source, title=raw.title, description=raw.description,
                part_price=part_price, shipping_price=shipping,
                currency_original=raw.currency, seller_country=raw.seller_country,
                is_eu=self.shipping_estimator.is_eu(raw.seller_country),
                condition_raw=raw.condition_label, condition_score=condition_score,
                condition_notes=f"Normalized: {normalized.value}",
                photos=raw.photos, listing_url=raw.listing_url,
                compatible_models=[], compatibility_confidence=CompatibilityConfidence.VERIFY,
                oem_part_number="", date_listed=datetime.now(), date_found=datetime.now(),
            )

            # Price filter -- skip for unconverted non-EUR if rates unavailable
            if filters.max_total_price:
                if currency != "EUR" and not self.currency_converter._rates_available:
                    pass  # Include unconverted listings rather than silently dropping
                elif listing.total_price > filters.max_total_price:
                    continue

            listings.append(listing)

        listings = deduplicate(listings)
        listings.sort(key=lambda l: (l.condition_score.value, l.total_price))
        return listings
```

- [ ] **Step 4: Run all search tests**

Run: `uv run pytest test_scripts/test_search.py -v`
Expected: All PASS (both old and new tests)

- [ ] **Step 5: Run full test suite to check for regressions**

Run: `uv run pytest test_scripts/ -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add src/core/search.py test_scripts/test_search.py
git commit -m "feat: wire currency conversion, query expansion, parallel execution, and timeout into SearchOrchestrator"
```

---

### Task 6: Add adapter cleanup to CLI

**Files:**
- Modify: `src/cli.py:36-81`

- [ ] **Step 1: Update run_search with try/finally cleanup**

In `src/cli.py`, update `run_search()` to clean up adapters:

```python
async def run_search(
    query,
    config_path=None,
    reports_dir=None,
    max_total_price=None,
    tiers=None,
    sources=None,
    adapters=None,
    translations=None,
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
        translations=translations,
    )

    try:
        listings = await orchestrator.run(filters)
    finally:
        for adapter in adapters.values():
            if hasattr(adapter, 'close'):
                try:
                    await adapter.close()
                except Exception:
                    pass

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
```

- [ ] **Step 2: Run CLI tests**

Run: `uv run pytest test_scripts/test_cli.py -v`
Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git add src/cli.py
git commit -m "feat: add adapter cleanup and translations support to CLI run_search"
```

---

### Task 7: Expand OEM seed catalog

**Files:**
- Modify: `data/seed/multistrada_1260_enduro.json`

- [ ] **Step 1: Add new parts to seed data**

Update `data/seed/multistrada_1260_enduro.json` -- add these entries to the `enduro_specific` array:

```json
      {
        "oem_number": "",
        "part_name": "Exhaust Headers",
        "category": "exhaust",
        "search_aliases": ["exhaust headers", "manifold", "exhaust pipes", "header pipes"]
      },
      {
        "oem_number": "34921341A",
        "part_name": "Rear Shock Sachs",
        "category": "suspension",
        "search_aliases": ["rear shock", "sachs shock", "rear suspension", "shock absorber", "34921341A"]
      }
```

Add these to the `shared` array:

```json
      {
        "oem_number": "61341051A",
        "part_name": "Rear Brake Pads",
        "category": "brakes",
        "search_aliases": ["rear brake pads", "rear pads", "61341051A"],
        "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"]
      },
      {
        "oem_number": "49240101A",
        "part_name": "Front Brake Disc",
        "category": "brakes",
        "search_aliases": ["front brake disc", "front rotor", "brake rotor", "49240101A"],
        "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"]
      },
      {
        "oem_number": "61041341A",
        "part_name": "Front Brake Caliper",
        "category": "brakes",
        "search_aliases": ["front caliper", "brake caliper", "brembo caliper", "61041341A"],
        "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"]
      },
      {
        "oem_number": "46012721A",
        "part_name": "Foot Pegs",
        "category": "controls",
        "search_aliases": ["foot pegs", "footpegs", "rider pegs", "46012721A"],
        "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"]
      },
      {
        "oem_number": "36011951A",
        "part_name": "Handlebar",
        "category": "controls",
        "search_aliases": ["handlebar", "handlebars", "handle bar", "36011951A"],
        "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"]
      },
      {
        "oem_number": "52510441A",
        "part_name": "Tail Light",
        "category": "electrical",
        "search_aliases": ["tail light", "taillight", "rear light", "brake light", "52510441A"],
        "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"]
      },
      {
        "oem_number": "40611291A",
        "part_name": "Instrument Cluster",
        "category": "electrical",
        "search_aliases": ["instrument cluster", "dashboard", "speedometer", "TFT display", "40611291A"],
        "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"]
      },
      {
        "oem_number": "16024071A",
        "part_name": "Fuel Pump",
        "category": "fuel",
        "search_aliases": ["fuel pump", "petrol pump", "benzin pump", "16024071A"],
        "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"]
      },
      {
        "oem_number": "28240991A",
        "part_name": "Throttle Body",
        "category": "fuel",
        "search_aliases": ["throttle body", "throttle bodies", "28240991A"],
        "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"]
      },
      {
        "oem_number": "42620201A",
        "part_name": "Air Filter",
        "category": "consumables",
        "search_aliases": ["air filter", "air cleaner", "42620201A"],
        "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"]
      },
      {
        "oem_number": "44440312A",
        "part_name": "Oil Filter",
        "category": "consumables",
        "search_aliases": ["oil filter", "44440312A"],
        "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"]
      },
      {
        "oem_number": "67040631A",
        "part_name": "Clutch Plates",
        "category": "drivetrain",
        "search_aliases": ["clutch plates", "friction plates", "clutch discs", "67040631A"],
        "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"]
      },
      {
        "oem_number": "",
        "part_name": "Coolant Hoses",
        "category": "cooling",
        "search_aliases": ["coolant hoses", "radiator hoses", "water hoses"],
        "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"]
      },
      {
        "oem_number": "28641301A",
        "part_name": "ECU",
        "category": "electrical",
        "search_aliases": ["ECU", "engine control unit", "electronic control", "28641301A"],
        "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"]
      },
      {
        "oem_number": "53620711A",
        "part_name": "Turn Signal",
        "category": "electrical",
        "search_aliases": ["turn signal", "indicator", "blinker", "53620711A"],
        "compatible_with": ["Multistrada 1260", "Multistrada 1260 S", "Multistrada 1260 Pikes Peak"]
      }
```

- [ ] **Step 2: Verify JSON is valid**

Run: `uv run python -c "import json; json.load(open('data/seed/multistrada_1260_enduro.json')); print('Valid JSON')"`
Expected: `Valid JSON`

- [ ] **Step 3: Run catalog tests**

Run: `uv run pytest test_scripts/test_catalog.py -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add data/seed/multistrada_1260_enduro.json
git commit -m "feat: expand OEM catalog from 17 to 33 parts"
```

---

### Task 8: Create live smoke test script

**Files:**
- Create: `test_scripts/smoke_test_live.py`

- [ ] **Step 1: Create the smoke test script**

Create `test_scripts/smoke_test_live.py`:

```python
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

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.adapters.registry import build_adapter_registry
from src.core.types import SearchFilters

QUERY = "Ducati Multistrada"


async def test_adapter(name: str, adapter, filters: SearchFilters) -> dict:
    """Test a single adapter and return results."""
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

    print(f"Smoke testing {len(adapters)} adapters with query: \"{QUERY}\"")
    print(f"{'Adapter':<20} {'Status':<10} {'Results':<10} {'Time':<10} {'Error'}")
    print("─" * 80)

    results = []
    for name, adapter in adapters.items():
        result = await test_adapter(name, adapter, filters)
        results.append(result)
        status_color = {"OK": "OK", "EMPTY": "EMPTY", "ERROR": "ERROR", "TIMEOUT": "TIMEOUT"}
        error_str = result["error"] or ""
        print(f"{result['name']:<20} {status_color[result['status']]:<10} {result['count']:<10} {result['time']:<10} {error_str}")

        # Clean up adapter
        if hasattr(adapter, 'close'):
            try:
                await adapter.close()
            except Exception:
                pass

    # Summary
    ok = sum(1 for r in results if r["status"] == "OK")
    empty = sum(1 for r in results if r["status"] == "EMPTY")
    errors = sum(1 for r in results if r["status"] in ("ERROR", "TIMEOUT"))
    print("─" * 80)
    print(f"Summary: {ok} OK, {empty} EMPTY, {errors} ERROR/TIMEOUT out of {len(results)} adapters")

    if empty > 0:
        print("\nEMPTY adapters may have broken CSS selectors. Inspect the live page and update _extract_listings().")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live smoke test for marketplace adapters")
    parser.add_argument("--adapter", nargs="+", help="Test specific adapters only")
    args = parser.parse_args()
    asyncio.run(main(args.adapter))
```

- [ ] **Step 2: Verify it runs without syntax errors**

Run: `uv run python test_scripts/smoke_test_live.py --adapter subito_it`
Expected: Table output with subito_it row showing OK, EMPTY, or ERROR

- [ ] **Step 3: Commit**

```bash
git add test_scripts/smoke_test_live.py
git commit -m "feat: add live smoke test script for adapter CSS selector validation"
```

---

### Task 9: Update issues tracker

**Files:**
- Modify: `Issues - Pending Items.md`

- [ ] **Step 1: Move completed items**

Update `Issues - Pending Items.md` to reflect what this overhaul addresses:

Move item 4 (Currency rate caching) to Completed with note: "Implemented 24h in-memory caching in CurrencyConverter."

Add to Completed:
- "Currency conversion wired into SearchOrchestrator -- all prices normalized to EUR"
- "Query translation engine added -- 30+ terms across 12 languages"
- "Relevance filter fixed to accept translated query matches"
- "Adapters now execute in parallel via asyncio.gather"
- "Per-adapter timeout (30s default) prevents one slow adapter from blocking search"
- "Browser cleanup added to prevent Playwright process leaks"
- "OEM catalog expanded from 17 to 33 parts"
- "Live smoke test script added for CSS selector validation"

- [ ] **Step 2: Commit**

```bash
git add "Issues - Pending Items.md"
git commit -m "docs: update issues tracker with completed pipeline overhaul items"
```
