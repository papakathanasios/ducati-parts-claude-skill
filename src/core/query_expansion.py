"""Query expansion module for multilingual Ducati parts search.

Translates English motorcycle-part search terms into target languages
so that scrapers can query local-language marketplaces.
"""

from __future__ import annotations

# Ducati model names and numeric identifiers that must never be translated.
_MODEL_TOKENS: frozenset[str] = frozenset(
    {
        "ducati",
        "multistrada",
        "monster",
        "panigale",
        "scrambler",
        "diavel",
        "hypermotard",
        "streetfighter",
        "supersport",
        "enduro",
        "touring",
        "pikes",
        "peak",
        "1260",
        "1200",
        "950",
        "821",
        "1100",
        "v4",
        "v2",
    }
)

# ---------------------------------------------------------------------------
# Multilingual term dictionary
# Keys are lowercase English terms; values map ISO-639-1 codes to translations.
# ---------------------------------------------------------------------------
TERM_TRANSLATIONS: dict[str, dict[str, str]] = {
    "exhaust": {
        "bg": "ауспух",
        "ro": "evacuare",
        "hu": "kipufogó",
        "pl": "wydech",
        "cz": "výfuk",
        "sk": "výfuk",
        "hr": "ispuh",
        "sl": "izpuh",
        "it": "scarico",
        "de": "Auspuff",
        "fr": "échappement",
        "es": "escape",
    },
    "clutch": {
        "bg": "съединител",
        "ro": "ambreiaj",
        "hu": "kuplung",
        "pl": "sprzęgło",
        "cz": "spojka",
        "sk": "spojka",
        "hr": "kvačilo",
        "sl": "sklopka",
        "it": "frizione",
        "de": "Kupplung",
        "fr": "embrayage",
        "es": "embrague",
    },
    "brake": {
        "bg": "спирачка",
        "ro": "frână",
        "hu": "fék",
        "pl": "hamulec",
        "cz": "brzda",
        "sk": "brzda",
        "hr": "kočnica",
        "sl": "zavora",
        "it": "freno",
        "de": "Bremse",
        "fr": "frein",
        "es": "freno",
    },
    "lever": {
        "bg": "лост",
        "ro": "manetă",
        "hu": "kar",
        "pl": "dźwignia",
        "cz": "páka",
        "sk": "páka",
        "hr": "ručica",
        "sl": "ročica",
        "it": "leva",
        "de": "Hebel",
        "fr": "levier",
        "es": "palanca",
    },
    "mirror": {
        "bg": "огледало",
        "ro": "oglindă",
        "hu": "tükör",
        "pl": "lusterko",
        "cz": "zrcátko",
        "sk": "zrkadlo",
        "hr": "ogledalo",
        "sl": "ogledalo",
        "it": "specchio",
        "de": "Spiegel",
        "fr": "rétroviseur",
        "es": "espejo",
    },
    "radiator": {
        "bg": "радиатор",
        "ro": "radiator",
        "hu": "hűtő",
        "pl": "chłodnica",
        "cz": "chladič",
        "sk": "chladič",
        "hr": "hladnjak",
        "sl": "hladilnik",
        "it": "radiatore",
        "de": "Kühler",
        "fr": "radiateur",
        "es": "radiador",
    },
    "windscreen": {
        "bg": "предно стъкло",
        "ro": "parbriz",
        "hu": "szélvédő",
        "pl": "szyba",
        "cz": "plexi",
        "sk": "plexi",
        "hr": "vjetrobran",
        "sl": "vetrobran",
        "it": "parabrezza",
        "de": "Windschild",
        "fr": "pare-brise",
        "es": "parabrisas",
    },
    "seat": {
        "bg": "седалка",
        "ro": "șa",
        "hu": "ülés",
        "pl": "siedzenie",
        "cz": "sedlo",
        "sk": "sedlo",
        "hr": "sjedalo",
        "sl": "sedež",
        "it": "sella",
        "de": "Sitzbank",
        "fr": "selle",
        "es": "asiento",
    },
    "chain": {
        "bg": "верига",
        "ro": "lanț",
        "hu": "lánc",
        "pl": "łańcuch",
        "cz": "řetěz",
        "sk": "reťaz",
        "hr": "lanac",
        "sl": "veriga",
        "it": "catena",
        "de": "Kette",
        "fr": "chaîne",
        "es": "cadena",
    },
    "fork": {
        "bg": "вилка",
        "ro": "furcă",
        "hu": "villa",
        "pl": "widelec",
        "cz": "vidlice",
        "sk": "vidlica",
        "hr": "vilica",
        "sl": "vilice",
        "it": "forcella",
        "de": "Gabel",
        "fr": "fourche",
        "es": "horquilla",
    },
    "disc": {
        "bg": "диск",
        "ro": "disc",
        "hu": "tárcsa",
        "pl": "tarcza",
        "cz": "kotouč",
        "sk": "kotúč",
        "hr": "disk",
        "sl": "disk",
        "it": "disco",
        "de": "Scheibe",
        "fr": "disque",
        "es": "disco",
    },
    "pad": {
        "bg": "накладка",
        "ro": "plăcuță",
        "hu": "betét",
        "pl": "klocek",
        "cz": "destička",
        "sk": "platničky",
        "hr": "pločica",
        "sl": "ploščica",
        "it": "pastiglie",
        "de": "Beläge",
        "fr": "plaquette",
        "es": "pastilla",
    },
    "shock": {
        "bg": "амортисьор",
        "ro": "amortizor",
        "hu": "lengéscsillapító",
        "pl": "amortyzator",
        "cz": "tlumič",
        "sk": "tlmič",
        "hr": "amortizer",
        "sl": "amortizerji",
        "it": "ammortizzatore",
        "de": "Stoßdämpfer",
        "fr": "amortisseur",
        "es": "amortiguador",
    },
    "headlight": {
        "bg": "фар",
        "ro": "far",
        "hu": "fényszóró",
        "pl": "reflektor",
        "cz": "světlo",
        "sk": "svetlo",
        "hr": "prednje svjetlo",
        "sl": "žaromet",
        "it": "faro",
        "de": "Scheinwerfer",
        "fr": "phare",
        "es": "faro",
    },
    "filter": {
        "bg": "филтър",
        "ro": "filtru",
        "hu": "szűrő",
        "pl": "filtr",
        "cz": "filtr",
        "sk": "filter",
        "hr": "filtar",
        "sl": "filter",
        "it": "filtro",
        "de": "Filter",
        "fr": "filtre",
        "es": "filtro",
    },
    "wheel": {
        "bg": "колело",
        "ro": "roată",
        "hu": "kerék",
        "pl": "koło",
        "cz": "kolo",
        "sk": "koleso",
        "hr": "kotač",
        "sl": "kolo",
        "it": "ruota",
        "de": "Rad",
        "fr": "roue",
        "es": "rueda",
    },
    "handlebar": {
        "bg": "кормило",
        "ro": "ghidon",
        "hu": "kormány",
        "pl": "kierownica",
        "cz": "řídítka",
        "sk": "riadidlá",
        "hr": "upravljač",
        "sl": "krmilo",
        "it": "manubrio",
        "de": "Lenker",
        "fr": "guidon",
        "es": "manillar",
    },
    "tank": {
        "bg": "резервоар",
        "ro": "rezervor",
        "hu": "tank",
        "pl": "zbiornik",
        "cz": "nádrž",
        "sk": "nádrž",
        "hr": "spremnik",
        "sl": "rezervoar",
        "it": "serbatoio",
        "de": "Tank",
        "fr": "réservoir",
        "es": "depósito",
    },
    "fairing": {
        "bg": "обтекател",
        "ro": "carenaj",
        "hu": "burkolat",
        "pl": "owiewka",
        "cz": "kapotáž",
        "sk": "kapotáž",
        "hr": "oplata",
        "sl": "oklep",
        "it": "carenatura",
        "de": "Verkleidung",
        "fr": "carénage",
        "es": "carenado",
    },
    "sprocket": {
        "bg": "зъбно колело",
        "ro": "pinion",
        "hu": "lánckerék",
        "pl": "zębatka",
        "cz": "řetězové kolo",
        "sk": "reťazové koleso",
        "hr": "lančanik",
        "sl": "zobnik",
        "it": "corona",
        "de": "Kettenrad",
        "fr": "pignon",
        "es": "piñón",
    },
    "caliper": {
        "bg": "апарат",
        "ro": "etrier",
        "hu": "féknyereg",
        "pl": "zacisk",
        "cz": "třmen",
        "sk": "strmeň",
        "hr": "čeljust",
        "sl": "čeljust",
        "it": "pinza",
        "de": "Bremssattel",
        "fr": "étrier",
        "es": "pinza",
    },
    "peg": {
        "bg": "стъпенка",
        "ro": "scarita",
        "hu": "lábtartó",
        "pl": "podnóżek",
        "cz": "stupačka",
        "sk": "stupačka",
        "hr": "papučica",
        "sl": "stopalo",
        "it": "pedana",
        "de": "Fußraste",
        "fr": "repose-pied",
        "es": "estribo",
    },
    "swingarm": {
        "bg": "махало",
        "ro": "basculantă",
        "hu": "lengőkar",
        "pl": "wahacz",
        "cz": "kyvka",
        "sk": "kyvka",
        "hr": "vilica",
        "sl": "nihalo",
        "it": "forcellone",
        "de": "Schwinge",
        "fr": "bras oscillant",
        "es": "basculante",
    },
    "fender": {
        "bg": "калник",
        "ro": "aripa",
        "hu": "sárvédő",
        "pl": "błotnik",
        "cz": "blatník",
        "sk": "blatník",
        "hr": "blatobran",
        "sl": "blatnik",
        "it": "parafango",
        "de": "Schutzblech",
        "fr": "garde-boue",
        "es": "guardabarros",
    },
    "battery": {
        "bg": "акумулатор",
        "ro": "acumulator",
        "hu": "akkumulátor",
        "pl": "akumulator",
        "cz": "akumulátor",
        "sk": "akumulátor",
        "hr": "akumulator",
        "sl": "akumulator",
        "it": "batteria",
        "de": "Batterie",
        "fr": "batterie",
        "es": "batería",
    },
    "gasket": {
        "bg": "гарнитура",
        "ro": "garnitură",
        "hu": "tömítés",
        "pl": "uszczelka",
        "cz": "těsnění",
        "sk": "tesnenie",
        "hr": "brtva",
        "sl": "tesnilo",
        "it": "guarnizione",
        "de": "Dichtung",
        "fr": "joint",
        "es": "junta",
    },
    # Compound terms (looked up before single-word fallback)
    "crash bar": {
        "bg": "рамка за защита",
        "ro": "bara de protecție",
        "hu": "bukócső",
        "pl": "gmol",
        "cz": "padací rám",
        "sk": "padací rám",
        "hr": "zaštitni okvir",
        "sl": "zaščitni okvir",
        "it": "paramotore",
        "de": "Sturzbügel",
        "fr": "pare-carter",
        "es": "defensa",
    },
    "skid plate": {
        "bg": "предпазна плоча",
        "ro": "scut motor",
        "hu": "motorvédő",
        "pl": "osłona silnika",
        "cz": "kryt motoru",
        "sk": "kryt motora",
        "hr": "zaštita motora",
        "sl": "zaščita motorja",
        "it": "paracoppa",
        "de": "Motorschutz",
        "fr": "sabot moteur",
        "es": "cubrecárter",
    },
    "spark plug": {
        "bg": "свещ",
        "ro": "bujie",
        "hu": "gyújtógyertya",
        "pl": "świeca zapłonowa",
        "cz": "zapalovací svíčka",
        "sk": "zapaľovacia sviečka",
        "hr": "svjećica",
        "sl": "svečka",
        "it": "candela",
        "de": "Zündkerze",
        "fr": "bougie",
        "es": "bujía",
    },
    "slip-on": {
        "bg": "слип-он",
        "ro": "slip-on",
        "hu": "slip-on",
        "pl": "slip-on",
        "cz": "slip-on",
        "sk": "slip-on",
        "hr": "slip-on",
        "sl": "slip-on",
        "it": "slip-on",
        "de": "Slip-on",
        "fr": "slip-on",
        "es": "slip-on",
    },
}

# Build a lookup of compound terms (those containing a space or hyphen) so
# the expansion loop can attempt two-word matches before single-word ones.
_COMPOUND_TERMS: dict[str, dict[str, str]] = {
    term: translations
    for term, translations in TERM_TRANSLATIONS.items()
    if " " in term or "-" in term
}


def expand_query(
    query: str,
    target_language: str,
    *,
    overrides: dict[str, str] | None = None,
) -> str:
    """Expand *query* by translating known English part terms.

    Parameters
    ----------
    query:
        The English search string (e.g. ``"Ducati exhaust slip-on"``).
    target_language:
        ISO-639-1 language code (e.g. ``"bg"``, ``"it"``).
    overrides:
        Optional mapping of ``{language_code: full_replacement_string}``.
        When *target_language* is found here, the override is returned
        verbatim and no further processing takes place.

    Returns
    -------
    str
        The query with recognised terms replaced by their translations.
        Model tokens and unknown words are kept unchanged.
    """
    # 1. Overrides take absolute precedence.
    if overrides and target_language in overrides:
        return overrides[target_language]

    # 2. English queries pass through unchanged.
    if target_language == "en":
        return query

    words = query.split()
    result: list[str] = []
    i = 0

    while i < len(words):
        word = words[i]

        # 3. Model tokens are never translated.
        if word.lower() in _MODEL_TOKENS:
            result.append(word)
            i += 1
            continue

        # 4. Attempt two-word compound match.
        if i + 1 < len(words):
            compound = f"{word} {words[i + 1]}"
            compound_key = compound.lower()
            if compound_key in _COMPOUND_TERMS:
                translations = _COMPOUND_TERMS[compound_key]
                if target_language in translations:
                    result.append(translations[target_language])
                    i += 2
                    continue

        # 5. Attempt hyphenated single-token compound match.
        if "-" in word:
            word_key = word.lower()
            if word_key in _COMPOUND_TERMS:
                translations = _COMPOUND_TERMS[word_key]
                if target_language in translations:
                    result.append(translations[target_language])
                    i += 1
                    continue

        # 6. Single-word translation.
        word_key = word.lower()
        if word_key in TERM_TRANSLATIONS:
            translations = TERM_TRANSLATIONS[word_key]
            if target_language in translations:
                result.append(translations[target_language])
                i += 1
                continue

        # 7. Unknown word -- pass through.
        result.append(word)
        i += 1

    return " ".join(result)
