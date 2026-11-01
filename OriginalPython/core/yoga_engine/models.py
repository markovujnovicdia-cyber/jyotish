"""
Podatkovni modeli Yoga Engine-a.

Namjerno odvojeno na dva sloja:

- `YogaDefinition` - statični "katalog" podaci o yogi, neovisni o bilo kojoj
  konkretnoj karti (naziv, izvor, kategorija, referentna točka, verzija
  pravila...). Postoji JEDNOM po yogi, registriran u core/yoga_engine/registry.py.

- `YogaResult` - rezultat PRIMJENE pravila na konkretnu kartu. present=False
  je jednako validan i koristan rezultat kao present=True (naročito za Debug
  mod - vidi reasons/debug_log), NE znači "yoga nije implementirana".

Razlika između "formation" (jesu li osnovni uvjeti ispunjeni - bool) i
"strength" (0-100, koliko je jaka NAKON što je formation=True) je namjerna
(zahtjev #19) - nikad se ne miješaju u jedno polje.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class ReferencePoint(str, Enum):
    """
    Referentne točke od kojih se broje kuće/znakovi za pojedinu yogu.
    Napomena: Hora Lagna i Ghatika Lagna su NAMJERNO izostavljene - vidi
    core/yoga_engine/context.py, ChartContext.reference_sign_index, gdje
    je objašnjeno zašto (nesigurnost oko točne klasične formule za elapsed-
    ghatika izračun; #2 zahtijeva da se ne izmišlja pravilo).
    """
    LAGNA = "Lagna"
    CHANDRA_LAGNA = "Chandra Lagna"
    SURYA = "Surya"
    ARUDHA_LAGNA = "Arudha Lagna"
    KARAKAMSHA = "Karakamsha"


class YogaStatus(str, Enum):
    """Prikazni status - izveden iz strength/cancellation, vidi core/yoga_engine/strength.py."""
    NOT_PRESENT = "nije prisutna"
    CANCELLED = "poništena"
    HEAVILY_AFFLICTED = "teško oštećena"
    WEAK = "slaba"
    MEDIUM = "srednja"
    STRONG = "jaka"
    VERY_STRONG = "vrlo jaka"


@dataclass
class YogaDefinition:
    """
    Statični katalog podaci o jednoj yogi - postoji jednom, neovisno o karti.
    Ovo je "recept", core/yoga_engine/registry.py ga povezuje s funkcijom
    pravila (Callable[[ChartContext], List[YogaResult]]).
    """
    id: str
    sanskrit_name: str
    transliteration: str
    hr_name: str
    hr_description: str
    category: str
    source: str  # "BPHS" / "Phaladipika" / "Saravali" / "Brihat Jataka" / "Jataka Parijata" / drugo
    source_reference: str = ""  # poglavlje/stih ako je poznat
    variant: str = ""  # "Parashara varijanta" / "Phaladipika varijanta" / ... ako postoji vise klasicnih definicija
    reference_point: str = ReferencePoint.LAGNA.value
    planets_involved: List[str] = field(default_factory=list)
    rule_version: str = "BPHS-1.0"
    implemented: bool = True
    requires_source_review: bool = False
    review_note: str = ""
    favorable: Optional[bool] = True  # None = neutralno/opisno (npr. Parivartana tip)


@dataclass
class YogaResult:
    """Rezultat primjene JEDNOG pravila na JEDNU kartu."""
    id: str
    name: str  # hrvatski naziv (iz definicije)
    sanskrit_name: str
    transliteration: str
    present: bool
    category: str
    planets: List[str]
    houses: List[int]
    reference: str
    strength: float  # 0-100, SAMO smisleno ako present=True (inace 0.0)
    status: str  # YogaStatus.value
    reasons: List[str]
    weakening_factors: List[str] = field(default_factory=list)
    cancellation_factors: List[str] = field(default_factory=list)
    source: str = ""
    variant: str = ""
    debug_log: List[str] = field(default_factory=list)  # korak-po-korak trag (zahtjev #25)
    requires_source_review: bool = False
    review_note: str = ""
    favorable: Optional[bool] = True
    instance_label: str = ""  # za yoge s vise pojavnica u istoj karti (Dhana #1, Parivartana Mars-Venera...)


class DebugLog:
    """
    Mali helper da pravila jednoloredamo grade debug_log i reasons bez
    dupliciranja iste poruke na dva mjesta - append_true/append_false ide u
    debug_log UVIJEK, a u reasons SAMO ako je uvjet pridonio konacnom TRUE
    rezultatu (poziva se rucno kroz .reasons na kraju pravila).
    """

    def __init__(self) -> None:
        self.lines: List[str] = []

    def check(self, label: str, value: bool, extra: str = "") -> bool:
        suffix = f" ({extra})" if extra else ""
        self.lines.append(f"{label} = {'TRUE' if value else 'FALSE'}{suffix}")
        return value

    def note(self, text: str) -> None:
        self.lines.append(text)

    def result(self, verdict: bool) -> None:
        self.lines.append(f"REZULTAT = {'PRISUTNA' if verdict else 'NIJE PRISUTNA'}")
