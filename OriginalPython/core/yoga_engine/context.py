"""
ChartContext - zajednički "prošireni" prikaz karte koji sva yoga pravila
koriste. NE računa ništa iznova preko Swiss Ephemerisa - isključivo
preslaguje/kešira podatke koje core.natal.get_natal_context već izračuna
(zahtjev #27: ne diraj postojeće izračune, samo ih ponovno iskoristi).

Ovdje su implementirane i sve zajedničke helper funkcije iz zahtjeva #4,
kao METODE ove klase (npr. `chart.is_exalted("Jupiter")` umjesto slobodne
funkcije `is_exalted(planet)` bez konteksta - potreban je nekakav "chart"
da bi pitanje uopće imalo smisao, pa je vezano na instancu).

Brojanje kuća je JYOTISH (inkluzivno, "znak u kojem je referentni planet
je njegova prva kuća") - vidi house_from().

Rahu/Ketu i Graha Drishti (zahtjev #5): planet_aspects/mutual_aspect/
house_aspected_by/sign_aspected_by DEFAULT-NO ne uključuju posebne aspekte
Rahua/Ketua (delegiraju na core.aspects.compute_graha_drishti bez
include_rahu_ketu) - tako se izbjegava automatsko "izmišljanje" Rahu/Ketu
aspekata u yogama čiji izvor to ne traži (zahtjev #7). Ako neko KONKRETNO
pravilo izričito treba tu (spornu) konvenciju, mora pozvati
`planet_aspects(p1, p2, include_rahu_ketu=True)` eksplicitno i to
dokumentirati u vlastitom docstringu/reasons.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from core.constants import RASHI, RASHI_LORD
from core.ephemeris import PlanetPosition
from core.aspects import compute_graha_drishti, ASPECTING_PLANETS
from core.planet_strength import compute_dignity, NATURAL_BENEFICS, NATURAL_MALEFICS
from core.combustion import check_combustion
from core.chara_karaka import get_atmakaraka
from core.varga import d9_navamsha_sign_index
from core.yoga_engine.dignity_data import is_moolatrikona as _is_moolatrikona_at
from core.yoga_engine.models import ReferencePoint

KENDRA_HOUSES = {1, 4, 7, 10}
TRIKONA_HOUSES = {1, 5, 9}
DUSTHANA_HOUSES = {6, 8, 12}
UPACHAYA_HOUSES = {3, 6, 10, 11}
PANAPARA_HOUSES = {2, 5, 8, 11}
APOKLIMA_HOUSES = {3, 6, 9, 12}

CLASSICAL_SEVEN = ["Sunce", "Mjesec", "Mars", "Merkur", "Jupiter", "Venera", "Saturn"]


def house_from(reference_sign_index: int, target_sign_index: int) -> int:
    """
    Jyotish (inkluzivno) brojanje kuća: znak u kojem je referentna točka je
    njena PRVA kuća. Primjer iz zahtjeva: Jupiter 4 znaka od Mjeseca =
    house_from(mjesec_sign, jupiter_sign) == 4.
    """
    return (target_sign_index - reference_sign_index) % 12 + 1


def sign_at_house(reference_sign_index: int, house_number: int) -> int:
    """Inverz od house_from - koji je sign_index na zadanoj kućnoj udaljenosti od reference."""
    return (reference_sign_index + house_number - 1) % 12


def is_kendra(house: int) -> bool:
    return house in KENDRA_HOUSES


def is_trikona(house: int) -> bool:
    return house in TRIKONA_HOUSES


def is_dusthana(house: int) -> bool:
    return house in DUSTHANA_HOUSES


def is_upachaya(house: int) -> bool:
    return house in UPACHAYA_HOUSES


def is_panapara(house: int) -> bool:
    return house in PANAPARA_HOUSES


def is_apoklima(house: int) -> bool:
    return house in APOKLIMA_HOUSES


def lord_of(sign_index: int) -> str:
    return RASHI_LORD[RASHI[sign_index % 12]]


@dataclass
class ChartContext:
    ascendant_longitude: float
    ascendant_sign_index: int
    positions: Dict[str, PlanetPosition]
    special_points: Dict
    moon_nature_mode: str = "always_benefic"  # ili "paksha_bala" (zahtjev #21)
    mercury_nature_mode: str = "always_benefic"  # ili "conditional_by_association" (zahtjev #21)
    atmakaraka: str = field(init=False)
    karakamsha_sign_index: int = field(init=False)

    def __post_init__(self) -> None:
        self.atmakaraka = get_atmakaraka(self.positions, scheme="7_karaka").planet
        self.karakamsha_sign_index = d9_navamsha_sign_index(
            self.positions[self.atmakaraka].longitude
        )

    # -- osnovno čitanje pozicija ------------------------------------------------

    def sign_index(self, name: str) -> int:
        """Prihvaća naziv planeta ILI referentnu točku (Lagna/Chandra Lagna/...)."""
        if name in self.positions:
            return self.positions[name].sign_index
        return self.reference_sign_index(name)

    def longitude(self, planet: str) -> float:
        return self.positions[planet].longitude

    def degree_in_sign(self, planet: str) -> float:
        return self.positions[planet].degree_in_sign

    def reference_sign_index(self, reference: str) -> int:
        if reference in (ReferencePoint.LAGNA.value, "Lagna", "AL_LAGNA_ALIAS"):
            return self.ascendant_sign_index
        if reference == ReferencePoint.CHANDRA_LAGNA.value:
            return self.sign_index("Mjesec")
        if reference == ReferencePoint.SURYA.value:
            return self.sign_index("Sunce")
        if reference == ReferencePoint.ARUDHA_LAGNA.value:
            return self.special_points["AL_sign_index"]
        if reference == ReferencePoint.KARAKAMSHA.value:
            return self.karakamsha_sign_index
        raise NotImplementedError(
            f"Referentna točka '{reference}' nije podržana. Hora Lagna i Ghatika "
            f"Lagna namjerno nisu implementirane - vidi napomenu u ovom modulu."
        )

    def house_of(self, planet: str, reference: str = ReferencePoint.LAGNA.value) -> int:
        return house_from(self.reference_sign_index(reference), self.sign_index(planet))

    def house_lord(self, house: int, reference: str = ReferencePoint.LAGNA.value) -> str:
        ref_sign = self.reference_sign_index(reference)
        return lord_of(sign_at_house(ref_sign, house))

    # -- konjunkcija (RASHI-bazirana, zahtjev #6 - ne zapadnjački orb) ----------

    def same_sign(self, p1: str, p2: str) -> bool:
        return self.sign_index(p1) == self.sign_index(p2)

    def planets_in_sign_with(self, planet: str, exclude_self: bool = True) -> List[str]:
        target = self.sign_index(planet)
        return [
            p for p in CLASSICAL_SEVEN
            if self.sign_index(p) == target and not (exclude_self and p == planet)
        ]

    def conjunction_count(self, planet: str) -> int:
        """Broj klasičnih 7 planeta (bez samog sebe) u istom znaku."""
        return len(self.planets_in_sign_with(planet))

    # -- Graha Drishti (zahtjev #5) ----------------------------------------------

    def _aspect_strength(self, from_planet: str, to_sign_index: int, include_rahu_ketu: bool = False) -> float:
        if from_planet not in ASPECTING_PLANETS and not include_rahu_ketu:
            return 0.0
        from_sign = self.sign_index(from_planet)
        rels = compute_graha_drishti(
            {from_planet: from_sign}, {"__target__": to_sign_index}, include_rahu_ketu=include_rahu_ketu
        )
        return rels[0].strength if rels else 0.0

    def planet_aspects(self, from_planet: str, to_planet: str, include_rahu_ketu: bool = False) -> bool:
        return self._aspect_strength(from_planet, self.sign_index(to_planet), include_rahu_ketu) > 0

    def mutual_aspect(self, p1: str, p2: str, include_rahu_ketu: bool = False) -> bool:
        return (
            self.planet_aspects(p1, p2, include_rahu_ketu)
            and self.planet_aspects(p2, p1, include_rahu_ketu)
        )

    def sign_aspected_by(self, planet: str, sign_index: int, include_rahu_ketu: bool = False) -> bool:
        return self._aspect_strength(planet, sign_index, include_rahu_ketu) > 0

    def house_aspected_by(self, planet: str, house: int, reference: str = ReferencePoint.LAGNA.value,
                           include_rahu_ketu: bool = False) -> bool:
        target_sign = sign_at_house(self.reference_sign_index(reference), house)
        return self.sign_aspected_by(planet, target_sign, include_rahu_ketu)

    def aspecting_planets_of(self, target: str, include_rahu_ketu: bool = False) -> List[str]:
        """Koji od 7 (ili 9, ako include_rahu_ketu) planeta aspektiraju zadani planet/točku."""
        candidates = CLASSICAL_SEVEN + (["Rahu", "Ketu"] if include_rahu_ketu else [])
        return [p for p in candidates if p != target and self.planet_aspects(p, target, include_rahu_ketu)]

    def is_conjunct_or_aspected_by(self, planet: str, others: List[str], include_rahu_ketu: bool = False) -> List[str]:
        hits = []
        for other in others:
            if other == planet:
                continue
            if self.same_sign(planet, other) or self.planet_aspects(other, planet, include_rahu_ketu):
                hits.append(other)
        return hits

    # -- dostojanstvo -------------------------------------------------------------

    def dignity(self, planet: str) -> str:
        return compute_dignity(planet, self.sign_index(planet))[0]

    def is_exalted(self, planet: str) -> bool:
        return self.dignity(planet) == "uzvišen"

    def is_debilitated(self, planet: str) -> bool:
        return self.dignity(planet) == "pad"

    def is_own_sign(self, planet: str) -> bool:
        return self.dignity(planet) == "vlastiti"

    def is_moolatrikona(self, planet: str) -> bool:
        return _is_moolatrikona_at(planet, self.longitude(planet))

    def is_own_or_exalted(self, planet: str) -> bool:
        return self.is_own_sign(planet) or self.is_exalted(planet) or self.is_moolatrikona(planet)

    def is_combust(self, planet: str) -> bool:
        if planet in ("Sunce", "Rahu", "Ketu"):
            return False
        info = check_combustion(planet, self.longitude(planet), self.longitude("Sunce"), self.is_retrograde(planet))
        return bool(info and info.is_combust)

    def is_retrograde(self, planet: str) -> bool:
        return self.positions[planet].is_retrograde

    # -- benefic/malefic priroda (zahtjev #20, #21) -------------------------------

    def is_natural_benefic(self, planet: str) -> bool:
        if planet == "Mjesec" and self.moon_nature_mode == "paksha_bala":
            return self.is_waxing_moon()
        if planet == "Merkur" and self.mercury_nature_mode == "conditional_by_association":
            malefics = [p for p in CLASSICAL_SEVEN + ["Rahu", "Ketu"] if p != "Merkur" and self.is_natural_malefic_base(p)]
            afflicted = self.is_conjunct_or_aspected_by("Merkur", malefics, include_rahu_ketu=True)
            return len(afflicted) == 0
        return planet in NATURAL_BENEFICS

    def is_natural_malefic_base(self, planet: str) -> bool:
        """Prirodna priroda BEZ Merkur/Mjesec konfigurabilnosti - koristi se interno kao referenca kad treba izbjeći rekurziju."""
        return planet in NATURAL_MALEFICS

    def is_natural_malefic(self, planet: str) -> bool:
        return not self.is_natural_benefic(planet) if planet in ("Mjesec", "Merkur") else planet in NATURAL_MALEFICS

    def is_waxing_moon(self) -> bool:
        diff = (self.longitude("Mjesec") - self.longitude("Sunce")) % 360.0
        return diff < 180.0

    def is_waning_moon(self) -> bool:
        return not self.is_waxing_moon()

    # -- Parivartana ---------------------------------------------------------------

    def has_exchange(self, lord1: str, lord2: str) -> bool:
        return lord_of(self.sign_index(lord1)) == lord2 and lord_of(self.sign_index(lord2)) == lord1
