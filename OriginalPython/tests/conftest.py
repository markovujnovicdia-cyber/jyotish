"""
Fiksni podaci za testove - bez geokodiranja (koordinate/vremenska zona su
tvrdo upisane), da testovi ne ovise o mrežnom pozivu i uvijek daju isti
rezultat.
"""

from datetime import datetime, timezone

import pytest

from core.constants import PLANET_ORDER, RASHI
from core.ephemeris import PlanetPosition
from core.natal import NatalContext, compute_special_points
from db.models import Person


def make_planet_position(longitude: float, is_retrograde: bool = False) -> PlanetPosition:
    """Sintetički PlanetPosition za jediničke testove (bez swisseph poziva)."""
    lon = longitude % 360.0
    sign_index = int(lon // 30)
    return PlanetPosition(
        name="?", longitude=lon, sign_index=sign_index, sign=RASHI[sign_index],
        degree_in_sign=lon - sign_index * 30, is_retrograde=is_retrograde,
    )


def make_natal_context(ascendant_longitude: float, planet_longitudes: dict, name: str = "Test") -> NatalContext:
    """
    Sintetički NatalContext bez swisseph poziva - za jedinicne testove
    core/synastry modula koji rade na core.natal.NatalContext objektima.
    Neeksplicitno zadani planeti dobiju fiksnu dužinu 65° (Blizanci),
    namjerno izvan tipičnih "posebnih" kuća kad je ascendent blizu 0°.
    """
    positions = {p: make_planet_position(planet_longitudes.get(p, 65.0)) for p in PLANET_ORDER}
    asc_sign_idx = int(ascendant_longitude % 360.0 // 30)

    class _FakePerson:
        birth_date = "2000-01-01"
        latitude = 0.0
        longitude = 0.0

    special_points = compute_special_points(_FakePerson(), jd_ut=2451544.5, asc_lon=ascendant_longitude,
                                             asc_sign_idx=asc_sign_idx, positions=positions)
    return NatalContext(
        person_name=name,
        utc_dt=datetime(2000, 1, 1, tzinfo=timezone.utc),
        jd_ut=2451544.5,
        ascendant_longitude=ascendant_longitude,
        ascendant_sign_index=asc_sign_idx,
        positions=positions,
        special_points=special_points,
    )


@pytest.fixture
def person_a() -> Person:
    return Person(
        id=1,
        name="Osoba A (test)",
        birth_date="1990-05-15",
        birth_time="14:30:00",
        birth_place="Zagreb",
        country="Hrvatska",
        latitude=45.8150,
        longitude=15.9819,
        timezone="Europe/Zagreb",
        time_confirmed=True,
    )


@pytest.fixture
def person_b() -> Person:
    return Person(
        id=2,
        name="Osoba B (test)",
        birth_date="1988-11-02",
        birth_time="03:10:00",
        birth_place="Split",
        country="Hrvatska",
        latitude=43.5081,
        longitude=16.4402,
        timezone="Europe/Zagreb",
        time_confirmed=True,
    )


@pytest.fixture
def person_lea() -> Person:
    """Referentni primjer iz zahtjeva (integracijski test sinastrije) - Sisak koordinate hardkodirane, bez geokodiranja."""
    return Person(
        id=101,
        name="Lea",
        birth_date="1985-11-04",
        birth_time="01:15:00",
        birth_place="Sisak",
        country="Hrvatska",
        latitude=45.4881,
        longitude=16.3745,
        timezone="Europe/Zagreb",
        time_confirmed=True,
    )


@pytest.fixture
def person_marko() -> Person:
    """Referentni primjer iz zahtjeva (integracijski test sinastrije) - Sisak koordinate hardkodirane, bez geokodiranja."""
    return Person(
        id=102,
        name="Marko Vujnović",
        birth_date="1976-12-26",
        birth_time="11:55:00",
        birth_place="Sisak",
        country="Hrvatska",
        latitude=45.4881,
        longitude=16.3745,
        timezone="Europe/Zagreb",
        time_confirmed=True,
    )
