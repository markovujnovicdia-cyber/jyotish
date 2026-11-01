"""
Varsheshwara (Gospodar godine) - Panchadhikari sustav sa svih 5 sastavnica
Pancha Vargiya Bale.

Pet kandidata potvrđeno kroz više neovisnih izvora (Tajika Neelakanthi,
Hayaratna, i više modernih stručnih izvora se slažu oko istih 5):
1. Janma Lagna Pati - vladar natalnog ascendenta
2. Muntha Pati - vladar Munthinog znaka
3. Varsha Lagna Pati - vladar godišnjeg (Varsha) ascendenta
4. Dina-Ratri Pati - vladar Sunčevog znaka (dan) ili Mjesečevog (noć), u Varshi
5. Tri-Rashi Pati - trojni (triplicity) vladar znaka Varsha Lagne, dan/noć

Snaga: Pancha Vargiya Bala, SVIH 5 klasičnih sastavnica (Kshetra, Uchcha,
Hadda, Drekkana, Navamsa) - točni maksimalni bodovi po sastavnici
(30/20/15/10/5) provjereni protiv više neovisnih izvora.

OPREZ - Hadda Bala: tablica termina/hadda korištena je "egipatska"
(najrašireniji zapadni sustav, kojeg je Tajika povijesno naslijedila
preko perzijsko-arapske astrologije). Istraživanje NIJE pronašlo izvor
koji izričito potvrđuje da je BAŠ OVO tablica koju Tajika tekstovi
koriste - postoje najmanje 3 konkurentske zapadne verzije koje se
razlikuju u nekoliko znakova. Koristi rezultat s tim na umu (označeno ⚠️
u prikazu).

Kvalifikacija: kandidat mora aspektirati Varsha Lagnu unutar vlastite
Deeptamsha (uz dvostranu geometriju Tajika aspekata). Ako nijedan ne
kvalificira, godišnji se vladar NE proglašava automatski. Kriterij jačine
odabran je iz Panchavargiya Bale; školske varijante ostaju moguće.

Korištena Tri-Rashi Pati tablica: Manitt(h)a/Tejahsimha, Hayanaratna ch. 5 §7.
Kod izričito ne potvrđuje povijesnu tablicu Hadda/Pancha Vargiya Bala,
pa te brojčane snage ostaju orijentacijske.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from core.constants import RASHI, RASHI_LORD
from core.planet_strength import compute_uchcha_bala
from core.varga import d9_navamsha_sign_index
from core.tajika import analyze_pair, TAJIKA_PLANETS

# Tajika triplicity day/night rulers, Manitt(h)a/Tejahsimha tradition:
# Hayanaratna ch. 5 §7, Martin Gansten (2020), table by sign.
# This is NOT the western repeating four-element triplicity sequence.
TRIPLICITY_DAY = dict(zip(RASHI, [
    "Sunce", "Venera", "Saturn", "Venera", "Jupiter", "Mjesec",
    "Merkur", "Mars", "Saturn", "Mars", "Jupiter", "Mjesec",
]))
TRIPLICITY_NIGHT = dict(zip(RASHI, [
    "Jupiter", "Mjesec", "Merkur", "Mars", "Sunce", "Venera",
    "Saturn", "Venera", "Saturn", "Mars", "Jupiter", "Mjesec",
]))


@dataclass
class VarsheshwaraCandidate:
    role: str
    planet: str
    strength_score: float
    aspects_varsha_lagna: bool
    bala_detail: str


def get_tri_rashi_lord(sign_index: int, is_day: bool) -> str:
    sign_name = RASHI[sign_index]
    return TRIPLICITY_DAY[sign_name] if is_day else TRIPLICITY_NIGHT[sign_name]


# ---------------------------------------------------------------------------
# Hadda Bala (5. sastavnica, max 15) - OPREZ: tablica termina/hadda koja se
# koristi je "egipatska" (ponekad zvana i ptolemejska) - najrašireniji,
# najčešće citirani zapadni sustav "termina", koji je Tajika povijesno
# naslijedila od perzijsko-arapske astrologije (koja ga je pak naslijedila
# od helenističke). Istraživanje NIJE pronašlo izvor koji izričito
# potvrđuje da JE OVO baš tablica koju Tajika tekstovi koriste - postoje
# najmanje tri konkurentske zapadne verzije (egipatska/haldejska/
# ptolemejska) koje se razlikuju u nekoliko znakova. Koristi s tim na umu.
# Format: (gornja_granica_stupnja, "planet") - ide redom od 0°.
# ---------------------------------------------------------------------------
_HADDA_TABLE: Dict[str, List[Tuple[float, str]]] = {
    "Ovan": [(6, "Jupiter"), (12, "Venera"), (20, "Merkur"), (25, "Mars"), (30, "Saturn")],
    "Bik": [(8, "Venera"), (15, "Merkur"), (22, "Jupiter"), (26, "Saturn"), (30, "Mars")],
    "Blizanci": [(7, "Merkur"), (14, "Jupiter"), (21, "Venera"), (25, "Mars"), (30, "Saturn")],
    "Rak": [(6, "Mars"), (13, "Venera"), (20, "Merkur"), (27, "Jupiter"), (30, "Saturn")],
    "Lav": [(6, "Jupiter"), (11, "Venera"), (18, "Saturn"), (24, "Merkur"), (30, "Mars")],
    "Djevica": [(7, "Merkur"), (17, "Venera"), (21, "Jupiter"), (28, "Mars"), (30, "Saturn")],
    "Vaga": [(6, "Saturn"), (14, "Merkur"), (21, "Jupiter"), (28, "Venera"), (30, "Mars")],
    "Škorpion": [(7, "Mars"), (11, "Venera"), (19, "Merkur"), (24, "Jupiter"), (30, "Saturn")],
    "Strijelac": [(12, "Jupiter"), (17, "Venera"), (21, "Merkur"), (26, "Saturn"), (30, "Mars")],
    "Jarac": [(7, "Merkur"), (14, "Jupiter"), (22, "Venera"), (26, "Saturn"), (30, "Mars")],
    "Vodenjak": [(7, "Merkur"), (13, "Venera"), (20, "Jupiter"), (25, "Mars"), (30, "Saturn")],
    "Ribe": [(12, "Venera"), (16, "Jupiter"), (19, "Merkur"), (28, "Mars"), (30, "Saturn")],
}


def _hadda_lord(sign_index: int, degree_in_sign: float) -> str:
    sign_name = RASHI[sign_index]
    for upper_bound, planet in _HADDA_TABLE[sign_name]:
        if degree_in_sign < upper_bound:
            return planet
    return _HADDA_TABLE[sign_name][-1][1]  # sigurnosna mreža za degree=30 rubni slučaj


def _drekkana_lord(sign_index: int, degree_in_sign: float) -> str:
    """1. dekan = vladar znaka, 2. = vladar 5. znaka od njega, 3. = 9. znaka (trikona uzorak)."""
    decan_num = min(int(degree_in_sign // 10), 2)
    decan_sign = (sign_index + decan_num * 4) % 12
    return RASHI_LORD[RASHI[decan_sign]]


# ---------------------------------------------------------------------------
# Pancha Vargiya Bala - svih 5 klasičnih sastavnica (Kshetra, Uchcha,
# Hadda, Drekkana, Navamsa), PROVJERENO protiv više neovisnih izvora,
# uključujući točne maksimalne bodove (30/20/15/10/5). Hadda Bala nosi
# gore opisanu napomenu o izvoru tablice.
#
# Zbroj 5 sastavnica (max 80) dijeli se s 4 radi usklađivanja s uobičajenom
# "Vishwa Bala" ljestvicom u referentnoj literaturi.
# ---------------------------------------------------------------------------

_DIGNITY_KSHETRA_POINTS = {
    "vlastiti": 30.0, "prijateljski": 22.5,
    "neutralan": 15.0, "neprijateljski": 7.5,
}


def _kshetra_relationship(planet: str, sign_index: int) -> str:
    """
    Kshetra Bala mjeri ISKLJUČIVO odnos planeta prema VLADARU znaka u kojem
    se nalazi (vlastiti/prijateljski/neutralan/neprijateljski) - NE
    uzvišenje/pad, jer to je već posebno pokriveno kroz Uchcha Balu. Ako bi
    se uzvišenje/pad ovdje također nagrađivalo/kažnjavalo, isti bi učinak
    bio uračunat DVA PUTA (jednom kroz Kshetru, jednom kroz Uchchu).
    """
    from core.constants import RASHI, RASHI_LORD
    from core.planet_strength import NATURAL_FRIENDS, NATURAL_ENEMIES
    sign_lord = RASHI_LORD[RASHI[sign_index]]
    if sign_lord == planet:
        return "vlastiti"
    if sign_lord in NATURAL_FRIENDS.get(planet, set()):
        return "prijateljski"
    if sign_lord in NATURAL_ENEMIES.get(planet, set()):
        return "neprijateljski"
    return "neutralan"


def _relationship_points(planet: str, lord: str, max_points: float) -> float:
    if lord == planet:
        return max_points
    from core.planet_strength import NATURAL_FRIENDS, NATURAL_ENEMIES
    if lord in NATURAL_FRIENDS.get(planet, set()):
        return max_points * 0.75
    if lord in NATURAL_ENEMIES.get(planet, set()):
        return max_points * 0.25
    return max_points * 0.5


def compute_pancha_vargiya_bala(planet: str, longitude: float, sign_index: int, degree_in_sign: float) -> Tuple[float, str]:
    """Vraća (ukupna_snaga, detalj_teksta) - svih 5 klasičnih sastavnica, podijeljeno s 4."""
    kshetra_rel = _kshetra_relationship(planet, sign_index)
    kshetra = _DIGNITY_KSHETRA_POINTS[kshetra_rel]

    uchcha_60 = compute_uchcha_bala(planet, longitude)
    uchcha = uchcha_60 / 3.0  # rescale 0-60 -> 0-20

    hadda_lord = _hadda_lord(sign_index, degree_in_sign)
    hadda = _relationship_points(planet, hadda_lord, 15.0)

    drekkana_lord = _drekkana_lord(sign_index, degree_in_sign)
    drekkana = _relationship_points(planet, drekkana_lord, 10.0)

    navamsa_sign = d9_navamsha_sign_index(longitude)
    navamsa_lord = RASHI_LORD[RASHI[navamsa_sign]]
    navamsa = _relationship_points(planet, navamsa_lord, 5.0)

    total = (kshetra + uchcha + hadda + drekkana + navamsa) / 4.0
    detail = (
        f"Kshetra {kshetra:.1f}, Uchcha {uchcha:.1f}, Hadda {hadda:.1f}, "
        f"Drekkana {drekkana:.1f}, Navamsa {navamsa:.1f} (÷4)"
    )
    return total, detail


def compute_varsheshwara(
    natal_asc_sign_index: int,
    muntha_sign_index: int,
    varsha_asc_sign_index: int,
    varsha_asc_longitude: float,
    is_day_birth: bool,
    varsha_planet_positions: dict,
) -> Dict:
    """
    varsha_planet_positions: {naziv: core.ephemeris.PlanetPosition} - IZ
    GODIŠNJE (Varsha) karte, ne natalne.
    Vraća {"candidates": [VarsheshwaraCandidate, ...], "winner": VarsheshwaraCandidate}
    (pobjednik samo među kandidatima koji aspektiraju godišnju lagnu;
    ako nijedan ne ispunjava uvjet, winner=None).
    """
    candidate_defs: List[tuple] = []

    candidate_defs.append(("Janma Lagna Pati", RASHI_LORD[RASHI[natal_asc_sign_index]]))
    candidate_defs.append(("Muntha Pati", RASHI_LORD[RASHI[muntha_sign_index]]))
    candidate_defs.append(("Varsha Lagna Pati", RASHI_LORD[RASHI[varsha_asc_sign_index]]))

    dina_ratri_planet = "Sunce" if is_day_birth else "Mjesec"
    dina_ratri_sign = varsha_planet_positions[dina_ratri_planet].sign_index
    candidate_defs.append(("Dina-Ratri Pati", RASHI_LORD[RASHI[dina_ratri_sign]]))

    candidate_defs.append(("Tri-Rashi Pati", get_tri_rashi_lord(varsha_asc_sign_index, is_day_birth)))

    results: List[VarsheshwaraCandidate] = []
    for role, planet in candidate_defs:
        pos = varsha_planet_positions[planet]
        strength, detail = compute_pancha_vargiya_bala(planet, pos.longitude, pos.sign_index, pos.degree_in_sign)

        # Hayanaratna §8: aspekt prema godišnjoj lagni je obvezan.
        # Pravilno računanje oba smjera kutova i smjernica znakova.
        # Za točku lagne koristi se kandidatov deeptamsha kao dopušteni
        # orb, a ne arbitraran "pola orba" koji isključuje valjane aspekte.
        from core.tajika import DEEPTAMSHA, _ASPECT_BY_SIGN_DISTANCE, _exact_aspect_residual
        asc_diff_sign = (varsha_asc_sign_index - pos.sign_index) % 12
        aspect_name = _ASPECT_BY_SIGN_DISTANCE.get(asc_diff_sign)
        aspects_lagna = (aspect_name is not None and
            abs(_exact_aspect_residual(pos.longitude, varsha_asc_longitude, aspect_name))
                <= DEEPTAMSHA[planet])

        results.append(VarsheshwaraCandidate(
            role=role, planet=planet, strength_score=round(strength, 2),
            aspects_varsha_lagna=aspects_lagna, bala_detail=detail,
        ))

    qualified = [c for c in results if c.aspects_varsha_lagna]
    winner = max(qualified, key=lambda c: c.strength_score) if qualified else None
    return {"candidates": results, "winner": winner, "any_qualified": bool(qualified)}
