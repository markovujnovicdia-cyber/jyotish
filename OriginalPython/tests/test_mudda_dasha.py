from datetime import datetime, timedelta, timezone

from core.dasha import (
    get_mudda_starting_lord, get_mudda_dasha_sequence,
    MUDDA_DASHA_TOTAL_DAYS, MUDDA_LORD_ORDER,
)
from core.constants import VIMSHOTTARI_YEARS
from core.nakshatra import get_nakshatra


def _moon_longitude_for(nakshatra_index: int, fraction_elapsed: float) -> float:
    """Vraća apsolutnu dužinu koja pada u zadanu nakshatru (0-26) na
    zadanom udjelu (0.0-1.0) unutar nje."""
    arc = 360.0 / 27.0
    return nakshatra_index * arc + fraction_elapsed * arc


def test_normal_starting_lord_formula_matches_spec():
    """
    Ashwini (janma_nakshatra_number=1), navršene godine=29:
    value = 29 + 1 - 2 = 28, remainder = 28 % 9 = 1 -> Sunce.
    """
    moon_lon = _moon_longitude_for(nakshatra_index=0, fraction_elapsed=0.25)
    lord = get_mudda_starting_lord(moon_lon, completed_years=29)
    assert lord == "Sunce"


def test_edge_case_remainder_zero_maps_to_venus():
    """completed_years=1, Ashwini(1): value=1+1-2=0, remainder=0 -> Venera."""
    moon_lon = _moon_longitude_for(nakshatra_index=0, fraction_elapsed=0.5)
    lord = get_mudda_starting_lord(moon_lon, completed_years=1)
    assert lord == "Venera"


def test_edge_case_remainder_eight_maps_to_ketu():
    """completed_years=9, Ashwini(1): value=9+1-2=8, remainder=8 -> Ketu."""
    moon_lon = _moon_longitude_for(nakshatra_index=0, fraction_elapsed=0.5)
    lord = get_mudda_starting_lord(moon_lon, completed_years=9)
    assert lord == "Ketu"


def test_normal_all_nine_remainders_match_spec_table():
    """Puna tablica iz specifikacije, provjerena za sve ostatke 0-8."""
    expected = {
        1: "Sunce", 2: "Mjesec", 3: "Mars", 4: "Rahu", 5: "Jupiter",
        6: "Saturn", 7: "Merkur", 8: "Ketu", 0: "Venera",
    }
    moon_lon = _moon_longitude_for(nakshatra_index=0, fraction_elapsed=0.5)  # janma_nakshatra_number=1
    for completed_years in range(2, 11):  # value = completed_years - 1, pokriva remainder 0-8 uzastopno
        value = completed_years + 1 - 2
        remainder = value % 9
        lord = get_mudda_starting_lord(moon_lon, completed_years)
        assert lord == expected[remainder], f"years={completed_years} remainder={remainder}"


def test_normal_mudda_lord_order_is_vimshottari_rotated_from_sun():
    assert MUDDA_LORD_ORDER == ["Sunce", "Mjesec", "Mars", "Rahu", "Jupiter", "Saturn", "Merkur", "Ketu", "Venera"]


def test_normal_sequence_total_duration_is_exactly_360_days():
    moon_lon = _moon_longitude_for(nakshatra_index=5, fraction_elapsed=0.6)
    start = datetime(2026, 6, 15, tzinfo=timezone.utc)
    periods = get_mudda_dasha_sequence(moon_lon, completed_years=34, solar_return_dt_utc=start)
    total = sum((p.end - p.start).total_seconds() for p in periods) / 86400.0
    assert abs(total - MUDDA_DASHA_TOTAL_DAYS) < 1e-6
    assert periods[0].start == start


def test_normal_full_lord_durations_are_vimshottari_years_times_three():
    """Puni (ne-balance) periodi moraju trajati TOČNO vimshottari_godine * 3 dana,
    NE skalirano na 365.2425 (klasičan način rada)."""
    moon_lon = _moon_longitude_for(nakshatra_index=0, fraction_elapsed=0.0)  # bez balance (fraction_elapsed=0)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    periods = get_mudda_dasha_sequence(moon_lon, completed_years=29, solar_return_dt_utc=start)
    # Prvi period (bez balance jer je fraction_elapsed=0) i svi puni periodi do zadnjeg (koji se skraćuje da zbroj bude 360)
    for p in periods[:-1]:
        expected_days = VIMSHOTTARI_YEARS[p.lord] * 3.0
        actual_days = (p.end - p.start).total_seconds() / 86400.0
        assert abs(actual_days - expected_days) < 1e-6, f"{p.lord}: {actual_days} != {expected_days}"


def test_edge_case_balance_uses_natal_nakshatra_fraction_not_mahadasha_fraction():
    """
    Balance prvog perioda = puno_trajanje * (1 - fraction_elapsed_nakshatre).
    Mjesec na 25% kroz Ashwini (janma_nakshatra_number=1) -> remaining=0.75.
    """
    moon_lon = _moon_longitude_for(nakshatra_index=0, fraction_elapsed=0.25)
    completed_years = 29  # -> starting lord = Sunce (vidi test iznad)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    periods = get_mudda_dasha_sequence(moon_lon, completed_years, solar_return_dt_utc=start)
    first = periods[0]
    assert first.lord == "Sunce"
    expected_days = VIMSHOTTARI_YEARS["Sunce"] * 3.0 * 0.75  # 18 * 0.75 = 13.5
    actual_days = (first.end - first.start).total_seconds() / 86400.0
    assert abs(actual_days - expected_days) < 1e-6


def test_normal_sequence_follows_rotated_vimshottari_order_from_starting_lord():
    moon_lon = _moon_longitude_for(nakshatra_index=0, fraction_elapsed=0.5)
    completed_years = 4  # value=4+1-2=3, remainder=3 -> Mars
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    periods = get_mudda_dasha_sequence(moon_lon, completed_years, solar_return_dt_utc=start)
    lords_in_order = [p.lord for p in periods]
    assert lords_in_order[0] == "Mars"
    # rotirani Vimshottari red od Marsa: Mars, Rahu, Jupiter, Saturn, Merkur, Ketu, Venera, Sunce, Mjesec, (Mars ponovno...)
    expected_start = ["Mars", "Rahu", "Jupiter", "Saturn", "Merkur", "Ketu", "Venera", "Sunce", "Mjesec"]
    assert lords_in_order[:len(expected_start)] == expected_start
