from core.synastry.config import SynastryConfig
from core.synastry.divisional_synastry import (
    compute_varga_house_overlay, compute_varga_same_sign_contacts,
    find_repeated_patterns_vs_d1, compute_navamsha_synastry,
)
from core.synastry.models import GrahaDrishtiContact, ConjunctionContact
from core.varga import d9_navamsha_sign_index
from tests.conftest import make_natal_context


def test_normal_varga_overlay_uses_d9_sign_not_d1():
    """
    Planet na 5° (D1 Ovan) ide u D9 preko d9_navamsha_sign_index - mora
    koristiti TU (varga) poziciju za kuću, ne sirovi D1 sign_index.
    """
    ctx_a = make_natal_context(ascendant_longitude=0.0, planet_longitudes={"Venera": 5.0})
    ctx_b = make_natal_context(ascendant_longitude=0.0, planet_longitudes={})
    rows = compute_varga_house_overlay(ctx_a, ctx_b, "A", "B", d9_navamsha_sign_index)
    venera_row = next(r for r in rows if r.planet == "Venera")
    expected_d9_idx = d9_navamsha_sign_index(5.0)
    from core.constants import RASHI
    assert venera_row.varga_sign == RASHI[expected_d9_idx]


def test_same_sign_contact_detected_in_varga():
    # 5.0 i 8.0 su unutar istog D9 dijela (3°20' širok, 0-3.33 je prvi dio)
    points_a = {"Venera": 1.0}
    points_b = {"Mars": 2.0}
    contacts = compute_varga_same_sign_contacts(points_a, points_b, d9_navamsha_sign_index)
    assert len(contacts) == 1
    assert contacts[0].person_a_object == "Venera"
    assert contacts[0].person_b_object == "Mars"


def test_negative_case_no_same_sign_contact_when_different_d9_sign():
    points_a = {"Venera": 1.0}
    points_b = {"Mars": 100.0}
    contacts = compute_varga_same_sign_contacts(points_a, points_b, d9_navamsha_sign_index)
    assert contacts == []


def test_repeated_pattern_detected_when_pair_in_both_d1_and_d9():
    d1_drishti = [GrahaDrishtiContact(
        source_person="A", target_person="B", from_planet="Venera", to_planet="Mars",
        house_distance=7, strength=1.0, strength_label="puni (100%)",
        from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
    )]
    varga_drishti = [GrahaDrishtiContact(
        source_person="A", target_person="B", from_planet="Venera", to_planet="Mars",
        house_distance=7, strength=1.0, strength_label="puni (100%)",
        from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
    )]
    notes = find_repeated_patterns_vs_d1(varga_drishti, [], d1_drishti, [], "Navamsha")
    assert len(notes) == 1
    pair_key, note_text = notes[0]
    assert "Venera" in pair_key and "Mars" in pair_key
    assert "Venera" in note_text and "Mars" in note_text


def test_negative_case_weak_d1_and_weak_d9_below_threshold_not_repeated():
    """
    Regresijski test (spec 9): SLAB D1 kontakt (1/4 aspekt) i SLAB, drukčiji
    D9 kontakt za isti par NE smiju automatski postati "ponovljena tema" -
    kombinirana jačina mora prijeći D1_D9_REPEAT_MIN_SCORE.
    """
    d1_drishti = [GrahaDrishtiContact(
        source_person="A", target_person="B", from_planet="Venera", to_planet="Mars",
        house_distance=10, strength=0.25, strength_label="1/4 (25%)",
        from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
    )]
    varga_drishti = [GrahaDrishtiContact(
        source_person="A", target_person="B", from_planet="Venera", to_planet="Mars",
        house_distance=3, strength=0.25, strength_label="1/4 (25%)",
        from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
    )]
    notes = find_repeated_patterns_vs_d1(varga_drishti, [], d1_drishti, [], "Navamsha")
    assert notes == []


def test_negative_case_no_repeated_pattern_when_pair_only_in_d9():
    varga_drishti = [GrahaDrishtiContact(
        source_person="A", target_person="B", from_planet="Sunce", to_planet="Saturn",
        house_distance=7, strength=1.0, strength_label="puni (100%)",
        from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
    )]
    notes = find_repeated_patterns_vs_d1(varga_drishti, [], [], [], "Navamsha")
    assert notes == []


def test_full_navamsha_synastry_runs_without_errors_on_real_context(person_a, person_b):
    from core.natal import get_natal_context
    from core.chara_karaka import get_atmakaraka, get_darakaraka
    from core.synastry.graha_drishti import build_graha_drishti_contacts
    from core.synastry.conjunctions import find_conjunctions

    ctx_a = get_natal_context(person_a)
    ctx_b = get_natal_context(person_b)
    config = SynastryConfig()

    karaka_positions_a = {p: pos for p, pos in ctx_a.positions.items() if p != "Ketu"}
    karaka_positions_b = {p: pos for p, pos in ctx_b.positions.items() if p != "Ketu"}
    dk_a, ak_a = get_darakaraka(karaka_positions_a).planet, get_atmakaraka(karaka_positions_a).planet
    dk_b, ak_b = get_darakaraka(karaka_positions_b).planet, get_atmakaraka(karaka_positions_b).planet

    d1_drishti = build_graha_drishti_contacts(ctx_a, ctx_b, "A", "B", config) + \
                 build_graha_drishti_contacts(ctx_b, ctx_a, "B", "A", config)
    points_a = {n: p.longitude for n, p in ctx_a.positions.items()}
    points_b = {n: p.longitude for n, p in ctx_b.positions.items()}
    d1_conj = find_conjunctions(points_a, points_b, config)

    result = compute_navamsha_synastry(
        ctx_a, ctx_b, config, "Saturn", "Mjesec", dk_a, dk_b, ak_a, ak_b, d1_drishti, d1_conj,
    )
    assert result.varga_code == "D9"
    assert len(result.overlay_a_to_b) == 9  # PLANET_ORDER length
    assert isinstance(result.repeated_pattern_notes, list)
