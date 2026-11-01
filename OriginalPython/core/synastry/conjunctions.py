"""
Stupanjske konjunkcije između planeta (i posebnih točaka) dviju natalnih
karata.

Namjerno se uspoređuje APSOLUTNA sidereal dužina (0-360°), NE znak - ovo
je ključno da bi se ispravno uhvatile konjunkcije preko granice znaka
(npr. 29° Ovna osobe A naspram 1° Bika osobe B su svega 2° razmaka, dakle
u konjunkciji, iako su formalno u različitim znakovima).

Ovo je odvojen, stupanjski/orbisni sloj - NE zamjenjuje klasični Graha
Drishti (core/synastry/graha_drishti.py), koji je kućno-brojani sustav.
Vidi core/synastry/config.py za konfigurabilne orbise.
"""

from typing import Dict, List, Optional

from core.constants import RASHI
from core.nakshatra import get_nakshatra
from core.synastry.config import SynastryConfig
from core.synastry.models import ConjunctionContact

NODE_NAMES = ("Rahu", "Ketu")


def _angular_distance(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def _special_flags(
    name_a: str, name_b: str,
    seventh_lord_a: Optional[str], seventh_lord_b: Optional[str],
) -> List[str]:
    flags = []
    if name_a in NODE_NAMES or name_b in NODE_NAMES:
        flags.append("Rahu/Ketu")
    if "Saturn" in (name_a, name_b):
        flags.append("Saturn")
    if "Mjesec" in (name_a, name_b):
        flags.append("Mjesec")
    if "Venera" in (name_a, name_b):
        flags.append("Venera")
    if "Mars" in (name_a, name_b):
        flags.append("Mars")
    if seventh_lord_a and seventh_lord_a in (name_a, name_b):
        flags.append("vladar 7. kuće (A)")
    if seventh_lord_b and seventh_lord_b in (name_a, name_b):
        flags.append("vladar 7. kuće (B)")
    if "UL" in (name_a, name_b):
        flags.append("Upapada Lagna (UL)")
    if "A7" in (name_a, name_b):
        flags.append("Darapada (A7)")
    return flags


def find_conjunctions(
    person_a_points: Dict[str, float],
    person_b_points: Dict[str, float],
    config: SynastryConfig,
    seventh_lord_a: Optional[str] = None,
    seventh_lord_b: Optional[str] = None,
) -> List[ConjunctionContact]:
    """
    person_a_points / person_b_points: {oznaka: apsolutna_duzina} - obično
    9 planeta + Lagna + AL/UL/A7/BP (posebne točke bez vlastite "brzine").
    seventh_lord_a/b: naziv vladara 7. kuće te osobe (za isticanje kad je
    baš taj planet uključen u konjunkciju - vidi specifikacija 2.3).
    """
    results: List[ConjunctionContact] = []
    for name_a, lon_a in person_a_points.items():
        for name_b, lon_b in person_b_points.items():
            orb = min(config.orb_for(name_a), config.orb_for(name_b))
            distance = _angular_distance(lon_a, lon_b)
            if distance > orb:
                continue

            nak_a = get_nakshatra(lon_a)
            nak_b = get_nakshatra(lon_b)
            sign_a = int(lon_a % 360.0 // 30)
            sign_b = int(lon_b % 360.0 // 30)

            results.append(ConjunctionContact(
                person_a_object=name_a,
                person_b_object=name_b,
                longitude_a=lon_a,
                longitude_b=lon_b,
                sign=RASHI[sign_a] if sign_a == sign_b else f"{RASHI[sign_a]} / {RASHI[sign_b]}",
                degree_distance=round(distance, 2),
                orb_used=orb,
                is_exact=distance <= 1.0,
                same_nakshatra=(nak_a.index == nak_b.index),
                same_pada=(nak_a.index == nak_b.index and nak_a.pada == nak_b.pada),
                special_flags=_special_flags(name_a, name_b, seventh_lord_a, seventh_lord_b),
            ))

    results.sort(key=lambda c: c.degree_distance)
    return results
