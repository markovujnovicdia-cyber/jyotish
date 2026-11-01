"""Regressions for the verified Tajika calculation corrections."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from core.tajika import (
    analyze_pair, find_ithasala_pairs, find_isarapha_pairs,
    find_kamboola_pairs, compute_saham_vivaha, compute_saham_putra,
)
from core.sahams import compute_sahams
from core.varsheshwara import (
    get_tri_rashi_lord, compute_varsheshwara,
)
from core.dasha import get_mudda_dasha_sequence


def test_mirrored_trine_works_exactly_in_both_orders():
    for first, first_lon, second, second_lon in [
        ("Mjesec", 125, "Mars", 5),
        ("Mars", 5, "Mjesec", 125),
    ]:
        relation = analyze_pair(first, first_lon, False, second, second_lon, False)
        assert relation.aspect == "trigon"
        assert relation.within_orb
        assert relation.orb_diff == pytest.approx(0)
        assert relation.is_exact
        assert not relation.is_applying and not relation.is_separating


@pytest.mark.parametrize('a,lon_a,b,lon_b,aspect', [
    ('Sunce', 10, 'Venera', 310, 'sekstil'),
    ('Sunce', 10, 'Mars', 280, 'kvadrat'),
    ('Sunce', 10, 'Jupiter', 250, 'trigon'),
    ('Sunce', 10, 'Saturn', 190, 'opozicija'),
])
def test_other_mirrored_aspects(a, lon_a, b, lon_b, aspect):
    rel = analyze_pair(a, lon_a, False, b, lon_b, False)
    assert rel.aspect == aspect and rel.within_orb and rel.is_exact


def test_applying_and_separating_use_true_signed_speeds():
    # Moon 0°, Mercury 5°: Moon gains on Mercury, approaching conjunction.
    applying = analyze_pair('Mjesec', 0, False, 'Merkur', 5, False, 13.0, 1.0)
    separating = analyze_pair('Mjesec', 5, False, 'Merkur', 0, False, 13.0, 1.0)
    assert applying.is_applying and not applying.is_separating
    assert separating.is_separating and not separating.is_applying
    reversed_vel = analyze_pair('Mjesec', 0, True, 'Merkur', 5, False, -1.0, 1.0)
    assert reversed_vel.is_separating
    stationary = analyze_pair('Mjesec', 0, False, 'Merkur', 5, False, 0.0, 0.0)
    assert not stationary.is_applying and not stationary.is_separating


def test_find_lists_exclude_exact_aspects():
    exact = {'Mjesec': (125, False, 13), 'Mars': (5, False, 0.5)}
    assert find_ithasala_pairs(exact) == []
    assert find_isarapha_pairs(exact) == []
    assert find_kamboola_pairs([]) == []


def test_trirashi_full_classical_mannittha_table():
    day = ['Sunce','Venera','Saturn','Venera','Jupiter','Mjesec','Merkur','Mars','Saturn','Mars','Jupiter','Mjesec']
    night = ['Jupiter','Mjesec','Merkur','Mars','Sunce','Venera','Saturn','Venera','Saturn','Mars','Jupiter','Mjesec']
    assert [get_tri_rashi_lord(i, True) for i in range(12)] == day
    assert [get_tri_rashi_lord(i, False) for i in range(12)] == night


def test_vivaha_and_putra_fixed_in_day_and_night_and_legacy_consistent():
    values = [10,40,80,110,150,200,260]
    names = ['Sunce','Mjesec','Mars','Merkur','Jupiter','Venera','Saturn']
    pos = {p: SimpleNamespace(longitude=v) for p, v in zip(names, values)}
    day = compute_sahams(20, pos, True)
    night = compute_sahams(20, pos, False)
    assert day['Vivaha'] == night['Vivaha'] == 320
    assert day['Putra'] == night['Putra'] == 160
    assert compute_saham_vivaha(20, 200, 260) == 320
    assert compute_saham_putra(20, 150, 40) == 160


def test_varsheshwara_does_not_invent_unqualified_winner():
    # All planets in Pisces: next to the Aries Asc, no Tajika aspect.
    positions = {planet: SimpleNamespace(longitude=340., sign_index=11, degree_in_sign=10.)
                 for planet in ['Sunce','Mjesec','Mars','Merkur','Jupiter','Venera','Saturn']}
    result = compute_varsheshwara(0, 0, 0, 22., True, positions)
    assert result['winner'] is None
    assert not result['any_qualified']


def test_mudda_covers_true_solar_year_without_gap():
    start = datetime(2026,11,4,12,27,56,tzinfo=timezone.utc)
    end = start + timedelta(days=365, hours=6)
    periods = get_mudda_dasha_sequence(85, 41, start, end_datetime_utc=end)
    assert periods[0].start == start
    assert periods[-1].end == end
    assert all(a.end == b.start for a,b in zip(periods,periods[1:]))
    assert get_mudda_dasha_sequence(85, 41, start)[-1].end == start + timedelta(days=360)
