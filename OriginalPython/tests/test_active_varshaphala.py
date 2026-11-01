"""
Testovi za određivanje AKTIVNE Varshaphale (core.varshaphala.
find_active_varshaphala_year / get_varshaphala_period_info) i za logiku
auto-selektiranja godine u UI-ju (ui.varsha_navigation.resolve_varsha_target_year).

Aktivna Varshaphala se određuje isključivo prema posljednjem solarnom
povratku (usporedba Julijanskih dana), NIKAD prema usporedbi broja
kalendarske godine - vidi core/varshaphala.py:find_active_varshaphala_year
za obrazloženje.
"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import swisseph as swe

from core.ephemeris import SIDEREAL_FLAG
from core.time_utils import utc_to_julian_day
from core.varshaphala import (
    find_active_varshaphala_year,
    find_solar_return_jd,
    get_varshaphala_period_info,
)
from ui.varsha_navigation import resolve_varsha_target_year


def _natal_sun_longitude(year: int, month: int, day: int, hour: float = 12.0) -> float:
    """Sidereal dužina Sunca za dani datum (podne UTC) - dovoljno za ove testove,
    ne treba pravo rođenje ni vremensku zonu osobe."""
    jd = swe.julday(year, month, day, hour)
    xx, _ = swe.calc_ut(jd, 0, SIDEREAL_FLAG)
    return xx[0] % 360.0


def _jd_to_datetime_whole_second(jd: float) -> datetime:
    """Pretvara JD u UTC datetime zaokružen na cijelu sekundu (utc_to_julian_day
    svejedno ne razlikuje mikrosekunde, pa je ovo najveća smislena preciznost
    za konstruiranje referentnih datuma u testovima granice)."""
    y, m, d, h = swe.revjul(jd)
    total_seconds = round(h * 3600)
    hour = int(total_seconds // 3600)
    minute = int((total_seconds % 3600) // 60)
    second = int(total_seconds % 60)
    return datetime(y, m, d, hour, minute, second, tzinfo=timezone.utc)


# --- Slučaj A: rođendan još nije prošao ---

def test_case_a_birthday_not_yet_passed_uses_previous_year():
    natal_sun_lon = _natal_sun_longitude(1985, 11, 4)
    reference = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
    active_year = find_active_varshaphala_year(natal_sun_lon, 1985, 11, 4, reference)
    assert active_year == 2025


# --- Slučaj B: rođendan je prošao ---

def test_case_b_birthday_already_passed_uses_current_year():
    natal_sun_lon = _natal_sun_longitude(1985, 3, 15)
    reference = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
    active_year = find_active_varshaphala_year(natal_sun_lon, 1985, 3, 15, reference)
    assert active_year == 2026


# --- Slučaj C: datum neposredno prije solarnog povratka ---

def test_case_c_day_immediately_before_return_uses_previous_varshaphala():
    natal_sun_lon = _natal_sun_longitude(1985, 3, 15)
    jd_return_2026 = find_solar_return_jd(natal_sun_lon, 2026, 3, 15)
    return_dt = _jd_to_datetime_whole_second(jd_return_2026)

    reference = return_dt - timedelta(days=1)
    active_year = find_active_varshaphala_year(natal_sun_lon, 1985, 3, 15, reference)
    assert active_year == 2025


# --- Slučaj D: datum neposredno nakon solarnog povratka ---

def test_case_d_day_immediately_after_return_uses_new_varshaphala():
    natal_sun_lon = _natal_sun_longitude(1985, 3, 15)
    jd_return_2026 = find_solar_return_jd(natal_sun_lon, 2026, 3, 15)
    return_dt = _jd_to_datetime_whole_second(jd_return_2026)

    reference = return_dt + timedelta(days=1)
    active_year = find_active_varshaphala_year(natal_sun_lon, 1985, 3, 15, reference)
    assert active_year == 2026


# --- Slučaj E: trenutak na granici povratka (sekundna preciznost) ---

def test_case_e_seconds_before_and_after_the_exact_return_moment():
    natal_sun_lon = _natal_sun_longitude(1985, 3, 15)
    jd_return_2026 = find_solar_return_jd(natal_sun_lon, 2026, 3, 15)
    return_dt = _jd_to_datetime_whole_second(jd_return_2026)

    just_before = return_dt - timedelta(seconds=5)
    just_after = return_dt + timedelta(seconds=5)

    assert find_active_varshaphala_year(natal_sun_lon, 1985, 3, 15, just_before) == 2025
    assert find_active_varshaphala_year(natal_sun_lon, 1985, 3, 15, just_after) == 2026


# --- Slučaj F: prijestupna godina (rođenje 29. veljače) ---

def test_case_f_leap_year_birthday_uses_real_sun_position_not_artificial_date():
    natal_sun_lon = _natal_sun_longitude(1988, 2, 29)

    # find_solar_return_jd mora raditi i za nekorektnu (ne-prijestupnu) ciljanu
    # godinu, bez pomicanja datuma na 28.2. ili 1.3. - samo unutarnja procjena
    # početne točke bisekcije koristi min(day, 28), stvarni rezultat prati
    # pravu poziciju Sunca.
    jd_return_2026 = find_solar_return_jd(natal_sun_lon, 2026, 2, 29)
    y, m, d, _h = swe.revjul(jd_return_2026)
    assert (y, m) in [(2026, 2), (2026, 3)]
    if m == 2:
        assert d in (27, 28)
    else:
        assert d == 1

    # referentni datum dobro nakon te stvarne solarne pozicije -> aktivna 2026.
    reference_after = datetime(2026, 7, 26, tzinfo=timezone.utc)
    assert find_active_varshaphala_year(natal_sun_lon, 1988, 2, 29, reference_after) == 2026

    # referentni datum dobro prije -> još je aktivna 2025.
    reference_before = datetime(2026, 1, 10, tzinfo=timezone.utc)
    assert find_active_varshaphala_year(natal_sun_lon, 1988, 2, 29, reference_before) == 2025


# --- Slučaj G: različite vremenske zone ---

def test_case_g_timezone_does_not_change_result_for_the_same_instant():
    natal_sun_lon = _natal_sun_longitude(1985, 3, 15)
    jd_return_2026 = find_solar_return_jd(natal_sun_lon, 2026, 3, 15)
    return_dt_utc = _jd_to_datetime_whole_second(jd_return_2026)

    # isti apsolutni trenutak, malo prije povratka, izražen u tri različite
    # vremenske zone (uklj. dvije s velikim UTC pomakom oko granice datuma)
    instant_utc = return_dt_utc - timedelta(hours=2)
    instant_sydney = instant_utc.astimezone(ZoneInfo("Australia/Sydney"))
    instant_la = instant_utc.astimezone(ZoneInfo("America/Los_Angeles"))

    results = {
        find_active_varshaphala_year(natal_sun_lon, 1985, 3, 15, instant_utc),
        find_active_varshaphala_year(natal_sun_lon, 1985, 3, 15, instant_sydney),
        find_active_varshaphala_year(natal_sun_lon, 1985, 3, 15, instant_la),
    }
    assert results == {2025}

    instant_utc_after = return_dt_utc + timedelta(hours=2)
    instant_sydney_after = instant_utc_after.astimezone(ZoneInfo("Australia/Sydney"))
    instant_la_after = instant_utc_after.astimezone(ZoneInfo("America/Los_Angeles"))

    results_after = {
        find_active_varshaphala_year(natal_sun_lon, 1985, 3, 15, instant_utc_after),
        find_active_varshaphala_year(natal_sun_lon, 1985, 3, 15, instant_sydney_after),
        find_active_varshaphala_year(natal_sun_lon, 1985, 3, 15, instant_la_after),
    }
    assert results_after == {2026}


# --- get_varshaphala_period_info: odvojena polja (ne miješati godinu, dob, redni broj) ---

def test_period_info_has_clearly_separated_fields():
    natal_sun_lon = _natal_sun_longitude(1985, 3, 15)
    info = get_varshaphala_period_info(natal_sun_lon, 1985, 3, 15, 2025)
    assert info.year == 2025
    assert info.completed_years_at_start == 40
    assert info.life_year_number == 41
    assert info.start_datetime_utc < info.end_datetime_utc
    assert info.end_datetime_utc - info.start_datetime_utc > timedelta(days=350)


# --- Slučaj H: promjena osobe -> auto-select aktivne Varshaphale ---

def test_case_h_person_change_auto_selects_active_year():
    result = resolve_varsha_target_year(
        previous_person_key="Osoba A|1985-03-15|12:00:00",
        current_person_key="Osoba B|1990-06-01|08:00:00",
        previous_target_year=2010,  # ručno odabrana godina za Osobu A
        active_year=2026,           # aktivna godina za Osobu B
        current_button_clicked=False,
    )
    assert result == 2026


# --- Slučaj I: ručno odabrana povijesna godina se NE mijenja sama od sebe ---

def test_case_i_manual_year_selection_is_kept_until_explicit_reset():
    # ista osoba, gumb nije kliknut -> zadržava ručno odabranu (povijesnu) godinu
    result = resolve_varsha_target_year(
        previous_person_key="Osoba A|1985-03-15|12:00:00",
        current_person_key="Osoba A|1985-03-15|12:00:00",
        previous_target_year=2010,
        active_year=2026,
        current_button_clicked=False,
    )
    assert result == 2010


def test_case_i_current_button_resets_to_active_year():
    result = resolve_varsha_target_year(
        previous_person_key="Osoba A|1985-03-15|12:00:00",
        current_person_key="Osoba A|1985-03-15|12:00:00",
        previous_target_year=2010,
        active_year=2026,
        current_button_clicked=True,
    )
    assert result == 2026


def test_case_i_first_ever_open_auto_selects_active_year():
    result = resolve_varsha_target_year(
        previous_person_key=None,
        current_person_key="Osoba A|1985-03-15|12:00:00",
        previous_target_year=None,
        active_year=2026,
        current_button_clicked=False,
    )
    assert result == 2026
