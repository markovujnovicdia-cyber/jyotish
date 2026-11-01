"""
Izračun kuća (bhava).

Glavni sustav: Whole Sign (cijeli znak) - najjednostavniji i klasični
sustav u Jyotishu. Znak u kojem je ascendent postaje 1. kuća u cijelosti,
sljedeći znak 2. kuća, itd.

Bhava Chalit - dodatni prikaz koji koristi TOČAN stupanj ascendenta kao
SREDINU 1. kuće (ne njen početak), pa svaka kuća obuhvaća 15° prije i 15°
poslije svoje sredine. Ovo je "Bhava Madhya" metoda - najrašireniji i
najjednostavniji od nekoliko postojećih Bhava Chalit pristupa (potvrđeno
kao "popularnija metoda" u više izvora). Planeti blizu granice dvije kuće
(Whole Sign) mogu se u Bhava Chalitu prebaciti u susjednu kuću.

Napomena: postoji i složenija, "prava" Sripati metoda koja koristi stvarni
MC (Medium Coeli) i trisekciju kvadranata - NIJE ovdje implementirana jer
zahtijeva dodatni astronomski izračun (MC) i njegovu pouzdanost nisam
mogao provjeriti bez mogućnosti testiranja u ovom okruženju.
"""

from typing import List

from core.constants import RASHI, RASHI_LORD


def whole_sign_house(planet_sign_index: int, ascendant_sign_index: int) -> int:
    """
    Vraća broj kuće (1-12) po Whole Sign sustavu.
    Kuća = razlika indeksa znakova + 1, modulo 12.
    """
    house = (planet_sign_index - ascendant_sign_index) % 12 + 1
    return house


def ascendant_sign_index(ascendant_longitude: float) -> int:
    return int((ascendant_longitude % 360.0) // 30)


def ascendant_sign_name(ascendant_longitude: float) -> str:
    return RASHI[ascendant_sign_index(ascendant_longitude)]


def bhava_chalit_house(planet_longitude: float, ascendant_longitude: float) -> int:
    """
    Bhava Chalit (Bhava Madhya) kuća za zadani planet - ascendent je
    SREDINA 1. kuće, svaka kuća 30° široka (15° prije i 15° poslije svoje
    sredine).
    """
    diff = (planet_longitude - ascendant_longitude + 15.0) % 360.0
    house = int(diff // 30.0) + 1
    return house


def houses_ruled_by_planet(planet: str, ascendant_sign_idx: int) -> List[int]:
    """
    Vraća listu kuća (1-12, Whole Sign) kojima planet vlada u zadanoj karti
    (određenoj svojim ascendentom). Obično 1 ili 2 kuće; Rahu/Ketu ne
    vladaju nijednim znakom pa vraćaju praznu listu. Koristi se npr. u
    sinastriji za prikaz "koje kuće u SVOJOJ karti planet vlada".
    """
    houses = []
    for sign_index, sign_name in enumerate(RASHI):
        if RASHI_LORD.get(sign_name) == planet:
            houses.append(whole_sign_house(sign_index, ascendant_sign_idx))
    return houses
