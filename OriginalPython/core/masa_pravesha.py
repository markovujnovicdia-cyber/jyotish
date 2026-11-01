"""
Masa Pravesha (mjesečne progresije) - klasična Tajika tehnika, spomenuta uz
Varsha Pravesha (npr. K.S. Charak, "A Textbook of Varshaphala"; i u
Suryasiddhanti, koja govori o "varsha i maasa pravesha" kartama).

Princip: baš kao što Varsha Pravesha traži trenutak kad Sunce ponovno
dosegne NATALNU dužinu (jednom godišnje), Masa Pravesha traži trenutak
kad Sunce dosegne natalnu dužinu + n*30° (n=0..11) - dakle 12 "mjesečnih
ulazaka" unutar iste godine, svaki približno 30-31 dan razmaknut. Prvi
Masa (n=0) je sam trenutak Varsha Pravesha.

Za svaki mjesec računamo ascendent i položaje planeta u tom trenutku -
isti princip kao Varsha karta, samo na finijoj (mjesečnoj) razini.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

import swisseph as swe

from core.ephemeris import get_ascendant, get_planet_positions, SIDEREAL_FLAG
from core.constants import RASHI
from core.special_points import (
    compute_arudha_lagna_sign_index,
    compute_bhrigu_bindu,
    compute_gulika_from_birth_data,
)

SUN_CODE = 0  # swe.SUN


@dataclass
class MasaPraveshaResult:
    month_number: int          # 1-12
    datetime_utc: datetime
    ascendant_longitude: float
    ascendant_sign: str
    planet_positions: Dict
    arudha_lagna_sign_index: int
    bhrigu_bindu_longitude: float
    gulika_longitude: Optional[float]
    mandi_longitude: Optional[float]
    mandi_ghatikas: Optional[float]


def _sun_longitude(jd_ut: float) -> float:
    xx, _ = swe.calc_ut(jd_ut, SUN_CODE, SIDEREAL_FLAG)
    return xx[0] % 360.0


def _find_sun_longitude_jd(target_longitude: float, jd_guess: float) -> float:
    """Bisekcijom traži Julijanski dan kad Sunce dosegne target_longitude, blizu jd_guess."""
    jd_lo = jd_guess - 4
    jd_hi = jd_guess + 4

    def diff(jd):
        lon = _sun_longitude(jd)
        return (lon - target_longitude + 180) % 360 - 180

    for _ in range(60):
        jd_mid = (jd_lo + jd_hi) / 2.0
        d_mid = diff(jd_mid)
        if abs(d_mid) < 1e-6:
            return jd_mid
        d_lo = diff(jd_lo)
        if (d_lo < 0) == (d_mid < 0):
            jd_lo = jd_mid
        else:
            jd_hi = jd_mid

    return (jd_lo + jd_hi) / 2.0


def compute_masa_pravesha_sequence(
    natal_sun_longitude: float, varsha_return_jd: float, lat: float, lon: float,
) -> List[MasaPraveshaResult]:
    """
    Vraća 12 Masa Pravesha rezultata unutar godine koja počinje na
    varsha_return_jd (Varsha Pravesha trenutak, koji je ujedno i 1. Masa).
    """
    results: List[MasaPraveshaResult] = []
    avg_days_per_masa = 365.2425 / 12.0  # ~30.44 dana, samo za procjenu polazišta pretrage

    for n in range(12):
        target_lon = (natal_sun_longitude + n * 30.0) % 360.0
        if n == 0:
            jd = varsha_return_jd
        else:
            jd_guess = varsha_return_jd + n * avg_days_per_masa
            jd = _find_sun_longitude_jd(target_lon, jd_guess)

        asc_longitude = get_ascendant(jd, lat, lon)
        asc_sign_index = int(asc_longitude // 30)
        planet_positions = get_planet_positions(jd)

        y, m, d, h = swe.revjul(jd)
        hour = int(h)
        minute = int((h - hour) * 60)
        dt = datetime(y, m, d, hour, minute, tzinfo=timezone.utc)

        planet_sign_index = {name: pos.sign_index for name, pos in planet_positions.items()}
        al_sign_index = compute_arudha_lagna_sign_index(asc_sign_index, planet_sign_index)
        bp_longitude = compute_bhrigu_bindu(
            planet_positions["Mjesec"].longitude, planet_positions["Rahu"].longitude
        )

        gulika_lon = None
        mandi_lon = None
        mandi_ghatikas = None
        try:
            gk_result = compute_gulika_from_birth_data(jd, dt.strftime("%Y-%m-%d"), lat, lon)
            gulika_lon = gk_result.longitude
            mandi_lon = gk_result.mandi_longitude
            mandi_ghatikas = gk_result.mandi_ghatikas
        except Exception:
            gulika_lon = None

        results.append(MasaPraveshaResult(
            month_number=n + 1,
            datetime_utc=dt,
            ascendant_longitude=asc_longitude,
            ascendant_sign=RASHI[asc_sign_index],
            planet_positions=planet_positions,
            arudha_lagna_sign_index=al_sign_index,
            bhrigu_bindu_longitude=bp_longitude,
            gulika_longitude=gulika_lon,
            mandi_longitude=mandi_lon,
            mandi_ghatikas=mandi_ghatikas,
        ))

    return results
