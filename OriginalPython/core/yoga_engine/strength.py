"""
Centralizirani, transparentni model snage yoge (zahtjev #19).

NAMJERNA razdvojenost od "postoji li yoga?" (formation, bool, definirano u
svakom pravilu zasebno prema klasičnom tekstu) i "koliko je jaka?"
(strength, 0-100, IZVEDENO tek NAKON što je formation=True). Ovo NIJE
zamjena za puni klasični Shadbala (isto ograničenje kao i postojeći
core/planet_strength.py - vidi njegov docstring) - to je dokumentirana,
reproducibilna sekundarna procjena koja koristi dignitet, kombustiju,
kućni položaj i aspekte malefika/dobrotvora kao ulazne faktore, IDENTIČNO
načelu kao core/planet_strength.compute_planet_strength (isti stil,
zaseban modul jer yoge trebaju kombinirati snagu VIŠE planeta odjednom, a
ne samo jednog).

Formula (dokumentirano, nema proizvoljnih "magic" brojeva bez objašnjenja):

    score = 50 (baznica)
    + dignitet planeta:      uzvišen +30, moolatrikona +25, vlastiti +20,
                              prijateljski +8, neutralan 0, neprijateljski -12,
                              pad -25
    - kombustija:             -15 ako je kombust
    + kućni položaj:          kendra +10, trikona +10, upachaya +5,
                              panapara 0, dusthana -15 (samo ako se zatraži
                              preko house_number parametra)
    + Vargottama bonus:       +10 ako je D1 znak == D9 (Navamsha) znak
    + dobrotvorni aspekti:    +5 po različitom dobrotvoru koji aspektira
                              (max +15)
    - zlotvorni aspekti:      -5 po različitom zlotvoru koji aspektira/je
                              u konjunkciji (max -20)

Rezultat se ograničava na [0, 100]. Status (STRONG/WEAK/...) se izvodi iz
konačnog broja kroz `classify_status`.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from core.yoga_engine.context import ChartContext, is_kendra, is_trikona, is_dusthana, is_upachaya, is_panapara
from core.yoga_engine.models import YogaStatus
from core.varga import d9_navamsha_sign_index

_DIGNITY_TERM = {
    "uzvišen": 30.0,
    "vlastiti": 20.0,
    "prijateljski": 8.0,
    "neutralan": 0.0,
    "neprijateljski": -12.0,
    "pad": -25.0,
}


@dataclass
class StrengthBreakdown:
    base: float = 50.0
    dignity_term: float = 0.0
    moolatrikona_bonus: float = 0.0
    combustion_penalty: float = 0.0
    house_term: float = 0.0
    vargottama_bonus: float = 0.0
    benefic_aspect_bonus: float = 0.0
    malefic_aspect_penalty: float = 0.0
    manual_adjustments: List[str] = field(default_factory=list)
    manual_delta: float = 0.0

    @property
    def total(self) -> float:
        raw = (
            self.base + self.dignity_term + self.moolatrikona_bonus - self.combustion_penalty
            + self.house_term + self.vargottama_bonus + self.benefic_aspect_bonus
            - self.malefic_aspect_penalty + self.manual_delta
        )
        return max(0.0, min(100.0, raw))

    def as_reasons(self) -> List[str]:
        lines = [f"Baznica: {self.base:.0f}"]
        if self.dignity_term:
            lines.append(f"Dostojanstvo: {self.dignity_term:+.0f}")
        if self.moolatrikona_bonus:
            lines.append(f"Moolatrikona: {self.moolatrikona_bonus:+.0f}")
        if self.combustion_penalty:
            lines.append(f"Kombustija: -{self.combustion_penalty:.0f}")
        if self.house_term:
            lines.append(f"Kućni položaj: {self.house_term:+.0f}")
        if self.vargottama_bonus:
            lines.append(f"Vargottama (D1=D9): {self.vargottama_bonus:+.0f}")
        if self.benefic_aspect_bonus:
            lines.append(f"Aspekti dobrotvora: {self.benefic_aspect_bonus:+.0f}")
        if self.malefic_aspect_penalty:
            lines.append(f"Aspekti/konjunkcije zlotvora: -{self.malefic_aspect_penalty:.0f}")
        lines.extend(self.manual_adjustments)
        lines.append(f"UKUPNO: {self.total:.0f}/100")
        return lines


def compute_planet_yoga_strength(
    chart: ChartContext,
    planet: str,
    house_number: Optional[int] = None,
    reference: str = "Lagna",
    exclude_from_affliction_check: Optional[List[str]] = None,
) -> StrengthBreakdown:
    """
    Osnovna gradivna jedinica - snaga JEDNOG planeta unutar yoge. Za yoge s
    više planeta (npr. Raja Yoga preko dva vladara), pozovi ovo za svaki
    planet i uzmi prosjek/min, ovisno o pravilu (dokumentirati u pozivnom
    pravilu koji je odabran).
    """
    exclude = set(exclude_from_affliction_check or [])
    b = StrengthBreakdown()
    b.dignity_term = _DIGNITY_TERM.get(chart.dignity(planet), 0.0)
    if chart.is_moolatrikona(planet):
        b.moolatrikona_bonus = 5.0  # dodatni bonus preko "vlastiti" (Moolatrikona > obican vlastiti znak)
    if chart.is_combust(planet):
        b.combustion_penalty = 15.0

    if house_number is not None:
        if is_kendra(house_number):
            b.house_term = 10.0
        elif is_trikona(house_number):
            b.house_term = 10.0
        elif is_upachaya(house_number) and house_number == 3:
            b.house_term = 5.0
        elif is_dusthana(house_number):
            b.house_term = -15.0

    d1_sign = chart.sign_index(planet)
    d9_sign = d9_navamsha_sign_index(chart.longitude(planet))
    if d1_sign == d9_sign:
        b.vargottama_bonus = 10.0

    from core.yoga_engine.context import CLASSICAL_SEVEN
    benefics_aspecting = [
        p for p in CLASSICAL_SEVEN
        if p != planet and p not in exclude and chart.is_natural_benefic(p) and chart.planet_aspects(p, planet)
    ]
    malefics_touching = [
        p for p in CLASSICAL_SEVEN + ["Rahu", "Ketu"]
        if p != planet and p not in exclude and chart.is_natural_malefic(p)
        and (chart.same_sign(p, planet) or chart.planet_aspects(p, planet, include_rahu_ketu=True))
    ]
    b.benefic_aspect_bonus = min(15.0, 5.0 * len(benefics_aspecting))
    b.malefic_aspect_penalty = min(20.0, 5.0 * len(malefics_touching))

    return b


def classify_status(formation: bool, strength: float, cancelled: bool = False) -> str:
    if not formation:
        return YogaStatus.NOT_PRESENT.value
    if cancelled:
        return YogaStatus.CANCELLED.value
    if strength < 20:
        return YogaStatus.HEAVILY_AFFLICTED.value
    if strength < 40:
        return YogaStatus.WEAK.value
    if strength < 60:
        return YogaStatus.MEDIUM.value
    if strength < 80:
        return YogaStatus.STRONG.value
    return YogaStatus.VERY_STRONG.value
