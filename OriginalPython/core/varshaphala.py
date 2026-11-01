"""
Varshaphala (godišnja karta / solarni povratak).

Implementirano:
- Solarni povratak: trenutak kada tranzitno Sunce (sidereal) ponovno
  dosegne točnu natalnu dužinu Sunca, u godini koju korisnik odabere.
- Ascendent godišnje karte (na trenutak solarnog povratka).
- Muntha: točka koja se svake godine pomiče jedan znak dalje od natalnog
  ascendenta (klasična formula: natal_asc_sign + broj_navršenih_godina).
- Arudha Lagna, Bhrigu Bindu i Gulika GODIŠNJE karte (iste formule kao za
  natalnu kartu, vidi core/special_points.py, samo primijenjene na
  Varshin ascendent/planete).
- Tajika aspekti (Ithasala/Isarapha/Kamboola) i 5 Sahama (Punya, Vidya,
  Yasha, Vivaha, Putra), vidi core/tajika.py za opseg i ograničenja.
- Mudda Dasha: klasična Tajika formula, 360 dana ove Varshe podijeljeno
  standardnim Vimshottari redoslijedom - početni vladar se određuje iz
  rednog broja NATALNE nakshatre Mjeseca i navršenih godina, NE iz
  natalnog Mahadasha vladara aktivnog u trenutku solarnog povratka (vidi
  core/dasha.py, get_mudda_dasha_sequence/get_mudda_starting_lord).
- Varsheshwara (Gospodar godine) - Pancha Vargiya Bala sa 4 od 5
  klasičnih sastavnica (Kshetra, Uchcha, Drekkana, Navamsa - provjereno
  protiv više izvora s točnim bodovima), plus klasični uvjet Tajika
  aspekta na Varsha Lagnu za kvalifikaciju kandidata - vidi
  core/varsheshwara.py za detalje i preostalo ograničenje (Hadda Bala).

Pojednostavljenje kod dan/noć rođenja Varshe: umjesto punog izračuna
izlaska/zalaska Sunca za trenutak solarnog povratka, dan/noć se određuje
pojednostavljeno preko kuće Sunca (whole sign) od Varshinog ascendenta -
kuće 1-6 = dan, kuće 7-12 = noć. Ovo je uobičajena aproksimacija, ali
nije identično preciznom izračunu horizonta.

NIJE implementirano (TODO za sljedeću verziju):
- Preostalih 11 od 16 klasičnih Sahama (vidi core/tajika.py za detalje i
  razlog - pronađene protuslovne formule u izvorima za nekoliko od njih).
- Preostalih 7 od 16 klasičnih Tajika yoga (Gairikambula, Khallasara,
  Duttota, Tambira, Kuttha, Ikkavala, Induvara) - nejasna/nedovoljno
  potvrđena definicija u dostupnim izvorima (9 od 16 JE implementirano,
  vidi core/karyesha_yogas.py).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import swisseph as swe

from core.ephemeris import SIDEREAL_FLAG, get_ascendant, get_planet_positions
from core.constants import RASHI, SWE_PLANET_CODES
from core.houses import whole_sign_house
from core.time_utils import utc_to_julian_day
from core.sahams import compute_sahams, is_daytime
from core.dasha import get_mudda_dasha_sequence, DashaPeriod
from core.special_points import (
    compute_arudha_lagna_sign_index,
    compute_bhrigu_bindu,
)
from core.tajika import (
    TAJIKA_PLANETS,
    PlanetPairRelation,
    find_ithasala_pairs,
    find_isarapha_pairs,
    find_kamboola_pairs,
    compute_saham_punya,
    compute_saham_vidya,
    compute_saham_yasha,
    compute_saham_vivaha,
    compute_saham_putra,
)
from core.varsheshwara import compute_varsheshwara

SUN_CODE = 0


@dataclass
class VarshaphalaResult:
    return_datetime_utc: datetime
    ascendant_longitude: float
    ascendant_sign: str
    muntha_sign: str
    planet_positions: dict
    arudha_lagna_sign: str
    bhrigu_bindu_longitude: float
    gulika_longitude: Optional[float]
    mandi_longitude: Optional[float]
    mandi_ghatikas: Optional[float]
    is_day_birth: bool
    ithasala_pairs: List[PlanetPairRelation]
    isarapha_pairs: List[PlanetPairRelation]
    kamboola_pairs: List[PlanetPairRelation]
    saham_punya: float
    saham_vidya: float
    saham_yasha: float
    saham_vivaha: float
    saham_putra: float
    mudda_dasha: List[DashaPeriod]
    varsheshwara: Dict


@dataclass
class VarshaphalaPeriodInfo:
    """
    Vremenski raspon i dobne oznake JEDNE Varshaphale (identificirane
    s "year" - godinom u kojoj počinje, ista konvencija kao target_year
    u compute_varshaphala/find_solar_return_jd). Namjerno odvojena
    polja (vidi napomenu u zadatku) - "kalendarska godina početka",
    "navršena dob na početku" i "redni broj godine života" NISU isto
    i ne smiju se miješati u jedan tekst.
    """
    year: int
    start_datetime_utc: datetime
    end_datetime_utc: datetime
    completed_years_at_start: int
    life_year_number: int


def _jd_to_utc_datetime(jd: float) -> datetime:
    y, m, d, h = swe.revjul(jd)
    hour = int(h)
    # Retain seconds and microseconds rather than silently losing precision.
    return datetime(y, m, d, tzinfo=timezone.utc) + timedelta(hours=h)


def _sun_longitude(jd_ut: float) -> float:
    xx, _ = swe.calc_ut(jd_ut, SUN_CODE, SIDEREAL_FLAG)
    return xx[0] % 360.0


def find_solar_return_jd(natal_sun_longitude: float, target_year: int,
                          approx_birth_month: int, approx_birth_day: int) -> float:
    """
    Iterativno (bisekcijom) traži Julijanski dan kada Sunce dosegne
    natal_sun_longitude u godini target_year, blizu rođendana.
    """
    approx_dt = datetime(target_year, approx_birth_month, min(approx_birth_day, 28))
    jd_guess = swe.julday(approx_dt.year, approx_dt.month, approx_dt.day, 12.0)

    # pretraga u prozoru od +/- 3 dana oko procijenjenog datuma
    jd_lo = jd_guess - 3
    jd_hi = jd_guess + 3

    def diff(jd):
        lon = _sun_longitude(jd)
        d = (lon - natal_sun_longitude + 180) % 360 - 180
        return d

    for _ in range(60):
        jd_mid = (jd_lo + jd_hi) / 2.0
        d_mid = diff(jd_mid)
        if abs(d_mid) < 1e-6:
            return jd_mid
        d_lo = diff(jd_lo)
        if (d_lo < 0) == (d_mid < 0):
            jd_lo = jd_mid
        else:
            jd_hi = jd_mid

    return (jd_lo + jd_hi) / 2.0


def find_active_varshaphala_year(natal_sun_longitude: float, birth_year: int,
                                  birth_month: int, birth_day: int,
                                  reference_dt_utc: datetime) -> int:
    """
    Određuje koja je Varshaphala AKTIVNA na dati referentni trenutak, prema
    POSLJEDNJEM solarnom povratku (ne prema usporedbi broja kalendarske
    godine referentnog datuma s godinom rođenja ili bilo čim drugim).

    Postupak: izračuna se solarni povratak koji bi (prema rođendanu)
    trebao pasti u kalendarsku godinu referentnog datuma. Ako je taj
    trenutak već prošao (<= referentni trenutak), ta je godina aktivna.
    Ako još nije nastupio, aktivna je prethodna godina (Varshaphala
    započeta prošlogodišnjim povratkom, još traje).

    Usporedba se radi u Julijanskim danima (ne kroz zaokruženi datetime)
    da bi trenutak "točno na granici" bio jednoznačan i precizan.
    """
    if reference_dt_utc.tzinfo is None:
        reference_dt_utc = reference_dt_utc.replace(tzinfo=timezone.utc)
    else:
        reference_dt_utc = reference_dt_utc.astimezone(timezone.utc)

    reference_jd = utc_to_julian_day(reference_dt_utc)
    ref_year = reference_dt_utc.year

    jd_this_year = find_solar_return_jd(natal_sun_longitude, ref_year, birth_month, birth_day)
    active_year = ref_year if jd_this_year <= reference_jd else ref_year - 1

    # ne može postojati Varshaphala prije godine rođenja
    return max(active_year, birth_year)


def get_varshaphala_period_info(natal_sun_longitude: float, birth_year: int,
                                 birth_month: int, birth_day: int, target_year: int) -> VarshaphalaPeriodInfo:
    """
    Vraća početak/kraj (solarni povratci) i dobne oznake za Varshaphalu
    koja počinje u target_year (bilo koja godina - aktivna, prošla ili
    buduća - ovo ne odlučuje koja je aktivna, vidi find_active_varshaphala_year).
    """
    jd_start = find_solar_return_jd(natal_sun_longitude, target_year, birth_month, birth_day)
    jd_end = find_solar_return_jd(natal_sun_longitude, target_year + 1, birth_month, birth_day)
    completed_years = target_year - birth_year
    return VarshaphalaPeriodInfo(
        year=target_year,
        start_datetime_utc=_jd_to_utc_datetime(jd_start),
        end_datetime_utc=_jd_to_utc_datetime(jd_end),
        completed_years_at_start=completed_years,
        life_year_number=completed_years + 1,
    )


def compute_varshaphala(natal_sun_longitude: float, natal_ascendant_longitude: float,
                         birth_year: int, birth_month: int, birth_day: int, target_year: int,
                         lat: float, lon: float,
                         natal_moon_longitude: float, birth_dt_utc: datetime) -> VarshaphalaResult:
    # NAPOMENA: birth_dt_utc se više NE koristi za Mudda Dashu (klasična
    # formula ispod koristi navršene godine + natalnu nakshatru, ne datum
    # rođenja izravno) - parametar je ostavljen radi stabilnosti potpisa
    # funkcije (drugi pozivatelji je već prosljeđuju).
    jd_return = find_solar_return_jd(natal_sun_longitude, target_year, birth_month, birth_day)

    asc_longitude = get_ascendant(jd_return, lat, lon)
    asc_sign_index = int(asc_longitude // 30)

    planet_positions = get_planet_positions(jd_return)

    completed_years = target_year - birth_year
    muntha = muntha_sign_for_age(natal_ascendant_longitude, completed_years)

    # Julijanski dan -> UTC datetime uz očuvane sekunde/mikrosekunde
    return_dt = _jd_to_utc_datetime(jd_return)

    # --- Arudha Lagna, Bhrigu Bindu (Varshine) ---
    planet_sign_index = {name: pos.sign_index for name, pos in planet_positions.items()}
    al_sign_index = compute_arudha_lagna_sign_index(asc_sign_index, planet_sign_index)
    bp_longitude = compute_bhrigu_bindu(
        planet_positions["Mjesec"].longitude, planet_positions["Rahu"].longitude
    )

    # Dan/noć se računa prema stvarnoj visini Sunca u trenutku povratka.
    is_day_birth = is_daytime(jd_return, lat, lon)

    # --- Gulika i Mandi (najsloženiji dio, može zakazati na ekstremnim lokacijama) ---
    gulika_longitude = None
    mandi_longitude = None
    mandi_ghatikas = None
    try:
        local_date_str = return_dt.strftime("%Y-%m-%d")
        gulika_result = compute_gulika_for_moment(jd_return, local_date_str, lat, lon)
        gulika_longitude = gulika_result.longitude
        mandi_longitude = gulika_result.mandi_longitude
        mandi_ghatikas = gulika_result.mandi_ghatikas
    except Exception:
        gulika_longitude = None

    # --- Tajika aspekti ---
    tajika_positions = {
        name: (planet_positions[name].longitude, planet_positions[name].is_retrograde,
               swe.calc_ut(jd_return, SWE_PLANET_CODES[name], SIDEREAL_FLAG)[0][3])
        for name in TAJIKA_PLANETS
    }
    ithasala_pairs = find_ithasala_pairs(tajika_positions)
    isarapha_pairs = find_isarapha_pairs(tajika_positions)
    kamboola_pairs = find_kamboola_pairs(ithasala_pairs)

    # --- Sahami ---
    sun_lon = planet_positions["Sunce"].longitude
    moon_lon = planet_positions["Mjesec"].longitude
    jupiter_lon = planet_positions["Jupiter"].longitude
    venus_lon = planet_positions["Venera"].longitude
    saturn_lon = planet_positions["Saturn"].longitude

    sahams = compute_sahams(asc_longitude, planet_positions, is_day_birth)
    saham_punya = sahams["Punya"]
    saham_vidya = sahams["Vidya"]
    saham_yasha = sahams["Yasha"]
    saham_vivaha = sahams["Vivaha"]
    saham_putra = sahams["Putra"]

    # --- Mudda Dasha (klasična Tajika formula - vidi core/dasha.py) ---
    next_return_jd = find_solar_return_jd(natal_sun_longitude, target_year + 1, birth_month, birth_day)
    mudda_dasha = get_mudda_dasha_sequence(
        natal_moon_longitude, completed_years, return_dt,
        end_datetime_utc=_jd_to_utc_datetime(next_return_jd))

    # --- Varsheshwara (Pancha Vargiya Bala + Tajika kvalifikacija) ---
    natal_asc_sign_index = int((natal_ascendant_longitude % 360.0) // 30)
    muntha_sign_index = RASHI.index(muntha)
    varsheshwara = compute_varsheshwara(
        natal_asc_sign_index, muntha_sign_index, asc_sign_index, asc_longitude,
        is_day_birth, planet_positions,
    )

    return VarshaphalaResult(
        return_datetime_utc=return_dt,
        ascendant_longitude=asc_longitude,
        ascendant_sign=RASHI[asc_sign_index],
        muntha_sign=muntha,
        planet_positions=planet_positions,
        arudha_lagna_sign=RASHI[al_sign_index],
        bhrigu_bindu_longitude=bp_longitude,
        gulika_longitude=gulika_longitude,
        mandi_longitude=mandi_longitude,
        mandi_ghatikas=mandi_ghatikas,
        is_day_birth=is_day_birth,
        ithasala_pairs=ithasala_pairs,
        isarapha_pairs=isarapha_pairs,
        kamboola_pairs=kamboola_pairs,
        saham_punya=saham_punya,
        saham_vidya=saham_vidya,
        saham_yasha=saham_yasha,
        saham_vivaha=saham_vivaha,
        saham_putra=saham_putra,
        mudda_dasha=mudda_dasha,
        varsheshwara=varsheshwara,
    )


def compute_gulika_for_moment(jd_return: float, local_date_str: str, lat: float, lon: float):
    """
    Gulika (i Mandi) za trenutak Varsha Pravesha (solarnog povratka).
    local_date_str se ovdje uzima iz UTC datuma trenutka povratka -
    pojednostavljenje (vidi napomenu na vrhu ovog modula).
    Vraća core.special_points.GulikaResult (ima i .mandi_longitude polje).
    """
    from core.special_points import compute_gulika_from_birth_data
    return compute_gulika_from_birth_data(jd_return, local_date_str, lat, lon)


def muntha_sign_for_age(natal_ascendant_longitude: float, completed_years: int) -> str:
    """
    Muntha se pomiče jedan znak po navršenoj godini od natalnog ascendenta.
    completed_years = target_year - birth_year (koliko je punih godina
    korisnik navršio u toj Varshaphali).
    """
    natal_asc_sign_index = int((natal_ascendant_longitude % 360.0) // 30)
    muntha_index = (natal_asc_sign_index + completed_years) % 12
    return RASHI[muntha_index]
