from datetime import date, datetime, timezone

from core.synastry.config import SynastryConfig
from core.synastry.predictive import (
    build_transit_rows, compute_double_transit, compute_predictive_snapshot, compute_timeline,
)
from tests.conftest import make_natal_context


def test_normal_double_transit_house_hit():
    ctx = make_natal_context(ascendant_longitude=0.0, planet_longitudes={
        "Venera": 65.0, "Mars": 65.0, "Jupiter": 65.0, "Saturn": 65.0,
    })
    # Jupiter u Ovnu (znak0 = 1. kuca od Asc) - u PREDICTIVE_ACTIVATION_HOUSES
    transit_rows = build_transit_rows(ctx, jd_ut=2451545.0)
    # Napravimo rucno "lazne" transit redove umjesto swisseph poziva za ovaj test bi bilo
    # slozenije - koristimo stvarni build_transit_rows nad sintetickim ctx-om i samo
    # provjeravamo da funkcija radi i vraca ocekivana polja.
    assert "Jupiter" in transit_rows
    assert 1 <= transit_rows["Jupiter"].house_from_ascendant <= 12


def test_double_transit_hits_and_simultaneous_flag():
    # NAPOMENA: tranzitne pozicije Jupitera/Saturna dolaze iz STVARNOG
    # swisseph izračuna za jd_ut, ne iz natalnih "planet_longitudes" ovdje
    # (koje utječu samo na natalne pozicije/kuće, ne na tranzit). Za
    # jd_ut=2451545.0 tranzitni Jupiter/Saturn su oba u znaku 0 (Ovan);
    # ascendent oba na 0 (Ovan) -> Ovan = 1. kuca za oboje (pogodak za oboje).
    ctx_a = make_natal_context(ascendant_longitude=0.0, planet_longitudes={
        "Venera": 65.0, "Mjesec": 65.0, "Mars": 65.0,
    })
    ctx_b = make_natal_context(ascendant_longitude=0.0, planet_longitudes={
        "Venera": 65.0, "Mjesec": 65.0, "Mars": 65.0,
    })
    jd_ut = 2451545.0
    transits_a = build_transit_rows(ctx_a, jd_ut)
    transits_b = build_transit_rows(ctx_b, jd_ut)

    result = compute_double_transit(
        ctx_a, ctx_b, transits_a, transits_b,
        seventh_lord_a="Mars", seventh_lord_b="Mars", darakaraka_a="Venera", darakaraka_b="Venera",
    )
    assert "1. kuća" in result.jupiter_hits_a
    assert "1. kuća" in result.saturn_hits_a
    assert result.simultaneous_both_charts is True


def test_negative_case_no_simultaneous_when_only_one_person_hit():
    # NAPOMENA: tranzitne pozicije Jupitera/Saturna dolaze iz STVARNOG
    # swisseph izračuna za jd_ut (ne iz "planet_longitudes" natalnih
    # vrijednosti postavljenih ovdje - to je samo natalni kontekst).
    # Za jd_ut=2451545.0 tranzitni Jupiter/Saturn su oba u znaku 0 (Ovan).
    # Ascendent A=0 (Ovan) -> 1. kuca (pogodak). Ascendent B=340 (Ribe)
    # -> Ovan je 2. kuca od B (nije u promatranom skupu) -> nema pogotka.
    ctx_a = make_natal_context(ascendant_longitude=0.0, planet_longitudes={
        "Venera": 65.0, "Mjesec": 65.0, "Mars": 65.0,
    })
    ctx_b = make_natal_context(ascendant_longitude=340.0, planet_longitudes={
        "Venera": 100.0, "Mjesec": 105.0, "Mars": 110.0,
    })
    jd_ut = 2451545.0
    transits_a = build_transit_rows(ctx_a, jd_ut)
    transits_b = build_transit_rows(ctx_b, jd_ut)
    result = compute_double_transit(
        ctx_a, ctx_b, transits_a, transits_b,
        seventh_lord_a="Mars", seventh_lord_b="Mars", darakaraka_a="Venera", darakaraka_b="Venera",
    )
    assert result.simultaneous_both_charts is False


def test_full_predictive_snapshot_runs_without_errors(person_a, person_b):
    from core.natal import get_natal_context
    from core.chara_karaka import get_atmakaraka, get_darakaraka
    from core.synastry.graha_drishti import build_graha_drishti_contacts
    from core.synastry.conjunctions import find_conjunctions
    from core.synastry.interpretation import enrich_graha_drishti_contacts, enrich_conjunction_contacts
    from core.synastry.nakshatra_matching import compute_nakshatra_synastry
    from core.synastry.transit_activations import build_natal_synastry_links
    from core.constants import RASHI, RASHI_LORD

    ctx_a = get_natal_context(person_a)
    ctx_b = get_natal_context(person_b)
    config = SynastryConfig()

    seventh_lord_a = RASHI_LORD[RASHI[(ctx_a.ascendant_sign_index + 6) % 12]]
    seventh_lord_b = RASHI_LORD[RASHI[(ctx_b.ascendant_sign_index + 6) % 12]]
    asc_lord_a = RASHI_LORD[RASHI[ctx_a.ascendant_sign_index]]
    asc_lord_b = RASHI_LORD[RASHI[ctx_b.ascendant_sign_index]]

    karaka_a = {p: pos for p, pos in ctx_a.positions.items() if p != "Ketu"}
    karaka_b = {p: pos for p, pos in ctx_b.positions.items() if p != "Ketu"}
    dk_a = get_darakaraka(karaka_a).planet
    dk_b = get_darakaraka(karaka_b).planet

    drishti = enrich_graha_drishti_contacts(
        build_graha_drishti_contacts(ctx_a, ctx_b, "A", "B", config) +
        build_graha_drishti_contacts(ctx_b, ctx_a, "B", "A", config)
    )
    points_a = {n: p.longitude for n, p in ctx_a.positions.items()}
    points_b = {n: p.longitude for n, p in ctx_b.positions.items()}
    conjunctions = enrich_conjunction_contacts(find_conjunctions(points_a, points_b, config))
    nakshatra_result = compute_nakshatra_synastry(ctx_a, ctx_b, seventh_lord_a, seventh_lord_b, dk_a, dk_b)
    links = build_natal_synastry_links(ctx_a, ctx_b, drishti, conjunctions, nakshatra_result)

    snapshot = compute_predictive_snapshot(
        ctx_a, ctx_b, datetime(2026, 6, 15, 12, tzinfo=timezone.utc),
        links, seventh_lord_a, seventh_lord_b, dk_a, dk_b, asc_lord_a, asc_lord_b, config,
    )
    assert snapshot.date_label == "2026-06-15"
    assert len(snapshot.transits_a) == 9
    assert len(snapshot.transits_b) == 9
    assert isinstance(snapshot.activations, list)
    assert snapshot.dasha_result.profile_a.person_label == "A"


def test_timeline_runs_and_produces_points(person_a, person_b):
    from core.natal import get_natal_context
    from core.chara_karaka import get_darakaraka
    from core.synastry.graha_drishti import build_graha_drishti_contacts
    from core.synastry.conjunctions import find_conjunctions
    from core.synastry.interpretation import enrich_graha_drishti_contacts, enrich_conjunction_contacts
    from core.synastry.nakshatra_matching import compute_nakshatra_synastry
    from core.synastry.transit_activations import build_natal_synastry_links
    from core.constants import RASHI, RASHI_LORD

    ctx_a = get_natal_context(person_a)
    ctx_b = get_natal_context(person_b)
    config = SynastryConfig()

    seventh_lord_a = RASHI_LORD[RASHI[(ctx_a.ascendant_sign_index + 6) % 12]]
    seventh_lord_b = RASHI_LORD[RASHI[(ctx_b.ascendant_sign_index + 6) % 12]]
    asc_lord_a = RASHI_LORD[RASHI[ctx_a.ascendant_sign_index]]
    asc_lord_b = RASHI_LORD[RASHI[ctx_b.ascendant_sign_index]]

    karaka_a = {p: pos for p, pos in ctx_a.positions.items() if p != "Ketu"}
    karaka_b = {p: pos for p, pos in ctx_b.positions.items() if p != "Ketu"}
    dk_a = get_darakaraka(karaka_a).planet
    dk_b = get_darakaraka(karaka_b).planet

    drishti = enrich_graha_drishti_contacts(
        build_graha_drishti_contacts(ctx_a, ctx_b, "A", "B", config) +
        build_graha_drishti_contacts(ctx_b, ctx_a, "B", "A", config)
    )
    points_a = {n: p.longitude for n, p in ctx_a.positions.items()}
    points_b = {n: p.longitude for n, p in ctx_b.positions.items()}
    conjunctions = enrich_conjunction_contacts(find_conjunctions(points_a, points_b, config))
    nakshatra_result = compute_nakshatra_synastry(ctx_a, ctx_b, seventh_lord_a, seventh_lord_b, dk_a, dk_b)
    links = build_natal_synastry_links(ctx_a, ctx_b, drishti, conjunctions, nakshatra_result)

    progress_calls = []
    points = compute_timeline(
        ctx_a, ctx_b, date(2026, 6, 1), date(2026, 6, 5), 1,
        links, seventh_lord_a, seventh_lord_b, dk_a, dk_b, asc_lord_a, asc_lord_b, config,
        progress_callback=progress_calls.append,
    )
    assert len(points) == 5
    assert all(p.total_strength >= 0.0 for p in points)
    assert len(progress_calls) > 0
