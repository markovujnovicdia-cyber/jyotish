"""
Ashtakavarga - sustav "bodova" (bindu) koji svaki od 8 izvora (7 klasičnih
planeta + Lagna) dodjeljuje određenim znakovima, gledano od svoje pozicije.

Tablica dobrotvornih mjesta (benefic places) je POTPUNA i PROVJERENA -
ukupni zbroj po planetu odgovara poznatim klasičnim konstantama (B.V.
Raman, "Ashtakavarga System of Prediction"):
  Sunce=48, Mjesec=49, Mars=39, Merkur=54, Jupiter=56, Venera=52, Saturn=39
  UKUPNO = 337 (provjereno zbrajanjem tablice ispod)

Rahu i Ketu se NE koriste u Ashtakavargi (klasično isključeni, po Parashari).

Formula: za planet P, za svaki od 8 izvora R (na svojoj poziciji), za
svaku kuću h iz BENEFIC_PLACES[P][R], bindu se dodjeljuje znaku:
    (sign_index_R + h - 1) % 12
Ovo je provjereno protiv radnog primjera iz literature (B.V. Ramanov
"Standard Horoscope") - formula i ukupni brojevi bindua su se poklopili.

Sarvashtakavarga = zbroj svih 7 Bhinnashtakavarga (BEZ redukcija - Trikona
i Ekadhipatya Sodhana redukcije mijenjaju samo pojedinačne Bhinnashtakavarge
za neke napredne primjene, ne i Sarvashtakavargu - nisu ovdje implementirane).
"""

from typing import Dict, List

ASHTAKAVARGA_PLANETS = ["Sunce", "Mjesec", "Mars", "Merkur", "Jupiter", "Venera", "Saturn"]
_SOURCES = ASHTAKAVARGA_PLANETS + ["Lagna"]

BENEFIC_PLACES: Dict[str, Dict[str, List[int]]] = {
    "Sunce": {
        "Sunce": [1, 2, 4, 7, 8, 9, 10, 11],
        "Mjesec": [3, 6, 10, 11],
        "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
        "Merkur": [3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [5, 6, 9, 11],
        "Venera": [6, 7, 12],
        "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
        "Lagna": [3, 4, 6, 10, 11, 12],
    },
    "Mjesec": {
        "Sunce": [3, 6, 7, 8, 10, 11],
        "Mjesec": [1, 3, 6, 7, 10, 11],
        "Mars": [2, 3, 5, 6, 9, 10, 11],
        "Merkur": [1, 3, 4, 5, 7, 8, 10, 11],
        "Jupiter": [1, 4, 7, 8, 10, 11, 12],
        "Venera": [3, 4, 5, 7, 9, 10, 11],
        "Saturn": [3, 5, 6, 11],
        "Lagna": [3, 6, 10, 11],
    },
    "Mars": {
        "Sunce": [3, 5, 6, 10, 11],
        "Mjesec": [3, 6, 11],
        "Mars": [1, 2, 4, 7, 8, 10, 11],
        "Merkur": [3, 5, 6, 11],
        "Jupiter": [6, 10, 11, 12],
        "Venera": [6, 8, 11, 12],
        "Saturn": [1, 4, 7, 8, 9, 10, 11],
        "Lagna": [1, 3, 6, 10, 11],
    },
    "Merkur": {
        "Sunce": [5, 6, 9, 11, 12],
        "Mjesec": [2, 4, 6, 8, 10, 11],
        "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
        "Merkur": [1, 3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [6, 8, 11, 12],
        "Venera": [1, 2, 3, 4, 5, 8, 9, 11],
        "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
        "Lagna": [1, 2, 4, 6, 8, 10, 11],
    },
    "Jupiter": {
        "Sunce": [1, 2, 3, 4, 7, 8, 9, 10, 11],
        "Mjesec": [2, 5, 7, 9, 11],
        "Mars": [1, 2, 4, 7, 8, 10, 11],
        "Merkur": [1, 2, 4, 5, 6, 9, 10, 11],
        "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11],
        "Venera": [2, 5, 6, 9, 10, 11],
        "Saturn": [3, 5, 6, 12],
        "Lagna": [1, 2, 4, 5, 6, 7, 9, 10, 11],
    },
    "Venera": {
        "Sunce": [8, 11, 12],
        "Mjesec": [1, 2, 3, 4, 5, 8, 9, 11, 12],
        "Mars": [3, 5, 6, 9, 11, 12],
        "Merkur": [3, 5, 6, 9, 11],
        "Jupiter": [5, 8, 9, 10, 11],
        "Venera": [1, 2, 3, 4, 5, 8, 9, 10, 11],
        "Saturn": [3, 4, 5, 8, 9, 10, 11],
        "Lagna": [1, 2, 3, 4, 5, 8, 9, 11],
    },
    "Saturn": {
        "Sunce": [1, 2, 4, 7, 8, 10, 11],
        "Mjesec": [3, 6, 11],
        "Mars": [3, 5, 6, 10, 11, 12],
        "Merkur": [6, 8, 9, 10, 11, 12],
        "Jupiter": [5, 6, 11, 12],
        "Venera": [6, 11, 12],
        "Saturn": [3, 5, 6, 11],
        "Lagna": [1, 3, 4, 6, 10, 11],
    },
}

TOTAL_BINDUS = {
    "Sunce": 48, "Mjesec": 49, "Mars": 39, "Merkur": 54,
    "Jupiter": 56, "Venera": 52, "Saturn": 39,
}

# Kakshya (podjela znaka na 8 dijelova od 3°45', vladari fiksnim
# redoslijedom - potvrđeno protiv 2 neovisna izvora): Saturn, Jupiter,
# Mars, Sunce, Venera, Merkur, Mjesec, Lagna. Kad tranzitni planet prolazi
# kroz Kakshyu izvora koji je dao bindu (u tom znaku, za taj planet), to
# je posebno "aktivan" - precizniji (3-4 dana) prozor unutar tranzita kroz
# cijeli znak.
KAKSHYA_ORDER = ["Saturn", "Jupiter", "Mars", "Sunce", "Venera", "Merkur", "Mjesec", "Lagna"]
KAKSHYA_SPAN = 30.0 / 8.0  # 3°45'


def get_kakshya_lord(degree_in_sign: float) -> str:
    """degree_in_sign: 0-30. Vraća naziv vladara Kakshye u kojoj je taj stupanj."""
    index = min(int(degree_in_sign / KAKSHYA_SPAN), 7)
    return KAKSHYA_ORDER[index]


def is_kakshya_activated(scored_planet: str, sign_index: int, kakshya_lord: str,
                          sign_index_by_source: Dict[str, int]) -> bool:
    """
    Provjerava je li Kakshya vladar (kakshya_lord) jedan od izvora koji je
    dao bindu baš OVOM znaku (sign_index) u Bhinnashtakavargi planeta
    scored_planet - ako da, ovaj uski prozor (Kakshya) je posebno aktivan.
    """
    table = BENEFIC_PLACES[scored_planet]
    lord_sign = sign_index_by_source[kakshya_lord]
    for house_offset in table.get(kakshya_lord, []):
        if (lord_sign + house_offset - 1) % 12 == sign_index:
            return True
    return False


def compute_bhinnashtakavarga(planet: str, sign_index_by_source: Dict[str, int]) -> List[int]:
    """
    planet: jedan od ASHTAKAVARGA_PLANETS
    sign_index_by_source: {"Sunce": idx, "Mjesec": idx, ..., "Lagna": idx}
        (sign_index, 0-11, za natalnu poziciju svakog od 8 izvora)
    Vraća listu od 12 brojeva (bindus po znaku, indeks 0=Ovan).
    """
    bindus = [0] * 12
    table = BENEFIC_PLACES[planet]
    for source in _SOURCES:
        source_sign = sign_index_by_source[source]
        for house in table[source]:
            target_sign = (source_sign + house - 1) % 12
            bindus[target_sign] += 1
    return bindus


def compute_sarvashtakavarga(sign_index_by_source: Dict[str, int]) -> List[int]:
    """Zbroj svih 7 Bhinnashtakavarga (bez redukcija). Vraća listu od 12 brojeva."""
    totals = [0] * 12
    for planet in ASHTAKAVARGA_PLANETS:
        bhinna = compute_bhinnashtakavarga(planet, sign_index_by_source)
        for i in range(12):
            totals[i] += bhinna[i]
    return totals
