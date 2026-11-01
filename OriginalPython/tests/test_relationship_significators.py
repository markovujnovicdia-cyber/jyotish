from core.natal import get_natal_context
from core.synastry.config import SynastryConfig
from core.synastry.conjunctions import find_conjunctions
from core.synastry.graha_drishti import build_graha_drishti_contacts
from core.synastry.interpretation import enrich_conjunction_contacts, enrich_graha_drishti_contacts
from core.synastry.relationship_significators import (
    build_significator_profile, build_synastry_points, compute_relationship_significators,
    CROSS_SIGNIFICATOR_PAIRS,
)
from tests.conftest import make_natal_context


def test_normal_profile_has_valid_seventh_house_and_karakas(person_a):
    ctx = get_natal_context(person_a)
    config = SynastryConfig()
    profile = build_significator_profile(ctx, "A", config)

    assert profile.seventh_house_sign in [
        "Ovan", "Bik", "Blizanci", "Rak", "Lav", "Djevica", "Vaga", "Škorpion",
        "Strijelac", "Jarac", "Vodenjak", "Ribe",
    ]
    assert 1 <= profile.seventh_lord_house <= 12
    assert profile.atmakaraka_planet != "Ketu"
    assert profile.darakaraka_planet != "Ketu"


def test_edge_case_upapada_second_and_eighth_are_two_signs_apart(person_a):
    ctx = get_natal_context(person_a)
    config = SynastryConfig()
    profile = build_significator_profile(ctx, "A", config)
    from core.constants import RASHI
    ul_idx = RASHI.index(profile.upapada_lagna_sign)
    second_idx = RASHI.index(profile.second_from_upapada_sign)
    eighth_idx = RASHI.index(profile.eighth_from_upapada_sign)
    assert second_idx == (ul_idx + 1) % 12
    assert eighth_idx == (ul_idx + 7) % 12


def test_full_significator_comparison_runs_without_errors(person_a, person_b):
    ctx_a = get_natal_context(person_a)
    ctx_b = get_natal_context(person_b)
    config = SynastryConfig()

    drishti_a_to_b = build_graha_drishti_contacts(ctx_a, ctx_b, "A", "B", config)
    drishti_b_to_a = build_graha_drishti_contacts(ctx_b, ctx_a, "B", "A", config)
    all_drishti = enrich_graha_drishti_contacts(drishti_a_to_b + drishti_b_to_a)

    points_a = {name: pos.longitude for name, pos in ctx_a.positions.items()}
    points_b = {name: pos.longitude for name, pos in ctx_b.positions.items()}
    conjunctions = enrich_conjunction_contacts(find_conjunctions(points_a, points_b, config))

    result = compute_relationship_significators(ctx_a, ctx_b, config, all_drishti, conjunctions)

    assert result.profile_a.person_label == "A"
    assert result.profile_b.person_label == "B"
    assert isinstance(result.cross_notes, list)


def test_normal_a_b_identity_never_crossed_for_any_significator_pair(person_a, person_b):
    """
    Generički test tražen u zahtjevu: svaki unakrsni par
    (core.synastry.relationship_significators.CROSS_SIGNIFICATOR_PAIRS)
    mora imati point_a.person_id == 'A' i point_b.person_id == 'B' - nikad
    obrnuto ili dvije točke iste osobe.
    """
    ctx_a = get_natal_context(person_a)
    ctx_b = get_natal_context(person_b)
    config = SynastryConfig()
    profile_a = build_significator_profile(ctx_a, "A", config)
    profile_b = build_significator_profile(ctx_b, "B", config)
    points_a = build_synastry_points(ctx_a, "A", profile_a)
    points_b = build_synastry_points(ctx_b, "B", profile_b)

    for role_a, role_b, _label in CROSS_SIGNIFICATOR_PAIRS:
        point_a, point_b = points_a[role_a], points_b[role_b]
        assert point_a.person_id == "A"
        assert point_b.person_id == "B"
        assert point_a.person_id != point_b.person_id


def test_regression_darakaraka_atmakaraka_pairing_is_not_swapped():
    """
    Regresijski test za TOČAN primjer iz prijave: Darakaraka osobe A je
    Saturn, Atmakaraka osobe B je Merkur. Karte su namjerno građene tako da
    "Merkur (A) aspektira Saturn (B)" GEOMETRIJSKI postoji (bivša greška bi
    tu unakrsnu vezu POGREŠNO prijavila kao potvrdu DK(A)-AK(B) veze), ALI
    "Saturn (A) aspektira Merkur (B)" (ISPRAVAN par) NE postoji (isti znak,
    razmak = konjunkcija, ne aspekt) - ispravljen kod NE smije prijaviti
    Graha Drishti napomenu za DK(A)-AK(B) na temelju pogrešnog para.
    """
    # Osoba A: Saturn ima NAJNIŽI stupanj unutar znaka -> Darakaraka.
    ctx_a = make_natal_context(ascendant_longitude=0.0, planet_longitudes={
        "Sunce": 25.0, "Mjesec": 20.0, "Mars": 15.0, "Merkur": 190.0,
        "Jupiter": 8.0, "Venera": 6.0, "Saturn": 2.0,
    })
    # Osoba B: Merkur ima NAJVIŠI stupanj unutar znaka -> Atmakaraka.
    ctx_b = make_natal_context(ascendant_longitude=0.0, planet_longitudes={
        "Sunce": 5.0, "Mjesec": 8.0, "Mars": 10.0, "Merkur": 28.0,
        "Jupiter": 12.0, "Venera": 15.0, "Saturn": 18.0,
    })
    config = SynastryConfig()

    profile_a = build_significator_profile(ctx_a, "A", config)
    profile_b = build_significator_profile(ctx_b, "B", config)
    assert profile_a.darakaraka_planet == "Saturn"
    assert profile_b.atmakaraka_planet == "Merkur"

    drishti_a_to_b = build_graha_drishti_contacts(ctx_a, ctx_b, "A", "B", config)
    drishti_b_to_a = build_graha_drishti_contacts(ctx_b, ctx_a, "B", "A", config)
    all_drishti = enrich_graha_drishti_contacts(drishti_a_to_b + drishti_b_to_a)

    # Provjeri konstrukciju: Merkur(A)->Saturn(B) MORA postojati (pogrešan par),
    # Saturn(A)->Merkur(B) NE SMIJE postojati (ispravan par, ali bez aspekta u ovoj karti).
    assert any(c.source_person == "A" and c.from_planet == "Merkur" and c.to_planet == "Saturn" for c in all_drishti)
    assert not any(c.source_person == "A" and c.from_planet == "Saturn" and c.to_planet == "Merkur" for c in all_drishti)

    conjunctions = []
    result = compute_relationship_significators(ctx_a, ctx_b, config, all_drishti, conjunctions)

    for note in result.cross_notes:
        if "Atmakaraka (A) - Darakaraka (B)" in note or "Darakaraka (A) - Atmakaraka (B)" in note:
            assert "Graha Drishti" not in note, (
                f"Pogrešno prijavljena DK/AK Graha Drishti veza na temelju zamijenjenog para: {note!r}"
            )
