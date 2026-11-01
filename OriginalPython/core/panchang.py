"""
Tithi (lunarni dan) - jedan od pet elemenata Panchanga. Mjeri kutnu
udaljenost Mjeseca od Sunca, podijeljenu na 30 dijelova od 12° svaki.

Formula i 30 imena su standardna, nesporna (osnovni sanskrtski redni
brojevi + Purnima/Amavasya) - nema alternativnih tradicija za ovo.
"""

from dataclasses import dataclass

TITHI_NAMES_SHUKLA = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",
]
TITHI_NAMES_KRISHNA = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya",
]

TITHI_ARC = 12.0  # stupnjeva po tithiju (360/30)


@dataclass
class TithiInfo:
    number: int          # 1-30 (1-15 Shukla, 16-30 Krishna)
    name: str
    paksha: str           # "Shukla" (rastući) ili "Krishna" (opadajući)
    fraction_elapsed: float  # 0.0-1.0, koliki dio tithija je prošao


def get_tithi(moon_longitude: float, sun_longitude: float) -> TithiInfo:
    diff = (moon_longitude - sun_longitude) % 360.0
    tithi_index = int(diff // TITHI_ARC)  # 0-29
    fraction = (diff - tithi_index * TITHI_ARC) / TITHI_ARC

    if tithi_index < 15:
        paksha = "Shukla"
        name = TITHI_NAMES_SHUKLA[tithi_index]
    else:
        paksha = "Krishna"
        name = TITHI_NAMES_KRISHNA[tithi_index - 15]

    return TithiInfo(number=tithi_index + 1, name=name, paksha=paksha, fraction_elapsed=fraction)
