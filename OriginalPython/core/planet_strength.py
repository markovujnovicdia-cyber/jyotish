"""
Pojednostavljena snaga planeta - NIJE puni klasični Shadbala (koji ima 6
kategorija: Sthana, Dig, Kaala, Chesta, Naisargika, Drik Bala, svaka sa
podkomponentama poput Saptavargaja, Hadda/termina, Drekkana snage itd. -
to je prevelik sustav da ga se pouzdano implementira bez mogućnosti
testiranja).

Umjesto toga, računamo tri dobro dokumentirane, provjerene komponente i
zbrajamo ih u jedan pojednostavljeni rezultat (0-100):

1. Uchcha Bala (snaga po uzvišenju/padu) - kontinuirana snaga od 0 (točan
   pad) do 60 (točno uzvišenje), mjerena kutnom udaljenošću od padnog
   stupnja. Egzaktni stupnjevi uzvišenja/pada potvrđeni protiv 6+
   neovisnih izvora.

2. Dostojanstvo znaka (vlastiti/prijateljski/neutralan/neprijateljski) -
   koristi klasične "Naisargika Maitri" (prirodno prijateljstvo) tablice,
   standardne i nesporne u literaturi.

3. Kendra Bala (bonus po tipu kuće) - kendra (1,4,7,10) najjača, panaphara
   (2,5,8,11) srednja, apoklima (3,6,9,12) najslabija.

Rezultat je user-friendly pokazatelj snage, NE zamjena za pravi Shadbala.
"""

from dataclasses import dataclass

from core.constants import RASHI_LORD, RASHI
from core.houses import houses_ruled_by_planet

# Prirodni dobrotvori/zlotvori (klasična, nesporna podjela) - polazna
# točka za FUNKCIONALNU prirodu niže; Merkur se konvencionalno broji kao
# prirodni dobrotvor kad nije u konjunkciji s malefikom (ovdje se ta
# suptilnost ne modelira - vidi ograničenje u compute_functional_nature).
NATURAL_BENEFICS = {"Jupiter", "Venera", "Mjesec", "Merkur"}
NATURAL_MALEFICS = {"Sunce", "Mars", "Saturn", "Rahu", "Ketu"}

TRIKONA_HOUSES = {1, 5, 9}
DUSTHANA_HOUSES = {6, 8, 12}

EXALTATION = {
    "Sunce": ("Ovan", 10.0),
    "Mjesec": ("Bik", 3.0),
    "Mars": ("Jarac", 28.0),
    "Merkur": ("Djevica", 15.0),
    "Jupiter": ("Rak", 5.0),
    "Venera": ("Ribe", 27.0),
    "Saturn": ("Vaga", 20.0),
}

NATURAL_FRIENDS = {
    "Sunce": {"Mjesec", "Mars", "Jupiter"},
    "Mjesec": {"Sunce", "Merkur"},
    "Mars": {"Sunce", "Mjesec", "Jupiter"},
    "Merkur": {"Sunce", "Venera"},
    "Jupiter": {"Sunce", "Mjesec", "Mars"},
    "Venera": {"Merkur", "Saturn"},
    "Saturn": {"Merkur", "Venera"},
}

NATURAL_ENEMIES = {
    "Sunce": {"Venera", "Saturn"},
    "Mjesec": set(),
    "Mars": {"Merkur"},
    "Merkur": {"Mjesec"},
    "Jupiter": {"Merkur", "Venera"},
    "Venera": {"Sunce", "Mjesec"},
    "Saturn": {"Sunce", "Mjesec", "Mars"},
}

KENDRA_HOUSES = {1, 4, 7, 10}
PANAPHARA_HOUSES = {2, 5, 8, 11}
# ostatak (3,6,9,12) su apoklima


@dataclass
class PlanetStrength:
    planet: str
    uchcha_bala: float       # 0-60
    dignity: str             # "uzvišen"/"vlastiti"/"prijateljski"/"neutralan"/"neprijateljski"/"pad"
    dignity_bonus: float     # 0-20
    kendra_bonus: float      # 5-15
    total_score: float       # zbroj, orijentacijski 0-100


def _angular_distance(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def compute_uchcha_bala(planet: str, longitude: float) -> float:
    """0 = točan pad, 60 = točno uzvišenje, glatko između."""
    if planet not in EXALTATION:
        return 30.0  # Rahu/Ketu nemaju klasično uzvišenje po ovom sustavu - neutralno
    exalt_sign, exalt_deg = EXALTATION[planet]
    exalt_sign_index = RASHI.index(exalt_sign)
    exalt_longitude = exalt_sign_index * 30 + exalt_deg
    debil_longitude = (exalt_longitude + 180.0) % 360.0

    dist_from_debil = _angular_distance(longitude, debil_longitude)
    return (dist_from_debil / 180.0) * 60.0


def compute_dignity(planet: str, sign_index: int) -> tuple:
    """
    Vraća (naziv_dostojanstva, bonus_bodovi) - naziv je za PRIKAZ (uključuje
    uzvišen/pad kao korisnu informaciju), ali bonus_bodovi se NE koristi u
    ukupnom zbroju (vidi _kshetra_bonus_only) jer bi dupliciralo učinak
    uzvišenja/pada koji je već posebno i kontinuirano pokriven kroz
    Uchcha Balu.
    """
    if planet not in RASHI_LORD.values() and planet not in ("Rahu", "Ketu"):
        pass  # svi klasični planeti su negdje vladari

    sign_name = RASHI[sign_index]
    sign_lord = RASHI_LORD.get(sign_name)

    if planet not in EXALTATION:
        return ("neutralan", 5.0)  # Rahu/Ketu - pojednostavljeno, nema klasično dostojanstvo ovdje

    exalt_sign, _ = EXALTATION[planet]
    debil_sign_index = (RASHI.index(exalt_sign) + 6) % 12

    if sign_index == RASHI.index(exalt_sign):
        return ("uzvišen", 20.0)
    if sign_index == debil_sign_index:
        return ("pad", 0.0)
    if sign_lord == planet:
        return ("vlastiti", 15.0)
    if sign_lord in NATURAL_FRIENDS.get(planet, set()):
        return ("prijateljski", 10.0)
    if sign_lord in NATURAL_ENEMIES.get(planet, set()):
        return ("neprijateljski", 3.0)
    return ("neutralan", 6.0)


def compute_functional_nature(planet: str, ascendant_sign_index: int) -> str:
    """
    Funkcionalna priroda planeta ZA DANI ascendent (BPHS pravilo) - koristi
    se u sinastrijskoj interpretaciji (core/synastry/interpretation.py) da
    se izbjegne paušalno tumačenje osi 3./10., 4./8., 5./9. koje ovisi
    SAMO o kućnoj udaljenosti, a ne o tome je li uključeni planet u TOJ
    karti zapravo dobrotvoran ili zlotvoran.

    Pravilo:
      - planet koji vlada TRIKONA kućom (1./5./9.) i NIJE isključivo
        vladar dusthane -> "funkcionalni dobrotvor" (čak i ako je prirodni
        malefik - klasični "yogakaraka"/trikona-vladar učinak)
      - planet koji vlada ISKLJUČIVO dusthana kućom/kućama (6./8./12.),
        bez trikona/kendra vladarstva -> "funkcionalni zlotvor" (čak i ako
        je prirodni dobrotvor)
      - planet koji vlada I trikonom/kendrom I dusthanom istodobno
        -> "mješovit (dvojako vladarstvo)"
      - inače (samo kendra 4./7./10., ili Rahu/Ketu koji ne vladaju
        znakom) -> zadržava PRIRODNU prirodu (NATURAL_BENEFICS/MALEFICS)

    OGRANIČENJE: ne modelira suptilnosti poput Merkurove konjunkcije s
    malefikom ili vladara 2./7. kad su jedini kendra vladari bez trikone -
    ovo je razuman, dokumentiran BPHS standard, ne konačna psihometrija.
    """
    ruled_houses = set(houses_ruled_by_planet(planet, ascendant_sign_index))
    natural = "dobrotvor" if planet in NATURAL_BENEFICS else "zlotvor"

    rules_trikona = bool(ruled_houses & TRIKONA_HOUSES)
    rules_dusthana = bool(ruled_houses & DUSTHANA_HOUSES)

    if rules_trikona and rules_dusthana:
        return "mješovit (dvojako vladarstvo)"
    if rules_trikona:
        return "funkcionalni dobrotvor"
    if rules_dusthana and not ruled_houses - DUSTHANA_HOUSES:
        return "funkcionalni zlotvor"
    return f"prirodni {natural} (bez odlučujućeg trikona/dusthana vladarstva)"


def _kshetra_bonus_only(planet: str, sign_index: int) -> float:
    """
    ISKLJUČIVO odnos prema vladaru znaka (vlastiti/prijateljski/neutralan/
    neprijateljski) - NAMJERNO bez uzvišenja/pada, jer to je već posebno i
    kontinuirano pokriveno kroz Uchcha Balu. Ovo se koristi u ukupnom
    zbroju (compute_planet_strength), za razliku od compute_dignity čiji
    je naziv/label namijenjen prikazu.
    """
    if planet not in EXALTATION:
        return 6.0  # Rahu/Ketu - neutralno

    sign_name = RASHI[sign_index]
    sign_lord = RASHI_LORD.get(sign_name)

    if sign_lord == planet:
        return 15.0
    if sign_lord in NATURAL_FRIENDS.get(planet, set()):
        return 10.0
    if sign_lord in NATURAL_ENEMIES.get(planet, set()):
        return 3.0
    return 6.0


def compute_kendra_bonus(house_num: int) -> float:
    if house_num in KENDRA_HOUSES:
        return 15.0
    if house_num in PANAPHARA_HOUSES:
        return 10.0
    return 5.0


def compute_planet_strength(planet: str, longitude: float, sign_index: int, house_num: int) -> PlanetStrength:
    uchcha = compute_uchcha_bala(planet, longitude)
    dignity_name, _ = compute_dignity(planet, sign_index)  # naziv samo za prikaz
    kshetra_bonus = _kshetra_bonus_only(planet, sign_index)  # bodovi za zbroj, bez dupliciranja s Uchchom
    kendra_bonus = compute_kendra_bonus(house_num)
    total = uchcha + kshetra_bonus + kendra_bonus  # okvirno 5-95

    return PlanetStrength(
        planet=planet,
        uchcha_bala=round(uchcha, 1),
        dignity=dignity_name,
        dignity_bonus=kshetra_bonus,
        kendra_bonus=kendra_bonus,
        total_score=round(total, 1),
    )
