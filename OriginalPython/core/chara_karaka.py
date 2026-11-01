"""
Chara Karake (Jaimini) - planeti rangirani po stupnju UNUTAR svog znaka
(0-30°), od najvišeg prema najnižem. Najviši stupanj = Atmakaraka (AK,
"signifikator duše/sebe"), najniži = Darakaraka (DK, "signifikator
supružnika/partnera") - DK je ključan za sinastriju (2.7, 2.8 u
specifikaciji), AK se koristi za usporedbu s Darakarakom druge osobe.

NAPOMENA - ništa slično ovome nije prije postojalo u projektu (core/ nije
sadržavao Chara Karaka izračun), pa je ovo NOVI modul dodan za potrebe
sinastrije (Faza 2).

Dvije klasične sheme (BPHS eksplicitno opisuje obje - izbor je konfigurabilan,
core/synastry/config.py):

- "7_karaka" (zadano): koristi se 7 klasičnih grahe (Sunce...Saturn), BEZ
  čvorova. Ovo je izvorna, najraširenija Parashara/Jaimini shema.
  Redoslijed (najviši stupanj -> najniži): Atmakaraka (AK), Amatyakaraka
  (AmK), Bhratrikaraka (BK), Matrikaraka (MK), Putrakaraka (PK),
  Gnatikaraka (GK), Darakaraka (DK).

- "8_karaka": dodaje Rahu (Ketu se NIKAD ne koristi kao karaka, ni u jednoj
  shemi - nesporno u svim izvorima). Redoslijed s 8 planeta koristi
  dodatni naziv "Pitrikaraka" (otac) umjesto dvostrukog Matri/Putra u
  istom nizu - izvori se RAZLIKUJU oko točnog rasporeda SREDNJIH naziva
  (Bhratri/Matri/Pitri/Putra/Gnati) kad se doda 8. planet, pa su ovdje ti
  srednji nazivi označeni kao INFORMATIVNI/manje pouzdani. AK (najviši
  stupanj) i DK (najniži stupanj) su POUZDANI u obje sheme - to su i
  jedina dva karaka koja specifikacija sinastrije zahtijeva.

ISPRAVAK - Rahuov OBRNUTI stupanj u "8_karaka" shemi: Rahu se klasično
uvijek kreće retrogradno, pa se za RANGIRANJE karaka koristi obrnut
stupanj (30° - stvarni stupanj unutar znaka), ne stvarni stupanj izravno
(standardna Jaimini konvencija - vidi npr. Jagannatha Hora i većinu
modernih komentara Jaimini Sutri). Ovo utječe SAMO na rang/poredak - polje
degree_in_sign u rezultatu i dalje prikazuje STVARNI (neobrnuti) stupanj,
radi ispravnog prikaza korisniku.

Izjednačeni stupnjevi (praktički se ne događaju sa stvarnim efemeridama,
ali su teoretski mogući): razrješava se po klasičnom "brže prvo" pravilu
(core.tajika.SPEED_ORDER) - brži planet dobiva viši rang.
"""

from dataclasses import dataclass
from typing import Dict, List

from core.tajika import SPEED_ORDER

KARAKA_NAMES_7 = [
    "Atmakaraka", "Amatyakaraka", "Bhratrikaraka", "Matrikaraka",
    "Putrakaraka", "Gnatikaraka", "Darakaraka",
]

# Srednji nazivi u 8-karaka shemi - manje pouzdani/skloniji varijacijama
# među izvorima (vidi napomenu na vrhu datoteke). AK (indeks 0) i DK
# (indeks 7, zadnji) su pouzdani.
KARAKA_NAMES_8 = [
    "Atmakaraka", "Amatyakaraka", "Bhratrikaraka", "Matrikaraka",
    "Pitrikaraka", "Putrakaraka", "Gnatikaraka", "Darakaraka",
]

_SPEED_RANK = {name: i for i, name in enumerate(SPEED_ORDER)}


@dataclass
class CharaKarakaResult:
    planet: str
    karaka_name: str
    rank: int              # 0 = Atmakaraka (najviši stupanj)
    degree_in_sign: float


def compute_chara_karakas(
    positions: Dict[str, "core.ephemeris.PlanetPosition"],
    scheme: str = "7_karaka",
) -> List[CharaKarakaResult]:
    """
    positions: {naziv_planeta: PlanetPosition} - očekuje barem 7 klasičnih
    grahe (Sunce...Saturn); za "8_karaka" shemu očekuje i Rahu. Ketu se
    NIKAD ne koristi.

    Vraća listu CharaKarakaResult sortiranu od Atmakarake (rank 0) prema
    Darakaraki (zadnji rank) - stupanj unutar znaka, silazno.
    """
    if scheme == "8_karaka":
        candidates = ["Sunce", "Mjesec", "Mars", "Merkur", "Jupiter", "Venera", "Saturn", "Rahu"]
        karaka_names = KARAKA_NAMES_8
    else:
        candidates = ["Sunce", "Mjesec", "Mars", "Merkur", "Jupiter", "Venera", "Saturn"]
        karaka_names = KARAKA_NAMES_7

    entries = [(p, positions[p].degree_in_sign) for p in candidates if p in positions]

    def _ranking_degree(planet: str, degree: float) -> float:
        # Rahu je uvijek retrogradan - za RANGIRANJE (ne za prikaz) koristi
        # se obrnut stupanj (vidi napomenu na vrhu datoteke).
        if planet == "Rahu":
            return 30.0 - degree
        return degree

    def sort_key(entry):
        planet, degree = entry
        # sekundarni kriterij (izjednačeni stupnjevi): brži planet više -
        # SPEED_ORDER je poredan od najbrže prema najsporijoj, pa NIŽI
        # _SPEED_RANK treba dati VIŠI (bolji) rang pri izjednačenom stupnju.
        return (-_ranking_degree(planet, degree), _SPEED_RANK.get(planet, 99))

    entries.sort(key=sort_key)

    return [
        CharaKarakaResult(planet=planet, karaka_name=karaka_names[i], rank=i, degree_in_sign=degree)
        for i, (planet, degree) in enumerate(entries)
    ]


def get_atmakaraka(positions, scheme: str = "7_karaka") -> CharaKarakaResult:
    return compute_chara_karakas(positions, scheme)[0]


def get_darakaraka(positions, scheme: str = "7_karaka") -> CharaKarakaResult:
    return compute_chara_karakas(positions, scheme)[-1]
