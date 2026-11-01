"""
Moolatrikona (mulatrikona) rasponi - klasična tablica (BPHS, poglavlje o
dostojanstvu planeta), standardna i potvrđena kroz više neovisnih izvora
(iste vrijednosti u Jagannatha Hora, Parashara's Light, tekstualnim
prijepisima BPHS-a). NAMJERNO odvojeno u zaseban modul umjesto dopune
core/planet_strength.py - Yoga Engine ne smije mijenjati postojeće
core izračune (zahtjev #27); ovo je NOVI, dosad nepostojeći podatak
(core/planet_strength.py ne razlikuje "vlastiti" od "moolatrikona").

Rahu/Ketu nemaju klasični Moolatrikona znak niti u jednom glavnom izvoru -
namjerno izostavljeni (is_moolatrikona vraća False za njih).
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from core.constants import RASHI

# {planet: (sign_name, deg_start, deg_end)} - raspon je UNUTAR znaka (0-30)
MOOLATRIKONA: Dict[str, Tuple[str, float, float]] = {
    "Sunce": ("Lav", 0.0, 20.0),
    "Mjesec": ("Bik", 4.0, 20.0),
    "Mars": ("Ovan", 0.0, 12.0),
    "Merkur": ("Djevica", 16.0, 20.0),
    "Jupiter": ("Strijelac", 0.0, 10.0),
    "Venera": ("Vaga", 0.0, 15.0),
    "Saturn": ("Vodenjak", 0.0, 20.0),
}

MOOLATRIKONA_SIGN_INDEX: Dict[str, int] = {
    planet: RASHI.index(sign_name) for planet, (sign_name, _, _) in MOOLATRIKONA.items()
}


def is_moolatrikona(planet: str, longitude: float) -> bool:
    """
    True ako je 'planet' na zadanoj apsolutnoj sidereal dužini unutar svog
    klasičnog Moolatrikona raspona. Napomena: Moolatrikona raspon je UNUTAR
    vlastitog znaka planeta izvan Moolatrikona potpodručja (npr. Sunce
    20°-30° Lava) - to je i dalje "vlastiti znak" (own sign), samo ne i
    Moolatrikona.
    """
    if planet not in MOOLATRIKONA:
        return False
    sign_name, deg_start, deg_end = MOOLATRIKONA[planet]
    sign_index = RASHI.index(sign_name)
    lon = longitude % 360.0
    if int(lon // 30) != sign_index:
        return False
    deg_in_sign = lon - sign_index * 30
    return deg_start <= deg_in_sign <= deg_end
