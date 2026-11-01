"""
Pomoćne funkcije za formatiranje oznaka planeta i posebnih točaka (AL/BP/GK)
na kartama - kratica + nakshatra (kratica) + pada, u jednom kompaktnom
retku, da karte ostanu čitke.
"""

from core.constants import PLANET_ABBR, NAKSHATRA_ABBR
from core.nakshatra import get_nakshatra


def format_planet_label(name: str, longitude: float, is_retrograde: bool = False) -> str:
    abbr = PLANET_ABBR.get(name, name[:2])
    if is_retrograde:
        abbr += "R"
    nak = get_nakshatra(longitude)
    nak_abbr = NAKSHATRA_ABBR[nak.index]
    return f"{abbr} {nak_abbr}-{nak.pada}"


def format_point_label(abbr: str, longitude: float) -> str:
    """Za posebne točke (AL, BP, GK) - bez retrogradnosti."""
    nak = get_nakshatra(longitude)
    nak_abbr = NAKSHATRA_ABBR[nak.index]
    return f"{abbr} {nak_abbr}-{nak.pada}"
