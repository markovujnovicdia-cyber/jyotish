"""
Vimshottari Dasha - izračun na temelju Mjesečeve nakshatre u trenutku rođenja.

Princip:
1. Odredi se nakshatra Mjeseca i koliki je njen dio već "prošao" u trenutku
   rođenja (fraction_elapsed).
2. Preostali dio prve Mahadashe = (1 - fraction_elapsed) * trajanje_vladara.
3. Nakon toga dashe teku redom po fiksnom ciklusu od 9 vladara, svaka u
   punom trajanju, sve dok se ne pokrije traženo razdoblje (obično 120 god).
4. Antardasha i Pratyantardasha dijele razdoblje svoje Mahadashe/Antardashe
   proporcionalno trajanjima vladara, u istom rotirajućem redoslijedu
   počevši od vladara same Mahadashe/Antardashe.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from core.constants import VIMSHOTTARI_ORDER, VIMSHOTTARI_YEARS, VIMSHOTTARI_TOTAL_YEARS
from core.nakshatra import get_nakshatra

# Odabrana konvencija: srednja solarna/gregorijanska godina, ne sideralna godina
DAYS_PER_YEAR = 365.2425


@dataclass
class DashaPeriod:
    lord: str
    start: datetime
    end: datetime


def _rotate_order_from(lord: str) -> List[str]:
    idx = VIMSHOTTARI_ORDER.index(lord)
    return VIMSHOTTARI_ORDER[idx:] + VIMSHOTTARI_ORDER[:idx]


def get_mahadasha_sequence(moon_longitude: float, birth_dt_utc: datetime,
                            years_to_cover: float = 120.0) -> List[DashaPeriod]:
    """
    Vraća pune Mahadasha periode; prvi počinje prije rođenja ako je dio
    nakshatre već prošao. Lista je dovoljno duga da
    pokrije 'years_to_cover' godina (klasično pun ciklus od 120 godina).
    """
    nak = get_nakshatra(moon_longitude)
    start_lord = nak.lord
    order = _rotate_order_from(start_lord)

    # Podrazdoblja pripadaju PUNOJ mahadaši. Njezin početak može biti
    # prije rođenja; rezanje na rođenje uništilo bi omjere i fazu antardaša.
    first_full_years = VIMSHOTTARI_YEARS[start_lord]
    elapsed = first_full_years * nak.fraction_elapsed
    cursor = birth_dt_utc - timedelta(days=elapsed * DAYS_PER_YEAR)
    horizon = birth_dt_utc + timedelta(days=years_to_cover * DAYS_PER_YEAR)
    periods: List[DashaPeriod] = []
    i = 0
    while cursor < horizon:
        lord = order[i % len(order)]
        end = cursor + timedelta(days=VIMSHOTTARI_YEARS[lord] * DAYS_PER_YEAR)
        periods.append(DashaPeriod(lord=lord, start=cursor, end=end))
        cursor = end
        i += 1

    return periods


def get_sub_periods(parent_lord: str, parent_start: datetime, parent_end: datetime) -> List[DashaPeriod]:
    """
    Dijeli jedan period (Mahadasha ili Antardasha) na pod-periode
    (Antardasha ili Pratyantardasha) proporcionalno trajanjima vladara,
    u rotirajućem redoslijedu koji počinje od vladara samog perioda.
    """
    order = _rotate_order_from(parent_lord)
    total_duration = (parent_end - parent_start).total_seconds()

    sub_periods: List[DashaPeriod] = []
    cursor = parent_start
    for lord in order:
        share = VIMSHOTTARI_YEARS[lord] / VIMSHOTTARI_TOTAL_YEARS
        duration_seconds = total_duration * share
        end = cursor + timedelta(seconds=duration_seconds)
        sub_periods.append(DashaPeriod(lord=lord, start=cursor, end=end))
        cursor = end

    # Zatvori granicu točno: kumulativno zaokruživanje mikrosekundi ne smije
    # ostaviti prazninu između roditelja i zadnjeg podrazdoblja.
    if sub_periods:
        sub_periods[-1].end = parent_end
    return sub_periods


def find_current_period(periods: List[DashaPeriod], at_dt: datetime) -> DashaPeriod:
    """Pronalazi period unutar liste koji sadrži zadani datum."""
    for p in periods:
        if p.start <= at_dt < p.end:
            return p
    raise ValueError("Datum je izvan izračunatog raspona daša.")


def get_current_dasha_snapshot(moon_longitude: float, birth_dt_utc: datetime, at_dt_utc: datetime):
    """
    Vraća (maha, antar, pratyantar) DashaPeriod objekte koji su aktivni
    na zadani datum 'at_dt_utc'.
    """
    years = max(120.0, (at_dt_utc - birth_dt_utc).total_seconds() / (86400 * DAYS_PER_YEAR) + 1.0)
    maha_sequence = get_mahadasha_sequence(moon_longitude, birth_dt_utc, years_to_cover=years)
    current_maha = find_current_period(maha_sequence, at_dt_utc)

    antar_sequence = get_sub_periods(current_maha.lord, current_maha.start, current_maha.end)
    current_antar = find_current_period(antar_sequence, at_dt_utc)

    pratyantar_sequence = get_sub_periods(current_antar.lord, current_antar.start, current_antar.end)
    current_pratyantar = find_current_period(pratyantar_sequence, at_dt_utc)

    return current_maha, current_antar, current_pratyantar


def get_current_dasha_5_levels(moon_longitude: float, birth_dt_utc: datetime, at_dt_utc: datetime):
    """
    Vraća (maha, antar, pratyantar, sookshma, prana) - svih 5 klasičnih
    razina Vimshottari dashe, aktivnih na zadani datum 'at_dt_utc'.
    Svaka sljedeća razina dijeli prethodnu na isti proporcionalan način
    (vidi get_sub_periods).
    """
    maha, antar, pratyantar = get_current_dasha_snapshot(moon_longitude, birth_dt_utc, at_dt_utc)

    sookshma_sequence = get_sub_periods(pratyantar.lord, pratyantar.start, pratyantar.end)
    current_sookshma = find_current_period(sookshma_sequence, at_dt_utc)

    prana_sequence = get_sub_periods(current_sookshma.lord, current_sookshma.start, current_sookshma.end)
    current_prana = find_current_period(prana_sequence, at_dt_utc)

    return maha, antar, pratyantar, current_sookshma, current_prana


# ---------------------------------------------------------------------------
# Mudda Dasha (za Varshaphalu) - klasična Tajika formula
#
# Odabrana konvencija aplikacije: 360 civilnih dana, svaki traje 24 sata.
# Trajanja su Vimshottari godine × 3. To nije isto što i 360 solarnih
# dana definiranih kao Sunčevo kretanje po 1°, opisano u PVR §30.3.
# Zbog toga se kalendarski datumi mogu razlikovati od drugih programa.
#
# Početni vladar - formula (NIJE isto što i "natalni Mahadasha vladar
# aktivan na solarni povratak" - ranija verzija ovog modula je koristila
# TU drugu, također dokumentiranu konvenciju; ovo je namjerno zamijenjeno
# specifičnom formulom po zahtjevu):
#   janma_nakshatra_number = redni broj natalne nakshatre Mjeseca (1-27,
#       Ashwini=1)
#   value = navršene_godine + janma_nakshatra_number - 2
#   remainder = value % 9
#   remainder -> vladar: 1=Sunce, 2=Mjesec, 3=Mars, 4=Rahu, 5=Jupiter,
#       6=Saturn, 7=Merkur, 8=Ketu, 0=Venera (=standardni Vimshottari
#       redoslijed rotiran da počinje od Sunca)
#
# Balance početnog vladara: koristi FRACTION_ELAPSED natalnog Mjeseca
# UNUTAR NJEGOVE NATALNE NAKSHATRE (core.nakshatra.get_nakshatra) - isti
# princip kao natalna Vimshottari (koja isto prenosi proteklo vrijeme u
# nakshatri u prvi period), NE proteklo vrijeme unutar neke Mahadashe.
# ---------------------------------------------------------------------------

MUDDA_DASHA_TOTAL_DAYS = 360.0
MUDDA_DAYS_PER_VIMSHOTTARI_YEAR = 3.0  # 360 / 120 - klasičan omjer, provjeren da zbroj svih 9 = točno 360

# Standardni Vimshottari redoslijed, rotiran da počinje od Sunca (ISTI
# poredak kao VIMSHOTTARI_ORDER, samo počevši od druge točke u ciklusu) -
# indeks u ovom popisu + 1 = "remainder" iz formule gore (remainder=0 -> Venera).
MUDDA_LORD_ORDER = ["Sunce", "Mjesec", "Mars", "Rahu", "Jupiter", "Saturn", "Merkur", "Ketu", "Venera"]


def get_mudda_starting_lord(natal_moon_longitude: float, completed_years: int) -> str:
    """
    Klasična Tajika formula za početnog Mudda Dasha vladara (vidi napomenu
    iznad). completed_years = navršene godine na početku ove Varshaphale
    (target_year - birth_year).
    """
    janma_nakshatra_number = get_nakshatra(natal_moon_longitude).index + 1  # 1-27, Ashwini=1
    value = completed_years + janma_nakshatra_number - 2
    remainder = value % 9  # Python % uvijek vraća 0-8 za pozitivan djelitelj
    return MUDDA_LORD_ORDER[(remainder - 1) % 9]


def get_mudda_dasha_sequence(
    natal_moon_longitude: float, completed_years: int, solar_return_dt_utc: datetime,
    end_datetime_utc: datetime | None = None,
) -> List[DashaPeriod]:
    """
    Vraća listu Mudda Dasha perioda (360 dana u starom API-ju ili
    proporcionalno do stvarnog sljedećeg povratka ako je end_datetime_utc
    zadan), počevši od trenutka Varsha Pravesha. Početni vladar se određuje
    formulom (get_mudda_starting_lord) - NE od natalnog Mjeseca u Varsha
    Pravesha karti, nego od NATALNOG (rođenjskog) Mjeseca. Balance
    početnog perioda dolazi od udjela natalne nakshatre koji je već
    "prošao" u trenutku rođenja (isti fraction_elapsed kao natalna
    Vimshottari), ne od bilo kakvog udjela unutar neke Mahadashe.
    """
    if end_datetime_utc is not None and end_datetime_utc <= solar_return_dt_utc:
        raise ValueError("Sljedeći solarni povratak mora biti nakon početka Varshaphale")
    # Legacy: 360 civil days. For a Varshaphala, scale durations of the
    # 360 traditional parts to the *actual next solar return* to avoid a
    # calendar gap of about five days. This is a declared software convention.
    annual_days = ((end_datetime_utc - solar_return_dt_utc).total_seconds()/86400
                   if end_datetime_utc is not None else MUDDA_DASHA_TOTAL_DAYS)
    scale = annual_days / MUDDA_DASHA_TOTAL_DAYS
    starting_lord = get_mudda_starting_lord(natal_moon_longitude, completed_years)
    remaining_fraction = 1.0 - get_nakshatra(natal_moon_longitude).fraction_elapsed

    order = _rotate_order_from(starting_lord)

    periods: List[DashaPeriod] = []
    cursor = solar_return_dt_utc
    total_days = 0.0
    i = 0
    while total_days < MUDDA_DASHA_TOTAL_DAYS - 1e-6:
        lord = order[i % len(order)]
        full_days = VIMSHOTTARI_YEARS[lord] * MUDDA_DAYS_PER_VIMSHOTTARI_YEAR
        duration_days = full_days * remaining_fraction if i == 0 else full_days
        if total_days + duration_days > MUDDA_DASHA_TOTAL_DAYS:
            duration_days = MUDDA_DASHA_TOTAL_DAYS - total_days  # skrati zadnji period da ukupno bude točno 360
        end = cursor + timedelta(days=duration_days * scale)
        periods.append(DashaPeriod(lord=lord, start=cursor, end=end))
        cursor = end
        total_days += duration_days
        i += 1

    if end_datetime_utc is not None and periods:
        periods[-1].end = end_datetime_utc
    return periods
