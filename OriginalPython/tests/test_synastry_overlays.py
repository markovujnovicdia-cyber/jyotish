from datetime import datetime, timezone

from core.constants import RASHI, PLANET_ORDER
from core.ephemeris import PlanetPosition
from core.natal import NatalContext
from core.synastry.overlays import compute_house_overlay, find_mutual_emphasis, SIGNIFICANT_HOUSES


def _pos(longitude: float, is_retrograde: bool = False) -> PlanetPosition:
    lon = longitude % 360.0
    sign_index = int(lon // 30)
    return PlanetPosition(
        name="?", longitude=lon, sign_index=sign_index, sign=RASHI[sign_index],
        degree_in_sign=lon - sign_index * 30, is_retrograde=is_retrograde,
    )


def _make_context(ascendant_longitude: float, planet_longitudes: dict, name="Test") -> NatalContext:
    # Neeksplicitno zadani planeti dobiju FIKSNU (istu za sve pozive) dužinu
    # 65° (Blizanci) - namjerno IZVAN SIGNIFICANT_HOUSES kad je ascendent
    # blizu 0°, da testovi koji provjeravaju SAMO jedan konkretan planet ne
    # dobiju slučajne "uzajamne" podudarnosti od neiskorištenih planeta.
    positions = {p: _pos(planet_longitudes.get(p, 65.0)) for p in PLANET_ORDER}
    asc_sign_idx = int(ascendant_longitude % 360.0 // 30)
    return NatalContext(
        person_name=name,
        utc_dt=datetime(2000, 1, 1, tzinfo=timezone.utc),
        jd_ut=2451544.5,
        ascendant_longitude=ascendant_longitude,
        ascendant_sign_index=asc_sign_idx,
        positions=positions,
        special_points={},
    )


def test_normal_overlay_house_relative_to_target_ascendant():
    """
    Ascendent osobe B je 0° (Ovan, 1. kuća = Ovan). Venera osobe A je na
    100° (Rak, znak 3 od Ovna) -> mora pasti u 4. kuću osobe B.
    """
    ctx_a = _make_context(ascendant_longitude=10.0, planet_longitudes={"Venera": 100.0})
    ctx_b = _make_context(ascendant_longitude=0.0, planet_longitudes={})
    rows = compute_house_overlay(ctx_a, ctx_b, "A", "B")
    venera_row = next(r for r in rows if r.planet == "Venera")
    assert venera_row.whole_sign_house == 4
    assert venera_row.sign == "Rak"
    assert venera_row.is_significant_house is True  # 4. kuća je u SIGNIFICANT_HOUSES


def test_edge_case_house_3_and_6_not_marked_significant():
    ctx_a = _make_context(ascendant_longitude=0.0, planet_longitudes={"Mars": 65.0})  # znak 2 (Blizanci) -> 3. kuca
    ctx_b = _make_context(ascendant_longitude=0.0, planet_longitudes={})
    rows = compute_house_overlay(ctx_a, ctx_b, "A", "B")
    mars_row = next(r for r in rows if r.planet == "Mars")
    assert mars_row.whole_sign_house == 3
    assert mars_row.is_significant_house is False
    assert 3 not in SIGNIFICANT_HOUSES
    assert 6 not in SIGNIFICANT_HOUSES


def test_bhava_chalit_house_differs_near_cusp():
    """
    Ascendent B na 5° Ovna (Bhava Chalit 1. kuća pokriva 350°-20°, jer je
    ascendent SREDINA 1. kuće). Planet na 355° (Ribe) je Whole Sign u 12.
    kući (Ribe = 11. znak), ali Bhava Chalit ga smjesta u 1. kuću - razlika
    mora biti zabilježena.
    """
    ctx_a = _make_context(ascendant_longitude=0.0, planet_longitudes={"Saturn": 355.0})
    ctx_b = _make_context(ascendant_longitude=5.0, planet_longitudes={})
    rows = compute_house_overlay(ctx_a, ctx_b, "A", "B")
    saturn_row = next(r for r in rows if r.planet == "Saturn")
    assert saturn_row.whole_sign_house == 12
    assert saturn_row.bhava_chalit_house == 1
    assert saturn_row.bhava_chalit_house != saturn_row.whole_sign_house


def test_negative_case_no_bhava_chalit_note_when_same():
    """Kad se Whole Sign i Bhava Chalit kuća poklapaju, polje mora biti None (ne duplicirati)."""
    ctx_a = _make_context(ascendant_longitude=0.0, planet_longitudes={"Jupiter": 5.0})
    ctx_b = _make_context(ascendant_longitude=0.0, planet_longitudes={})
    rows = compute_house_overlay(ctx_a, ctx_b, "A", "B")
    jup_row = next(r for r in rows if r.planet == "Jupiter")
    assert jup_row.whole_sign_house == 1
    assert jup_row.bhava_chalit_house is None


def test_mutual_emphasis_detects_repeated_planet_both_directions():
    ctx_a = _make_context(ascendant_longitude=0.0, planet_longitudes={"Venera": 190.0})  # 7. kuca od B
    ctx_b = _make_context(ascendant_longitude=0.0, planet_longitudes={"Venera": 190.0})  # 7. kuca od A
    overlay_a_to_b = compute_house_overlay(ctx_a, ctx_b, "A", "B")
    overlay_b_to_a = compute_house_overlay(ctx_b, ctx_a, "B", "A")
    notes = find_mutual_emphasis(overlay_a_to_b, overlay_b_to_a)
    assert any("Venera" in n for n in notes)


def test_mutual_emphasis_empty_when_no_overlap():
    ctx_a = _make_context(ascendant_longitude=0.0, planet_longitudes={"Venera": 65.0})  # 3. kuca (nije significant)
    ctx_b = _make_context(ascendant_longitude=0.0, planet_longitudes={"Mars": 65.0})
    overlay_a_to_b = compute_house_overlay(ctx_a, ctx_b, "A", "B")
    overlay_b_to_a = compute_house_overlay(ctx_b, ctx_a, "B", "A")
    notes = find_mutual_emphasis(overlay_a_to_b, overlay_b_to_a)
    assert notes == []
