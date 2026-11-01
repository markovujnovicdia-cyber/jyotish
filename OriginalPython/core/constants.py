"""
Astrološke konstante za Jyotish aplikaciju.

Napomena o jeziku:
- Nazivi planeta ostaju kako je korisnik naveo (hrvatski, uobičajeni nazivi).
- Nazivi rashi (znakova) su na hrvatskom (Ovan, Bik, ...).
- Nazivi nakshatri ostaju sanskrtski, jer je to standard u vedskoj
  astrologiji i lakše se prati literatura.
"""

# --- Rashi (12 zodijačkih znakova), redom od Ovna (0°) do Riba ---
RASHI = [
    "Ovan",
    "Bik",
    "Blizanci",
    "Rak",
    "Lav",
    "Djevica",
    "Vaga",
    "Škorpion",
    "Strijelac",
    "Jarac",
    "Vodenjak",
    "Ribe",
]

# Vladari znakova (klasični, ne moderni vladari za Rahu/Ketu jer oni nemaju znak)
RASHI_LORD = {
    "Ovan": "Mars",
    "Bik": "Venera",
    "Blizanci": "Merkur",
    "Rak": "Mjesec",
    "Lav": "Sunce",
    "Djevica": "Merkur",
    "Vaga": "Venera",
    "Škorpion": "Mars",
    "Strijelac": "Jupiter",
    "Jarac": "Saturn",
    "Vodenjak": "Saturn",
    "Ribe": "Jupiter",
}

# --- Planeti koje aplikacija prati (bez Lagne, koja se računa posebno) ---
# Redoslijed prikaza u tablicama
PLANET_ORDER = ["Sunce", "Mjesec", "Mars", "Merkur", "Jupiter", "Venera", "Saturn", "Rahu", "Ketu"]

# Kratice od dva slova, za prikaz na kotaču (gdje nema mjesta za pun naziv)
PLANET_ABBR = {
    "Sunce": "Su",
    "Mjesec": "Mj",
    "Mars": "Ma",
    "Merkur": "Me",
    "Jupiter": "Ju",
    "Venera": "Ve",
    "Saturn": "Sa",
    "Rahu": "Ra",
    "Ketu": "Ke",
}

# --- 27 Nakshatri, redom od 0° Mesha ---
NAKSHATRA = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

NAKSHATRA_ABBR = [
    "Asw", "Bha", "Kri", "Roh", "Mrg", "Ard", "Pun", "Pus", "Asl", "Mag", "PPh", "UPh",
    "Has", "Chi", "Swa", "Vis", "Anu", "Jye", "Mul", "PAs", "UAs", "Shr", "Dha", "Sht",
    "PBh", "UBh", "Rev",
]

# --- Vladajuće božanstvo (devata) svake nakshatre - standardna, nesporna
# tablica (ista u BPHS i svim glavnim izvorima). Koristi se za nakshatra
# sinastriju (core/synastry/nakshatra_matching.py) - isključivo opisno,
# nema bodovnu ulogu.
NAKSHATRA_DEVATA = [
    "Ashwini Kumaras", "Yama", "Agni", "Brahma (Prajapati)", "Soma (Chandra)", "Rudra",
    "Aditi", "Brihaspati", "Nagas (Sarpa)", "Pitri devovi", "Bhaga", "Aryaman",
    "Savitar", "Tvashtar (Vishwakarma)", "Vayu", "Indra-Agni", "Mitra", "Indra",
    "Nirriti", "Apas", "Vishvedevas", "Vishnu", "Vasu (8 Vasua)", "Varuna",
    "Aja Ekapada", "Ahir Budhnya", "Pushan",
]

# --- Gana (Deva/Manushya/Rakshasa) svake nakshatre - standardna tablica,
# koristi se i za nakshatra sinastriju i za Gana Kootu (core/synastry/ashtakoota.py).
# 9 nakshatri svake vrste (nesporno, ista raspodjela u svim glavnim izvorima).
NAKSHATRA_GANA = [
    "Deva", "Manushya", "Rakshasa", "Manushya", "Deva", "Manushya",
    "Deva", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya",
    "Deva", "Rakshasa", "Deva", "Rakshasa", "Deva", "Rakshasa",
    "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Rakshasa",
    "Manushya", "Manushya", "Deva",
]

# --- Yoni (životinjski simbol + spol) svake nakshatre - standardna tablica
# (14 životinja, svaka se ponavlja s oba spola kroz 27 nakshatri, uz jednu
# preklapajuću - Ashwini/Shatabhisha oboje "Konj"). Koristi se za nakshatra
# sinastriju i Yoni Kootu.
NAKSHATRA_YONI = [
    ("Konj", "m"), ("Slon", "m"), ("Ovca", "ž"), ("Zmija", "m"), ("Zmija", "ž"), ("Pas", "ž"),
    ("Mačka", "ž"), ("Ovca", "m"), ("Mačka", "m"), ("Štakor", "m"), ("Štakor", "ž"), ("Krava", "ž"),
    ("Bivol", "ž"), ("Tigar", "ž"), ("Bivol", "m"), ("Tigar", "m"), ("Jelen", "ž"), ("Jelen", "m"),
    ("Pas", "m"), ("Majmun", "m"), ("Mungos", "m"), ("Majmun", "ž"), ("Lav", "ž"), ("Konj", "ž"),
    ("Lav", "m"), ("Krava", "m"), ("Slon", "ž"),
]

# --- Nadi (Vata/Pitta/Kapha) svake nakshatre - periodičan obrazac perioda 6
# (Vata,Pitta,Kapha,Kapha,Pitta,Vata), ponavlja se 4x + prva 3 od 5. ciklusa
# (27 = 4*6 + 3). Provjereno protiv standardne Ashtakoota literature.
_NADI_CYCLE = ["Vata", "Pitta", "Kapha", "Kapha", "Pitta", "Vata"]
NAKSHATRA_NADI = [_NADI_CYCLE[i % 6] for i in range(27)]

# --- Varna (po elementu znaka) - standardna, nesporna tablica.
# Voda (Rak, Škorpion, Ribe) = Brahmin, Vatra (Ovan, Lav, Strijelac) = Kshatriya,
# Zemlja (Bik, Djevica, Jarac) = Vaishya, Zrak (Blizanci, Vaga, Vodenjak) = Shudra.
# Hijerarhija (za Varna Kootu): Brahmin > Kshatriya > Vaishya > Shudra.
RASHI_VARNA = {
    "Ovan": "Kshatriya", "Bik": "Vaishya", "Blizanci": "Shudra", "Rak": "Brahmin",
    "Lav": "Kshatriya", "Djevica": "Vaishya", "Vaga": "Shudra", "Škorpion": "Brahmin",
    "Strijelac": "Kshatriya", "Jarac": "Vaishya", "Vodenjak": "Shudra", "Ribe": "Brahmin",
}
VARNA_RANK = {"Brahmin": 4, "Kshatriya": 3, "Vaishya": 2, "Shudra": 1}

# --- Vashya (skupina "vladanja/kontrole") po znaku - standardna tablica iz
# 5 skupina: Chatushpada (četveronožac), Manava (čovjek), Jalachara (vodeno
# biće), Vanachara (šumska/divlja životinja), Keeta (insekt). Škorpion se
# klasično dijeli - prva polovica Keeta, druga Jalachara; ovdje pojednostavljeno
# kao Keeta (uobičajena pojednostavljena konvencija u softveru), naznačeno.
RASHI_VASHYA_GROUP = {
    "Ovan": "Chatushpada", "Bik": "Chatushpada", "Blizanci": "Manava", "Rak": "Jalachara",
    "Lav": "Vanachara", "Djevica": "Manava", "Vaga": "Manava", "Škorpion": "Keeta",
    "Strijelac": "Manava", "Jarac": "Chatushpada", "Vodenjak": "Manava", "Ribe": "Jalachara",
}

# --- Element (Vatra/Zemlja/Zrak/Voda) po znaku - standardna, nesporna
# tablica. Koristi se za "element pade" u nakshatra sinastriji (D9 znak
# pade određuje element).
RASHI_ELEMENT = {
    "Ovan": "Vatra", "Lav": "Vatra", "Strijelac": "Vatra",
    "Bik": "Zemlja", "Djevica": "Zemlja", "Jarac": "Zemlja",
    "Blizanci": "Zrak", "Vaga": "Zrak", "Vodenjak": "Zrak",
    "Rak": "Voda", "Škorpion": "Voda", "Ribe": "Voda",
}

# Vladari nakshatri, redom (koristi se za Vimshottari dashu)
# Ciklus: Ketu, Venera, Sunce, Mjesec, Mars, Rahu, Jupiter, Saturn, Merkur (ponavlja se 3x)
NAKSHATRA_LORD_CYCLE = ["Ketu", "Venera", "Sunce", "Mjesec", "Mars", "Rahu", "Jupiter", "Saturn", "Merkur"]
NAKSHATRA_LORDS = [NAKSHATRA_LORD_CYCLE[i % 9] for i in range(27)]

# --- Vimshottari Dasha trajanja (u godinama), ukupno 120 godina ---
VIMSHOTTARI_YEARS = {
    "Ketu": 7,
    "Venera": 20,
    "Sunce": 6,
    "Mjesec": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Merkur": 17,
}
VIMSHOTTARI_ORDER = ["Ketu", "Venera", "Sunce", "Mjesec", "Mars", "Rahu", "Jupiter", "Saturn", "Merkur"]
VIMSHOTTARI_TOTAL_YEARS = sum(VIMSHOTTARI_YEARS.values())  # 120

# --- Swiss Ephemeris planet kodovi (iz pyswisseph) ---
# Rahu = srednji čvor (mean node), Ketu = Rahu + 180°
SWE_PLANET_CODES = {
    "Sunce": 0,      # SE_SUN
    "Mjesec": 1,     # SE_MOON
    "Merkur": 2,     # SE_MERCURY
    "Venera": 3,     # SE_VENUS
    "Mars": 4,       # SE_MARS
    "Jupiter": 5,    # SE_JUPITER
    "Saturn": 6,     # SE_SATURN
    "Rahu": 10,      # SE_MEAN_NODE
}

# Jedna nakshatra = 360/27 = 13°20' = 13.3333...°
NAKSHATRA_ARC = 360.0 / 27.0
# Jedna pada = 1/4 nakshatre = 3°20'
PADA_ARC = NAKSHATRA_ARC / 4.0
