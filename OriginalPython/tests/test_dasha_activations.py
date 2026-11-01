from datetime import datetime, timezone

from core.synastry.dasha_activations import build_dasha_profile, find_dasha_mutual_activations
from tests.conftest import make_natal_context


def test_normal_profile_has_valid_fields():
    ctx = make_natal_context(ascendant_longitude=0.0, planet_longitudes={"Mjesec": 100.0})
    birth_dt = datetime(2000, 1, 1, tzinfo=timezone.utc)
    at_dt = datetime(2010, 1, 1, tzinfo=timezone.utc)
    profile = build_dasha_profile(ctx, "A", birth_dt, at_dt, seventh_lord="Mars", darakaraka="Venera")
    assert profile.person_label == "A"
    assert profile.maha_lord in [
        "Ketu", "Venera", "Sunce", "Mjesec", "Mars", "Rahu", "Jupiter", "Saturn", "Merkur",
    ]
    assert isinstance(profile.maha_houses_ruled, list)


def test_edge_case_relation_to_seventh_direct_when_maha_lord_is_seventh_lord():
    ctx = make_natal_context(ascendant_longitude=0.0, planet_longitudes={"Mjesec": 100.0})
    birth_dt = datetime(2000, 1, 1, tzinfo=timezone.utc)
    at_dt = datetime(2010, 1, 1, tzinfo=timezone.utc)
    profile = build_dasha_profile(ctx, "A", birth_dt, at_dt, seventh_lord=None, darakaraka="Venera")
    # koristimo STVARNI maha_lord kao "seventh_lord" da testiramo izravnu (direct) granu
    profile_direct = build_dasha_profile(ctx, "A", birth_dt, at_dt, seventh_lord=profile.maha_lord, darakaraka="Venera")
    assert "izravna" in profile_direct.relation_to_seventh


def test_mutual_activation_same_maha_lord_detected():
    ctx_a = make_natal_context(ascendant_longitude=0.0, planet_longitudes={"Mjesec": 100.0})
    ctx_b = make_natal_context(ascendant_longitude=90.0, planet_longitudes={"Mjesec": 100.0})  # ista nakshatra Mjeseca -> isti maha_lord
    birth_dt = datetime(2000, 1, 1, tzinfo=timezone.utc)
    at_dt = datetime(2010, 1, 1, tzinfo=timezone.utc)

    profile_a = build_dasha_profile(ctx_a, "A", birth_dt, at_dt, seventh_lord="Mars", darakaraka="Venera")
    profile_b = build_dasha_profile(ctx_b, "B", birth_dt, at_dt, seventh_lord="Mars", darakaraka="Venera")
    assert profile_a.maha_lord == profile_b.maha_lord  # oba Mjeseca u istoj nakšatri -> isti ciklus/vladar

    notes = find_dasha_mutual_activations(
        profile_a, profile_b,
        asc_lord_a="Mars", seventh_lord_a="Saturn", darakaraka_a="Jupiter",
        asc_lord_b="Sunce", seventh_lord_b="Merkur", darakaraka_b="Venera",
    )
    assert any("ISTOG planeta" in n for n in notes)


def test_cross_role_activation_detected():
    ctx_a = make_natal_context(ascendant_longitude=0.0, planet_longitudes={"Mjesec": 100.0})
    ctx_b = make_natal_context(ascendant_longitude=180.0, planet_longitudes={"Mjesec": 200.0})
    birth_dt = datetime(2000, 1, 1, tzinfo=timezone.utc)
    at_dt = datetime(2010, 1, 1, tzinfo=timezone.utc)

    profile_a = build_dasha_profile(ctx_a, "A", birth_dt, at_dt, seventh_lord="Mars", darakaraka="Venera")
    profile_b = build_dasha_profile(ctx_b, "B", birth_dt, at_dt, seventh_lord="Mars", darakaraka="Venera")

    # postavi B-ov 7. vladar da bude BAŠ A-ov trenutni maha_lord -> ocekivana unakrsna aktivacija
    notes = find_dasha_mutual_activations(
        profile_a, profile_b,
        asc_lord_a="Saturn", seventh_lord_a="Saturn", darakaraka_a="Jupiter",
        asc_lord_b="Sunce", seventh_lord_b=profile_a.maha_lord, darakaraka_b="Venera",
    )
    assert any("BAŠ vladar 7. kuće osobe B" in n for n in notes)


def test_negative_case_no_mutual_activation_when_unrelated():
    ctx_a = make_natal_context(ascendant_longitude=0.0, planet_longitudes={"Mjesec": 100.0})
    ctx_b = make_natal_context(ascendant_longitude=180.0, planet_longitudes={"Mjesec": 200.0})
    birth_dt = datetime(2000, 1, 1, tzinfo=timezone.utc)
    at_dt = datetime(2010, 1, 1, tzinfo=timezone.utc)

    profile_a = build_dasha_profile(ctx_a, "A", birth_dt, at_dt, seventh_lord="Mars", darakaraka="Venera")
    profile_b = build_dasha_profile(ctx_b, "B", birth_dt, at_dt, seventh_lord="Mars", darakaraka="Venera")

    if profile_a.maha_lord == profile_b.maha_lord:
        return  # slucajno poklapanje - preskoci (nedeterministicki rub slucaj)

    notes = find_dasha_mutual_activations(
        profile_a, profile_b,
        asc_lord_a="XXX", seventh_lord_a="XXX", darakaraka_a="XXX",
        asc_lord_b="YYY", seventh_lord_b="YYY", darakaraka_b="YYY",
    )
    assert notes == []
