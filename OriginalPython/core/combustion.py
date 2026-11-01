"""
Kombustija (Asta/Astangata) - planet je "spaljen" kad je preblizu Suncu,
gubi vidljivost i (simbolički) samostalnu snagu. Sunce se nikad ne
kombustira; Rahu/Ketu se klasično ne uzimaju u obzir.

Orbite PROVJERENE protiv 6+ neovisnih izvora (BPHS, Phaladeepika),
svi se slažu oko istih vrijednosti - nesporna, standardna tablica.
"""

from dataclasses import dataclass
from typing import Optional

COMBUSTION_ORBS = {
    "Mjesec": 12.0,
    "Mars": 17.0,
    "Merkur": 14.0,   # 12.0 ako je retrogradan
    "Jupiter": 11.0,
    "Venera": 10.0,    # 8.0 ako je retrogradna
    "Saturn": 15.0,
}
_RETROGRADE_ORBS = {
    "Merkur": 12.0,
    "Venera": 8.0,
}


@dataclass
class CombustionInfo:
    is_combust: bool
    orb_used: float
    distance_from_sun: float


def check_combustion(planet: str, planet_longitude: float, sun_longitude: float,
                      is_retrograde: bool = False) -> Optional[CombustionInfo]:
    """
    Vraća None za Sunce/Rahu/Ketu (kombustija se na njih ne primjenjuje).
    """
    if planet not in COMBUSTION_ORBS:
        return None

    orb = _RETROGRADE_ORBS.get(planet, COMBUSTION_ORBS[planet]) if is_retrograde else COMBUSTION_ORBS[planet]
    distance = abs((planet_longitude - sun_longitude + 180) % 360 - 180)

    return CombustionInfo(is_combust=distance <= orb, orb_used=orb, distance_from_sun=distance)
