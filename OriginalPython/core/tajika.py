"""
Tajika sustav (koristi se u Varshaphali/godišnjoj karti) - Perso-arapski
sloj vedske astrologije, drukčiji od klasičnog Parashara sustava.

OPSEG OVE IMPLEMENTACIJE (namjerno ograničen, radije jasno reći što
NIJE napravljeno nego nagađati pogrešnu formulu):

Implementirano:
- Tajika aspekti (5 vrsta: konjunkcija, sekstil, kvadrat, trigon, opozicija)
  između svih parova od 7 klasičnih planeta (Rahu/Ketu se NE koriste u
  Tajika sustavu - potvrđeno u više izvora)
- Deeptamsha (orb) svake planete i kombinirani orb para
- Ithasala yoga (planet se približava - "primjenjujući" aspekt unutar orba)
- Isarapha yoga (planet se udaljava - "razdvajajući" aspekt unutar orba)
- Kamboola yoga se provjerava za konkretan Lagnesha/Karyesha par
  (dodatna Mjesečeva Ithasala), ne globalno na svakom Mjesečevom paru
- 5 Sahama (od klasičnih 16): Punya, Vidya, Yasha, Vivaha, Putra

NIJE implementirano OVDJE (namjerno - vidi core/karyesha_yogas.py za 7
dodatnih yoga koje ZAHTIJEVAJU odabir Karyesha/životnog područja: Nakta,
Yamaya, Manau, Kambula (za specifičan par), Radda, Duparikutha, Durupha):
- Preostalih 11 od 16 klasičnih Sahama (Shatru, Bandhu, Mrityu, Matru,
  Pitru, Rajya, Arogya, Dhana, Griha, Karma, Saubhagya, Paradesa) -
  temeljito istraženo, ali za nekoliko od njih pronađene su MEĐUSOBNO
  PROTUSLOVNE formule u različitim izvorima (npr. Karma Saham naveden i
  kao "Mars-Merkur+Lagna" i kao "Sunce-Saturn+Lagna"), a za ostale nije
  pronađena dovoljno pouzdana/ponovljena formula - radije ostaviti
  neimplementirano nego nagađati koja je verzija ispravna.
- Provjera kombustije (planet preblizu Suncu) kao dodatnog uvjeta za
  jačinu yoge.

Sve formule potvrđene protiv više neovisnih izvora prije implementacije.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# Deeptamsha (orb utjecaja) svake planete, u stupnjevima
DEEPTAMSHA = {
    "Sunce": 15.0,
    "Mjesec": 12.0,
    "Mars": 8.0,
    "Merkur": 7.0,
    "Jupiter": 9.0,
    "Venera": 7.0,
    "Saturn": 9.0,
}

# Tradicionalni redoslijed normalne brzine. Za status primjene/separacije
# KORISTIMO STVARNE efemeridne brzine kad su dostupne; retrogradni
# predznaci i stacionarnost mogu izmijeniti odnos. Fallback ispod služi
# samo pozivateljima koji nemaju efemeridnu brzinu.
SPEED_ORDER = ["Mjesec", "Merkur", "Venera", "Sunce", "Mars", "Jupiter", "Saturn"]

TAJIKA_PLANETS = SPEED_ORDER  # Rahu/Ketu se ne koriste u Tajika sustavu

_ASPECT_BY_SIGN_DISTANCE = {
    0: "konjunkcija",
    2: "sekstil", 10: "sekstil",
    3: "kvadrat", 9: "kvadrat",
    4: "trigon", 8: "trigon",
    6: "opozicija",
}
_ASPECT_EXACT_DEGREE = {
    "konjunkcija": 0.0,
    "sekstil": 60.0,
    "kvadrat": 90.0,
    "trigon": 120.0,
    "opozicija": 180.0,
}


@dataclass
class PlanetPairRelation:
    planet_a: str
    planet_b: str
    faster: str
    slower: str
    aspect: Optional[str]  # None ako nema Tajika aspekta između njih
    orb_diff: float        # koliko su stupnjeva udaljeni od TOČNOG kuta aspekta
    combined_orb: float
    within_orb: bool
    is_applying: bool      # True = približava se, False = udaljava se ili egzaktno
    is_exact: bool = False
    is_separating: bool = False
    relative_speed: float = 0.0


def _sign_index(longitude: float) -> int:
    return int(longitude % 360.0 // 30)


# Srednje prividne dnevne brzine (°/dan) služe SAMO za stari API kad
# efemeridne brzine nisu proslijeđene. Za godišnju kartu uvijek se koriste
# stvarne brzine iz Swiss Ephemerisa.
_MEAN_SPEED = {"Mjesec": 13.176, "Merkur": 1.20, "Venera": 1.18,
               "Sunce": 0.986, "Mars": 0.524, "Jupiter": 0.083,
               "Saturn": 0.034}


def _signed_angle(value: float) -> float:
    return (value + 180.0) % 360.0 - 180.0


def _exact_aspect_residual(lon_a: float, lon_b: float, aspect: str) -> float:
    """Signed residual to nearest of ±sextile/square/trine, 0 or 180.

    Both aspect orientations are necessary: 125° Moon, 5° Mars is
    exactly a trine, regardless of the input order of the planets.
    """
    angle = _ASPECT_EXACT_DEGREE[aspect]
    targets = (0.0,) if angle == 0 else ((180.0,) if angle == 180 else (angle, -angle))
    direction = _signed_angle(lon_b - lon_a)
    return min((_signed_angle(direction - target) for target in targets), key=abs)


def analyze_pair(
    planet_a: str, lon_a: float, retro_a: bool,
    planet_b: str, lon_b: float, retro_b: bool,
    speed_a: Optional[float] = None, speed_b: Optional[float] = None,
) -> PlanetPairRelation:
    """Tajika sign-aspect and local applying/separating classification.

    speed_a/speed_b are signed longitude speeds in degrees/day. Exact aspects
    are separate from both Ithasala and Isharafa; this avoids false positives
    at the moment of exactitude. For historical callers using just booleans,
    the fallback approximates signed speeds and is not ephemeris-precise.
    """
    if planet_a == planet_b:
        raise ValueError("Tajika requires two different planets")
    sign_dist = (_sign_index(lon_b) - _sign_index(lon_a)) % 12
    aspect = _ASPECT_BY_SIGN_DISTANCE.get(sign_dist)
    faster, slower = (planet_a, planet_b) if SPEED_ORDER.index(planet_a) < SPEED_ORDER.index(planet_b) else (planet_b, planet_a)
    combined_orb = (DEEPTAMSHA[planet_a] + DEEPTAMSHA[planet_b]) / 2.0
    if aspect is None:
        return PlanetPairRelation(planet_a, planet_b, faster, slower, None, 999.0, combined_orb, False, False)

    residual = _exact_aspect_residual(lon_a, lon_b, aspect)
    orb_diff = abs(residual)
    within_orb = orb_diff <= combined_orb + 1e-10
    exact = orb_diff < 1e-8
    vel_a = speed_a if speed_a is not None else _MEAN_SPEED[planet_a] * (-1 if retro_a else 1)
    vel_b = speed_b if speed_b is not None else _MEAN_SPEED[planet_b] * (-1 if retro_b else 1)
    relative_speed = vel_b - vel_a
    approaching = (residual * relative_speed) < -1e-10 and not exact
    separating = (residual * relative_speed) > 1e-10 and not exact
    return PlanetPairRelation(planet_a, planet_b, faster, slower, aspect,
                              orb_diff, combined_orb, within_orb, approaching,
                              exact, separating, relative_speed)


def _unpack_position(position):
    """Accept (lon, retro) and (lon, retro, signed_speed) for compatibility."""
    if len(position) == 2:
        longitude, retrograde = position
        return longitude, retrograde, None
    longitude, retrograde, signed_speed = position
    return longitude, retrograde, signed_speed


def _relations(positions: dict) -> List[PlanetPairRelation]:
    names = list(positions)
    return [analyze_pair(a, *_unpack_position(positions[a])[:2],
                         b, *_unpack_position(positions[b])[:2],
                         _unpack_position(positions[a])[2], _unpack_position(positions[b])[2])
            for i, a in enumerate(names) for b in names[i+1:]]


def find_ithasala_pairs(positions: dict) -> List[PlanetPairRelation]:
    return [r for r in _relations(positions) if r.aspect and r.within_orb and r.is_applying]


def find_isarapha_pairs(positions: dict) -> List[PlanetPairRelation]:
    return [r for r in _relations(positions) if r.aspect and r.within_orb and r.is_separating]


def find_kamboola_pairs(ithasala_pairs: List[PlanetPairRelation]) -> List[PlanetPairRelation]:
    """Deprecated old API: do NOT mistake every Moon Ithasala for Kamboola.

    Kamboola additionally requires a *third-party* Ithasala between the two
    relevant significators. Without Lagnesha/Karyesha context we cannot prove
    it. Use core.karyesha_yogas.analyze_karyesha_yogas instead.
    """
    return []


# --- Sahami (samo 4 od klasičnih 16, dobro potvrđeni formulom) ---

def _norm(deg: float) -> float:
    return deg % 360.0


def compute_saham_punya(asc_lon: float, sun_lon: float, moon_lon: float, is_day_birth: bool) -> float:
    """Sreća/zaštita. Dan: Mjesec-Sunce+Asc. Noć: Sunce-Mjesec+Asc."""
    from core.sahams import saham_arc
    return saham_arc(moon_lon, sun_lon, asc_lon) if is_day_birth else saham_arc(sun_lon, moon_lon, asc_lon)


def compute_saham_vidya(asc_lon: float, sun_lon: float, moon_lon: float, is_day_birth: bool) -> float:
    """Obrazovanje/učenje. Obrnuto od Punya sahama."""
    from core.sahams import saham_arc
    return saham_arc(sun_lon, moon_lon, asc_lon) if is_day_birth else saham_arc(moon_lon, sun_lon, asc_lon)


def compute_saham_yasha(asc_lon: float, jupiter_lon: float, punya_saham_lon: float) -> float:
    """Slava/ugled. Jupiter - Punya Saham + Asc."""
    from core.sahams import saham_arc
    return saham_arc(jupiter_lon, punya_saham_lon, asc_lon)


def compute_saham_vivaha(asc_lon: float, venus_lon: float, saturn_lon: float) -> float:
    """Brak. Venera - Saturn + Asc (isto za dan i noć)."""
    from core.sahams import saham_arc
    return saham_arc(venus_lon, saturn_lon, asc_lon)


def compute_saham_putra(asc_lon: float, jupiter_lon: float, moon_lon: float) -> float:
    """Djeca/potomstvo. Jupiter - Mjesec + Asc (isto za dan i noć).
    Potvrđeno protiv 2 neovisna izvora bez sukoba formule."""
    from core.sahams import saham_arc
    return saham_arc(jupiter_lon, moon_lon, asc_lon)


# NAPOMENA o preostalih 11 od klasičnih 16 Sahama (Shatru, Bandhu, Mrityu,
# Matru, Pitru, Rajya, Arogya, Dhana, Griha, Karma, Saubhagya, Paradesa):
# Istraženo opsežno prije implementacije - za nekoliko od njih (npr. Karma,
# Pitru/Rajya) pronađene su MEĐUSOBNO PROTUSLOVNE formule u različitim
# izvorima (npr. Karma Saham naveden i kao "Mars-Merkur+Lagna" i kao
# "Sunce-Saturn+Lagna" u različitim tablicama), a za ostale nije pronađena
# dovoljno pouzdana/ponovljena formula. Radije ih ne implementirati nego
# nagađati koja je verzija ispravna - vidi raspravu u kodu ako se odluči
# dodati ih uz jasnu naznaku koje škole/izvora se prati.
