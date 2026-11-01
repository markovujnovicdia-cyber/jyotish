"""
Zajednički natalni kontekst osobe - Julijanski dan, ascendent, pozicije
planeta i posebne točke (AL/UL/A7/BP/GK/Mandi).

Izdvojeno iz ui/pages_chart.py (gdje je ranije bilo kao privatne funkcije
_get_natal_context/_compute_natal_special_points) da bi se ISTA logika
mogla ponovno koristiti u core/synastry/ bez dupliciranja - astronomski
rezultati su identični, ovo je čisto premještanje koda.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict

from core.time_utils import local_to_utc, utc_to_julian_day
from core.ephemeris import get_ascendant, get_planet_positions, PlanetPosition
from core.houses import ascendant_sign_index
from core.special_points import (
    compute_arudha_lagna_sign_index,
    compute_upapada_lagna_sign_index,
    compute_darapada_sign_index,
    compute_bhrigu_bindu,
    compute_gulika_from_birth_data,
)
from core.constants import PLANET_ORDER


@dataclass
class NatalContext:
    person_name: str
    utc_dt: datetime
    jd_ut: float
    ascendant_longitude: float
    ascendant_sign_index: int
    positions: Dict[str, PlanetPosition]
    special_points: Dict


def compute_special_points(person, jd_ut: float, asc_lon: float, asc_sign_idx: int, positions: Dict) -> Dict:
    """
    Vraća dict s AL/UL/A7 (sign_index) i BP/GK/Mandi (longitude, GK/Mandi
    mogu biti None ako izračun ne uspije - vidi core/special_points.py).
    """
    planet_sign_index = {name: positions[name].sign_index for name in PLANET_ORDER}
    al_sign_idx = compute_arudha_lagna_sign_index(asc_sign_idx, planet_sign_index)
    ul_sign_idx = compute_upapada_lagna_sign_index(asc_sign_idx, planet_sign_index)
    a7_sign_idx = compute_darapada_sign_index(asc_sign_idx, planet_sign_index)
    bp_lon = compute_bhrigu_bindu(positions["Mjesec"].longitude, positions["Rahu"].longitude)

    gk_lon = None
    mandi_lon = None
    mandi_ghatikas = None
    try:
        gk_result = compute_gulika_from_birth_data(jd_ut, person.birth_date, person.latitude, person.longitude)
        gk_lon = gk_result.longitude
        mandi_lon = gk_result.mandi_longitude
        mandi_ghatikas = gk_result.mandi_ghatikas
    except Exception:
        gk_lon = None

    return {
        "AL_sign_index": al_sign_idx, "UL_sign_index": ul_sign_idx, "A7_sign_index": a7_sign_idx,
        "BP_longitude": bp_lon, "GK_longitude": gk_lon,
        "MANDI_longitude": mandi_lon, "MANDI_ghatikas": mandi_ghatikas,
    }


def get_natal_context(person) -> NatalContext:
    """
    person: db.models.Person (ili bilo koji objekt s istim poljima -
    name, birth_date, birth_time, timezone, latitude, longitude).
    """
    utc_dt = local_to_utc(person.birth_date, person.birth_time, person.timezone)
    jd_ut = utc_to_julian_day(utc_dt)
    asc_lon = get_ascendant(jd_ut, person.latitude, person.longitude)
    positions = get_planet_positions(jd_ut)
    asc_sign_idx = ascendant_sign_index(asc_lon)
    special_points = compute_special_points(person, jd_ut, asc_lon, asc_sign_idx, positions)

    return NatalContext(
        person_name=person.name,
        utc_dt=utc_dt,
        jd_ut=jd_ut,
        ascendant_longitude=asc_lon,
        ascendant_sign_index=asc_sign_idx,
        positions=positions,
        special_points=special_points,
    )
