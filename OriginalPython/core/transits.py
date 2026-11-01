"""
Tranziti - položaji planeta na odabrani datum, promatrani od natalnog
ascendenta i natalnog Mjeseca. Posebno se ističu Saturn, Jupiter,
Rahu/Ketu i Mars jer su tradicionalno najznačajniji za tranzitnu analizu.
"""

from dataclasses import dataclass
from datetime import datetime, time
from typing import Dict

from core.ephemeris import get_planet_positions, PlanetPosition
from core.houses import whole_sign_house, ascendant_sign_index

HIGHLIGHTED_PLANETS = ["Saturn", "Jupiter", "Rahu", "Ketu", "Mars"]


@dataclass
class TransitRow:
    planet: str
    sign: str
    degree_in_sign: float
    longitude: float
    house_from_ascendant: int
    house_from_moon: int
    is_retrograde: bool
    highlighted: bool


def compute_transits(transit_jd_ut: float, natal_ascendant_longitude: float,
                      natal_moon_longitude: float) -> Dict[str, TransitRow]:
    """
    transit_jd_ut: Julijanski dan (UT) za odabrani datum tranzita
                   (obično se uzima podne UT ako korisnik bira samo datum,
                   bez preciznog vremena).
    """
    positions = get_planet_positions(transit_jd_ut)

    asc_sign = ascendant_sign_index(natal_ascendant_longitude)
    moon_sign = int((natal_moon_longitude % 360.0) // 30)

    rows: Dict[str, TransitRow] = {}
    for name, pos in positions.items():
        rows[name] = TransitRow(
            planet=name,
            sign=pos.sign,
            degree_in_sign=pos.degree_in_sign,
            longitude=pos.longitude,
            house_from_ascendant=whole_sign_house(pos.sign_index, asc_sign),
            house_from_moon=whole_sign_house(pos.sign_index, moon_sign),
            is_retrograde=pos.is_retrograde,
            highlighted=name in HIGHLIGHTED_PLANETS,
        )
    return rows


def julian_day_for_date_noon_utc(date_str: str) -> float:
    """
    Pomoćna funkcija: za odabrani datum (bez konkretnog vremena) uzima
    podne UTC kao razumnu referentnu točku za tranzitni izračun dana.
    """
    from core.time_utils import utc_to_julian_day
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    dt = dt.replace(hour=12, minute=0, second=0)
    return utc_to_julian_day(dt)
