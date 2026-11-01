from datetime import datetime, timezone
from types import SimpleNamespace
from core.dasha import (get_mahadasha_sequence, get_sub_periods,
    get_current_dasha_5_levels, DAYS_PER_YEAR)
from core.sahams import saham_arc, compute_sahams, SAHAM_INFO


def test_birth_inside_mahadasha_keeps_original_antardasha_phase():
    birth = datetime(2000, 1, 1, tzinfo=timezone.utc)
    # Halfway through Ashwini: 3.5 years of the full 7-year Ketu MD elapsed.
    md = get_mahadasha_sequence(360 / 27 / 2, birth)[0]
    assert md.lord == 'Ketu' and md.start < birth < md.end
    assert abs((md.end-md.start).total_seconds()/86400/DAYS_PER_YEAR-7) < 1e-9
    antar = get_sub_periods(md.lord, md.start, md.end)
    assert abs((antar[0].end-antar[0].start).total_seconds()/86400/DAYS_PER_YEAR-49/120) < 1e-9
    levels = get_current_dasha_5_levels(360 / 27 / 2, birth, birth)
    assert [p.lord for p in levels[:2]] == ['Ketu', 'Rahu']
    assert all(p.start <= birth < p.end for p in levels)


def test_subperiod_boundaries_exactly_cover_parent():
    birth = datetime(2000, 1, 1, tzinfo=timezone.utc)
    parent = get_mahadasha_sequence(6, birth)[0]
    for _ in range(4):
        children = get_sub_periods(parent.lord, parent.start, parent.end)
        assert children[0].start == parent.start
        assert children[-1].end == parent.end
        assert all(a.end == b.start for a,b in zip(children,children[1:]))
        parent = children[-1]


def test_saham_arc_book_examples_and_wrap():
    # PVR §28.8, example 3: artha and vanik (degrees/minutes).
    assert abs(saham_arc(310+50/60, 19+10/60, 280+50/60)-(212+30/60)) < 1e-9
    assert abs(saham_arc(311+28/60, 345+14/60, 280+50/60)-(247+4/60)) < 1e-9
    assert saham_arc(40, 10, 20) == 50  # C inside B-to-A arc
    assert saham_arc(40, 10, 100) == 160  # C outside: add 30
    assert saham_arc(10, 350, 355) == 15  # crossing zero


def test_saham_day_night_and_fixed_formulas():
    positions = {name:SimpleNamespace(longitude=lon) for name,lon in
      zip(['Sunce','Mjesec','Mars','Merkur','Jupiter','Venera','Saturn'],[10,40,80,110,150,200,260])}
    day = compute_sahams(20, positions, True)
    night = compute_sahams(20, positions, False)
    assert set(day) == set(SAHAM_INFO) and len(day) == 20
    assert day['Punya'] == 50 and night['Punya'] == 20
    assert day['Vidya'] == night['Punya'] and night['Vidya'] == day['Punya']
    for key in ['Vyapara','Artha','Labha','Bhratri','Paradesa']:
        assert day[key] == night[key]
    assert all(0 <= value < 360 for value in list(day.values())+list(night.values()))
