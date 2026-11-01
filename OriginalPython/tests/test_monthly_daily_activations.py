from datetime import date

from core.natal import get_natal_context
from core.synastry.config import SynastryConfig
from core.synastry.monthly_daily_activations import (
    compute_moon_daily_highlights, compute_moon_trigger_days_over_range,
)
from core.synastry.transit_activations import build_natal_synastry_links


def _setup(person_a, person_b):
    from core.synastry.graha_drishti import build_graha_drishti_contacts
    from core.synastry.conjunctions import find_conjunctions
    from core.synastry.interpretation import enrich_graha_drishti_contacts, enrich_conjunction_contacts
    from core.synastry.nakshatra_matching import compute_nakshatra_synastry
    from core.chara_karaka import get_darakaraka
    from core.constants import RASHI, RASHI_LORD

    ctx_a = get_natal_context(person_a)
    ctx_b = get_natal_context(person_b)
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
    return ctx_a, ctx_b, links, seventh_lord_a, seventh_lord_b, dk_a, dk_b, config


def test_normal_daily_highlight_runs_without_errors(person_a, person_b):
    ctx_a, ctx_b, links, sl_a, sl_b, dk_a, dk_b, config = _setup(person_a, person_b)
    result = compute_moon_daily_highlights(ctx_a, ctx_b, links, date(2026, 6, 15), sl_a, sl_b, dk_a, dk_b, config)
    assert result.date_label == "2026-06-15"
    assert isinstance(result.notes, list)


def test_edge_case_moon_crossing_own_natal_moon_sign_detected(person_a, person_b):
    """
    Pronadji datum u sljedecih 30 dana kad tranzitni Mjesec dijeli znak s
    natalnim Mjesecom osobe A (Mjesec prolazi kroz sav zodijak za ~27-28 dana,
    pa mora postojati barem jedan takav dan u mjesec dana).
    """
    from datetime import timedelta
    ctx_a, ctx_b, links, sl_a, sl_b, dk_a, dk_b, config = _setup(person_a, person_b)
    found = False
    for i in range(30):
        d = date(2026, 6, 1) + timedelta(days=i)
        result = compute_moon_daily_highlights(ctx_a, ctx_b, links, d, sl_a, sl_b, dk_a, dk_b, config)
        if any("Mjesec (A)" in n for n in result.notes):
            found = True
            break
    assert found


def test_negative_case_no_false_positive_when_unrelated_range(person_a, person_b):
    """Pojedini dan i dalje mora vratiti listu (moguće praznu), bez pucanja, cak i s praznim natal_links."""
    ctx_a, ctx_b, _, sl_a, sl_b, dk_a, dk_b, config = _setup(person_a, person_b)
    result = compute_moon_daily_highlights(ctx_a, ctx_b, [], date(2026, 6, 15), sl_a, sl_b, dk_a, dk_b, config)
    assert isinstance(result.notes, list)  # ne smije puknuti s praznim links


def test_range_computation_returns_only_nonempty_days(person_a, person_b):
    ctx_a, ctx_b, links, sl_a, sl_b, dk_a, dk_b, config = _setup(person_a, person_b)
    progress_calls = []
    days = compute_moon_trigger_days_over_range(
        ctx_a, ctx_b, links, date(2026, 6, 1), date(2026, 6, 10),
        sl_a, sl_b, dk_a, dk_b, config, progress_callback=progress_calls.append,
    )
    assert all(len(d.notes) > 0 for d in days)
    assert len(progress_calls) > 0
