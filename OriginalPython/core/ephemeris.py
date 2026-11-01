"""
Sloj oko Swiss Ephemeris (pyswisseph) biblioteke.

Postavke po specifikaciji:
- Ayanamsha: Lahiri (SIDM_LAHIRI)
- Zodijak: sidereal (SEFLG_SIDEREAL)
- Rahu/Ketu: mean node (SE_MEAN_NODE), Ketu = Rahu + 180°

Sve funkcije rade s Julijanskim danom u UT (ne lokalnim vremenom) -
za pretvorbu koristi core.time_utils.
"""

from dataclasses import dataclass
from typing import Dict

import swisseph as swe

from core.constants import RASHI, SWE_PLANET_CODES

# Postavi Lahiri ayanamshu jednom, globalno za cijelu sesiju
swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

SIDEREAL_FLAG = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED


@dataclass
class PlanetPosition:
    name: str
    longitude: float          # apsolutni sidereal stupanj, 0-360
    sign_index: int           # 0 = Mesha, 1 = Vrishabha, ...
    sign: str                 # naziv znaka
    degree_in_sign: float      # 0-30 stupnjeva unutar znaka
    is_retrograde: bool


def _normalize_deg(deg: float) -> float:
    return deg % 360.0


def get_ascendant(jd_ut: float, lat: float, lon: float) -> float:
    """
    Vraća sidereal stupanj ascendenta (Lagne) za zadani Julijanski dan i
    geografsku širinu/dužinu. Koristi se sustav kuća 'W' (whole sign) kao
    osnova za houses(), ali stvarni sidereal ascendent dobivamo oduzimanjem
    ayanamshe od tropskog ascendenta koji swe.houses() vraća.
    """
    # swe.houses_ex s SIDEREAL_FLAG direktno vraća sidereal kuće/ascendent
    cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, b'W', SIDEREAL_FLAG)
    asc = ascmc[0]
    return _normalize_deg(asc)


def get_planet_positions(jd_ut: float) -> Dict[str, PlanetPosition]:
    """
    Računa sidereal pozicije za Sunce, Mjesec, Mars, Merkur, Jupiter,
    Venera, Saturn, Rahu i Ketu (Ketu izveden iz Rahua).
    """
    results: Dict[str, PlanetPosition] = {}

    for name, code in SWE_PLANET_CODES.items():
        xx, _flags = swe.calc_ut(jd_ut, code, SIDEREAL_FLAG)
        lon = _normalize_deg(xx[0])
        speed = xx[3]  # dnevna brzina u longitudi; negativna = retrogradan
        sign_index = int(lon // 30)
        deg_in_sign = lon - sign_index * 30
        results[name] = PlanetPosition(
            name=name,
            longitude=lon,
            sign_index=sign_index,
            sign=RASHI[sign_index],
            degree_in_sign=deg_in_sign,
            is_retrograde=speed < 0,
        )

    # Ketu = Rahu + 180°, uvijek "direktan" u smislu simetrije s Rahuom
    rahu = results["Rahu"]
    ketu_lon = _normalize_deg(rahu.longitude + 180.0)
    ketu_sign_index = int(ketu_lon // 30)
    results["Ketu"] = PlanetPosition(
        name="Ketu",
        longitude=ketu_lon,
        sign_index=ketu_sign_index,
        sign=RASHI[ketu_sign_index],
        degree_in_sign=ketu_lon - ketu_sign_index * 30,
        is_retrograde=rahu.is_retrograde,
    )

    return results


def get_sunrise_sunset_jd(jd_ut_approx: float, lat: float, lon: float):
    """
    Vraća (izlazak_jd, zalazak_jd) Sunca za dan koji sadrži jd_ut_approx,
    na zadanoj lokaciji. Koristi swe.rise_trans - NIJE testirano u ovom
    razvojnom okruženju (nema pyswisseph ovdje), potrebno provjeriti na
    stvarnom primjeru prije oslanjanja na Guliku.
    """
    geopos = (lon, lat, 0.0)
    _res_rise, tret_rise = swe.rise_trans(jd_ut_approx - 0.5, swe.SUN, swe.CALC_RISE, geopos)
    _res_set, tret_set = swe.rise_trans(jd_ut_approx - 0.5, swe.SUN, swe.CALC_SET, geopos)
    return tret_rise[0], tret_set[0]
