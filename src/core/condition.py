import re
from enum import Enum


class NormalizedCondition(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    UNKNOWN = "unknown"
    EXCLUDED = "excluded"


EXCLUSION_KEYWORDS: list[str] = [
    r"\bbroken\b", r"\bcracked\b", r"\bfor parts\b", r"\bdamaged\b",
    r"\bbent\b", r"\brush?ted?\b", r"\bscrap\b", r"\bdefective\b",
    r"\brotto\b", r"\bcrepato\b", r"\bper ricambi\b", r"\bdanneggiato\b",
    r"\bpiegato\b", r"\barrugginito\b", r"\brottame\b",
    r"\bkaputt\b", r"\bgerissen\b", r"\bfür teile\b", r"\bbeschädigt\b",
    r"\bverbogen\b", r"\bverrostet\b", r"\bschrott\b", r"\bdefekt\b",
    r"\bcassé\b", r"\bfissuré\b", r"\bpour pièces\b", r"\bendommagé\b",
    r"\btordu\b", r"\brouillé\b", r"\bferraille\b",
    r"\bstricat\b", r"\bcrăpat\b", r"\bpentru piese\b", r"\bdeteriora\b",
    r"\bîndoit\b", r"\bruginit\b",
    r"счупен", r"напукан", r"за части", r"повреден", r"огънат", r"ръждясал", r"скрап",
    r"\bzłamany\b", r"\bpęknięty\b", r"\bna części\b", r"\buszkodzony\b",
    r"\bzgięty\b", r"\bzardzewiały\b", r"\bzłom\b",
    r"\btörött\b", r"\brepedt\b", r"\balkatrésznek\b", r"\bsérült\b",
    r"\bgörbült\b", r"\brozsdás\b",
    r"\bzlomený\b", r"\bprasklý\b", r"\bna díly\b", r"\bpoškozený\b",
    r"\bohnutý\b", r"\bzrezivělý\b",
    r"\bslomljen\b", r"\bnapuknut\b", r"\bza dijelove\b", r"\boštećen\b",
    r"\bsavijen\b", r"\bzahrđao\b",
]

_EXCLUSION_PATTERN = re.compile("|".join(EXCLUSION_KEYWORDS), re.IGNORECASE)

_EXCELLENT_LABELS = [
    "like new", "come nuovo", "wie neu", "comme neuf", "como nuevo",
    "mint", "as new", "nuovo", "neuwertig", "neuf", "nuevo",
    "ca nou", "като нов", "jak nowy", "jako novy",
]
_GOOD_LABELS = [
    "good", "buono", "gut", "bon", "bueno", "buen",
    "bun", "добър", "dobry", "dobar", "dobra",
]
_FAIR_LABELS = [
    "acceptable", "accettabile", "akzeptabel", "acceptable", "aceptable",
    "fair", "satisfactory", "usato", "gebraucht", "usado",
]
_EXCLUDED_LABELS = [
    "for parts", "per ricambi", "für teile", "pour pièces", "para piezas",
    "not working", "non funzionante", "defekt",
    "for parts or not working", "per ricambi o non funzionante",
]


class ConditionFilter:
    def should_exclude(self, title: str, description: str) -> bool:
        text = f"{title} {description}"
        return bool(_EXCLUSION_PATTERN.search(text))

    def normalize_label(self, label: str) -> NormalizedCondition:
        if not label.strip():
            return NormalizedCondition.UNKNOWN
        lower = label.lower().strip()
        for excluded in _EXCLUDED_LABELS:
            if excluded in lower:
                return NormalizedCondition.EXCLUDED
        for excellent in _EXCELLENT_LABELS:
            if excellent in lower:
                return NormalizedCondition.EXCELLENT
        for good in _GOOD_LABELS:
            if good in lower:
                return NormalizedCondition.GOOD
        for fair in _FAIR_LABELS:
            if fair in lower:
                return NormalizedCondition.FAIR
        return NormalizedCondition.UNKNOWN
