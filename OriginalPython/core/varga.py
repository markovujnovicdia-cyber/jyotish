"""
Varga (divizijske karte).

Sve implementirane varge (D1, D9, D7, D10, D12) su provjerene i potvrđene
protiv referentne literature (Brihat Parashara Hora Shastra, više
neovisnih izvora i primjera).

Svaka varga funkcija prima apsolutni sidereal stupanj (0-360) i vraća
indeks znaka (0-11) u toj vargi.
"""

from core.constants import RASHI


def d1_sign_index(longitude: float) -> int:
    """D1 / Rashi - osnovni znak, bez podjele."""
    return int((longitude % 360.0) // 30)


def d9_navamsha_sign_index(longitude: float) -> int:
    """
    D9 / Navamsha - stabilna, provjerena formula.

    Svaki znak (30°) dijeli se na 9 dijelova od 3°20'. Zbog specifičnog
    rasporeda (pokretni/nepokretni/dvostruki znakovi) cijela shema se
    matematički svodi na jednostavnu formulu: čitav zodijak (360°) dijeli
    se na 108 jednakih dijelova (12 znakova x 9), a redoslijed navamsha
    znakova kontinuirano kruži kroz sve znakove od Mesha nadalje.
    """
    lon = longitude % 360.0
    part_size = 30.0 / 9.0  # 3°20'
    part_number = int(lon / part_size)  # 0-107
    return part_number % 12


def d1_sign_name(longitude: float) -> str:
    return RASHI[d1_sign_index(longitude)]


def d9_sign_name(longitude: float) -> str:
    return RASHI[d9_navamsha_sign_index(longitude)]


# ---------------------------------------------------------------------------
# D7 (Saptamsha) - PROVJERENO
# Klasično pravilo (BPHS): znak se dijeli na 7 dijelova (~4°17'09" svaki).
# Za neparne znakove brojanje kreće od istog znaka; za parne znakove
# brojanje kreće od 7. znaka od njega. Potvrđeno protiv više neovisnih
# izvora i primjera (npr. Jagannatha Hora dokumentacija).
# ---------------------------------------------------------------------------
def d7_saptamsha_sign_index(longitude: float) -> int:
    lon = longitude % 360.0
    sign = int(lon // 30)
    deg_in_sign = lon - sign * 30
    part_size = 30.0 / 7.0
    n = int(deg_in_sign / part_size)  # 0-6

    is_odd_sign = (sign % 2 == 0)  # Mesha(0), Mithuna(2)... = "neparni" u tradicionalnom brojanju (1.,3.,5. znak)
    start = sign if is_odd_sign else (sign + 6) % 12
    return (start + n) % 12


# ---------------------------------------------------------------------------
# D10 (Dashamsha) - PROVJERENO
# Klasično pravilo (BPHS): znak se dijeli na 10 dijelova (3° svaki). Za
# neparne znakove brojanje kreće od istog znaka; za parne znakove
# brojanje kreće od 9. znaka od njega. Potvrđeno protiv više neovisnih
# izvora i primjera.
# ---------------------------------------------------------------------------
def d10_dashamsha_sign_index(longitude: float) -> int:
    lon = longitude % 360.0
    sign = int(lon // 30)
    deg_in_sign = lon - sign * 30
    part_size = 3.0
    n = int(deg_in_sign / part_size)  # 0-9

    is_odd_sign = (sign % 2 == 0)
    start = sign if is_odd_sign else (sign + 8) % 12
    return (start + n) % 12


# ---------------------------------------------------------------------------
# D12 (Dvadashamsha) - PROVJERENO
# Klasično pravilo (BPHS): znak se dijeli na 12 dijelova (2°30' svaki),
# brojanje UVIJEK kreće od istog znaka (bez razlike parni/neparni).
# Potvrđeno protiv više neovisnih izvora i primjera.
# ---------------------------------------------------------------------------
def d12_dvadashamsha_sign_index(longitude: float) -> int:
    lon = longitude % 360.0
    sign = int(lon // 30)
    deg_in_sign = lon - sign * 30
    part_size = 2.5
    n = int(deg_in_sign / part_size)  # 0-11
    return (sign + n) % 12
