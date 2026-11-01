from datetime import datetime, timezone

from core.natal import get_natal_context
from core.synastry.transit_activations import build_natal_synastry_links
from core.synastry.varshaphala_activations import build_varshaphala_profile, compute_varshaphala_synastry


def test_normal_profile_has_valid_fields(person_a):
    ctx = get_natal_context(person_a)
    at_dt = datetime(2026, 6, 15, tzinfo=timezone.utc)
    profile, result = build_varshaphala_profile(person_a, ctx, "A", 2026, at_dt, seventh_lord="Mars")
    assert profile.person_label == "A"
    assert profile.target_year == 2026
    assert profile.ascendant_sign in [
        "Ovan", "Bik", "Blizanci", "Rak", "Lav", "Djevica", "Vaga", "Škorpion",
        "Strijelac", "Jarac", "Vodenjak", "Ribe",
    ]
    assert 1 <= profile.venus_house <= 12
    assert profile.active_mudda_dasha_lord in [
        "Ketu", "Venera", "Sunce", "Mjesec", "Mars", "Rahu", "Jupiter", "Saturn", "Merkur",
    ]
    assert profile.tajika_ithasala_count >= 0
    assert profile.tajika_isarapha_count >= 0


def test_edge_case_target_year_before_birth_year_still_works_forward(person_a):
    """compute_varshaphala uzima godinu solarnog povratka - godina rodenja+1 mora raditi bez greske."""
    ctx = get_natal_context(person_a)
    birth_year = int(person_a.birth_date.split("-")[0])
    at_dt = datetime(birth_year + 1, 6, 15, tzinfo=timezone.utc)
    profile, result = build_varshaphala_profile(person_a, ctx, "A", birth_year + 1, at_dt, seventh_lord="Mars")
    assert profile.target_year == birth_year + 1


def test_full_varshaphala_synastry_runs_without_errors(person_a, person_b):
    ctx_a = get_natal_context(person_a)
    ctx_b = get_natal_context(person_b)

    from core.synastry.config import SynastryConfig
    from core.synastry.graha_drishti import build_graha_drishti_contacts
    from core.synastry.conjunctions import find_conjunctions
    from core.synastry.interpretation import enrich_graha_drishti_contacts, enrich_conjunction_contacts
    from core.synastry.nakshatra_matching import compute_nakshatra_synastry
    from core.chara_karaka import get_darakaraka
    from core.constants import RASHI, RASHI_LORD

    config = SynastryConfig()
    seventh_lord_a = RASHI_LORD[RASHI[(ctx_a.ascendant_sign_index + 6) % 12]]
    seventh_lord_b = RASHI_LORD[RASHI[(ctx_b.ascendant_sign_index + 6) % 12]]

    drishti = enrich_graha_drishti_contacts(
        build_graha_drishti_contacts(ctx_a, ctx_b, "A", "B", config) +
        build_graha_drishti_contacts(ctx_b, ctx_a, "B", "A", config)
    )
    points_a = {n: p.longitude for n, p in ctx_a.positions.items()}
    points_b = {n: p.longitude for n, p in ctx_b.positions.items()}
    conjunctions = enrich_conjunction_contacts(find_conjunctions(points_a, points_b, config))
    karaka_a = {p: pos for p, pos in ctx_a.positions.items() if p != "Ketu"}
    karaka_b = {p: pos for p, pos in ctx_b.positions.items() if p != "Ketu"}
    dk_a, dk_b = get_darakaraka(karaka_a).planet, get_darakaraka(karaka_b).planet
    nakshatra_result = compute_nakshatra_synastry(ctx_a, ctx_b, seventh_lord_a, seventh_lord_b, dk_a, dk_b)
    links = build_natal_synastry_links(ctx_a, ctx_b, drishti, conjunctions, nakshatra_result)

    at_dt = datetime(2026, 6, 15, tzinfo=timezone.utc)
    result = compute_varshaphala_synastry(
        person_a, ctx_a, person_b, ctx_b, 2026, 2026, at_dt,
        seventh_lord_a, seventh_lord_b, links,
    )
    assert result.profile_a.person_label == "A"
    assert result.profile_b.person_label == "B"
    assert isinstance(result.b_planets_on_a_sensitive_points, list)
    assert isinstance(result.mudda_dasha_activates_natal_link, list)
    assert len(result.notes) >= 1
    assert "Tajika" in result.notes[0]


def test_negative_case_no_mudda_activation_when_links_empty(person_a, person_b):
    ctx_a = get_natal_context(person_a)
    ctx_b = get_natal_context(person_b)
    at_dt = datetime(2026, 6, 15, tzinfo=timezone.utc)
    result = compute_varshaphala_synastry(
        person_a, ctx_a, person_b, ctx_b, 2026, 2026, at_dt,
        seventh_lord_a="Mars", seventh_lord_b="Mars", natal_links=[],
    )
    assert result.mudda_dasha_activates_natal_link == []
