"""
Detekcija odabranih klasičnih yoga - provjereno protiv više neovisnih
izvora prije implementacije.

Implementirano:
- Pancha Mahapurusha yoge (5): Ruchaka (Mars), Bhadra (Merkur),
  Hamsa (Jupiter), Malavya (Venera), Sasa (Saturn) - planet u vlastitom
  ili uzvišenom znaku, I u kutnoj kući (1,4,7,10) od Lagne.
- Gajakesari yoga: Jupiter u kutnoj kući (1,4,7,10) od Mjeseca.
- Chandra-Mangal yoga: Mjesec i Mars u istom znaku (konjunkcija).
- Budhaditya yoga: Sunce i Merkur u istom znaku (konjunkcija).

NIJE implementirano (TODO za sljedeću verziju): Neecha Bhanga Raja Yoga
(otkazivanje pada - više različitih klasičnih uvjeta, zahtijeva dodatnu
provjeru prije implementacije), Raja yoge (kombinacije vladara kendra i
trikona kuća), Dhana yoge.
"""

from dataclasses import dataclass
from typing import List

from core.houses import whole_sign_house
from core.planet_strength import compute_dignity

_KENDRA_HOUSES = {1, 4, 7, 10}

_MAHAPURUSHA_PLANETS = {
    "Mars": "Ruchaka",
    "Merkur": "Bhadra",
    "Jupiter": "Hamsa",
    "Venera": "Malavya",
    "Saturn": "Sasa",
}


@dataclass
class YogaResult:
    name: str
    planets: List[str]
    description: str


def detect_yogas(asc_sign_idx: int, positions: dict) -> List[YogaResult]:
    """
    positions: {naziv_planeta: core.ephemeris.PlanetPosition}
    Vraća listu pronađenih yoga (može biti prazna).
    """
    yogas: List[YogaResult] = []

    for planet, yoga_name in _MAHAPURUSHA_PLANETS.items():
        pos = positions[planet]
        house = whole_sign_house(pos.sign_index, asc_sign_idx)
        dignity, _ = compute_dignity(planet, pos.sign_index)
        if house in _KENDRA_HOUSES and dignity in ("uzvišen", "vlastiti"):
            yogas.append(YogaResult(
                name=yoga_name,
                planets=[planet],
                description=(
                    f"{planet} je {dignity} u {house}. kući (kutna kuća) - "
                    f"klasična Pancha Mahapurusha yoga."
                ),
            ))

    moon_sign = positions["Mjesec"].sign_index
    jupiter_sign = positions["Jupiter"].sign_index
    house_from_moon = whole_sign_house(jupiter_sign, moon_sign)
    if house_from_moon in _KENDRA_HOUSES:
        yogas.append(YogaResult(
            name="Gajakesari",
            planets=["Jupiter", "Mjesec"],
            description=(
                f"Jupiter je u kutnoj kući ({house_from_moon}.) gledano od Mjeseca - "
                f"jedna od najpoznatijih yoga, donosi mudrost i ugled."
            ),
        ))

    if positions["Mjesec"].sign_index == positions["Mars"].sign_index:
        yogas.append(YogaResult(
            name="Chandra-Mangal",
            planets=["Mjesec", "Mars"],
            description="Mjesec i Mars u istom znaku - donosi poduzetnički duh i financijsku dobit.",
        ))

    if positions["Sunce"].sign_index == positions["Merkur"].sign_index:
        yogas.append(YogaResult(
            name="Budhaditya",
            planets=["Sunce", "Merkur"],
            description="Sunce i Merkur u istom znaku - donosi intelekt i analitičke sposobnosti.",
        ))

    return yogas
