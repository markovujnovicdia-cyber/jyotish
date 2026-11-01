"""
Izračun nakshatre i pade na temelju apsolutnog sidereal stupnja (0-360).
"""

from dataclasses import dataclass

from core.constants import NAKSHATRA, NAKSHATRA_LORDS, NAKSHATRA_ARC, PADA_ARC


@dataclass
class NakshatraInfo:
    name: str
    index: int      # 0-26
    pada: int       # 1-4
    lord: str       # vladar nakshatre (koristi se za Vimshottari dashu)
    fraction_elapsed: float  # koliki dio nakshatre je već prošao (0.0 - 1.0)


def get_nakshatra(longitude: float) -> NakshatraInfo:
    lon = longitude % 360.0
    index = int(lon // NAKSHATRA_ARC)
    pos_in_nakshatra = lon - index * NAKSHATRA_ARC
    pada = int(pos_in_nakshatra // PADA_ARC) + 1
    fraction_elapsed = pos_in_nakshatra / NAKSHATRA_ARC

    return NakshatraInfo(
        name=NAKSHATRA[index],
        index=index,
        pada=pada,
        lord=NAKSHATRA_LORDS[index],
        fraction_elapsed=fraction_elapsed,
    )
