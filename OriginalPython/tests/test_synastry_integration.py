"""
Integracijski testovi - koriste PRAVI Swiss Ephemeris izračun (core.natal)
za dvije fiksne osobe (tests/conftest.py), bez geokodiranja. Provjeravaju
da cijeli lanac (natal kontekst -> overlay/drishti/konjunkcije -> izvještaj)
radi zajedno bez pucanja i da su rezultati interno konzistentni.
"""

from core.constants import PLANET_ORDER
from core.natal import get_natal_context
from core.synastry.config import SynastryConfig
from core.synastry.conjunctions import find_conjunctions
from core.synastry.graha_drishti import build_graha_drishti_contacts
from core.synastry.interpretation import enrich_conjunction_contacts, enrich_graha_drishti_contacts
from core.synastry.overlays import compute_house_overlay, find_mutual_emphasis
from core.synastry.report import build_basic_report


def test_natal_context_sanity(person_a):
    ctx = get_natal_context(person_a)
    assert 0.0 <= ctx.ascendant_longitude < 360.0
    assert set(ctx.positions.keys()) == set(PLANET_ORDER)
    for name in PLANET_ORDER:
        assert 0.0 <= ctx.positions[name].longitude < 360.0


def test_house_overlay_covers_all_planets_both_directions(person_a, person_b):
    ctx_a = get_natal_context(person_a)
    ctx_b = get_natal_context(person_b)
    overlay_a_to_b = compute_house_overlay(ctx_a, ctx_b, "A", "B")
    overlay_b_to_a = compute_house_overlay(ctx_b, ctx_a, "B", "A")
    assert len(overlay_a_to_b) == len(PLANET_ORDER)
    assert len(overlay_b_to_a) == len(PLANET_ORDER)
    assert all(1 <= r.whole_sign_house <= 12 for r in overlay_a_to_b)


def test_graha_drishti_runs_both_directions_with_all_node_modes(person_a, person_b):
    ctx_a = get_natal_context(person_a)
    ctx_b = get_natal_context(person_b)
    for mode in ("seventh_only", "5_7_9", "none"):
        config = SynastryConfig(node_aspect_mode=mode)
        contacts_ab = build_graha_drishti_contacts(ctx_a, ctx_b, "A", "B", config)
        contacts_ba = build_graha_drishti_contacts(ctx_b, ctx_a, "B", "A", config)
        for c in contacts_ab + contacts_ba:
            assert c.strength in (0.25, 0.5, 0.75, 1.0)
            assert 1 <= c.house_distance <= 12


def test_full_basic_report_builds_without_errors(person_a, person_b):
    ctx_a = get_natal_context(person_a)
    ctx_b = get_natal_context(person_b)
    config = SynastryConfig()

    overlay_a_to_b = compute_house_overlay(ctx_a, ctx_b, "A", "B")
    overlay_b_to_a = compute_house_overlay(ctx_b, ctx_a, "B", "A")
    mutual_notes = find_mutual_emphasis(overlay_a_to_b, overlay_b_to_a)

    drishti_a_to_b = enrich_graha_drishti_contacts(build_graha_drishti_contacts(ctx_a, ctx_b, "A", "B", config))
    drishti_b_to_a = enrich_graha_drishti_contacts(build_graha_drishti_contacts(ctx_b, ctx_a, "B", "A", config))

    points_a = {name: pos.longitude for name, pos in ctx_a.positions.items()}
    points_b = {name: pos.longitude for name, pos in ctx_b.positions.items()}
    conjunctions = enrich_conjunction_contacts(find_conjunctions(points_a, points_b, config))

    report = build_basic_report(
        person_a.name, person_a.birth_date, person_b.name, person_b.birth_date,
        ctx_a, ctx_b, "Ljubavni/partnerski odnos", config,
        overlay_a_to_b, overlay_b_to_a, mutual_notes,
        drishti_a_to_b, drishti_b_to_a, conjunctions,
    )

    assert "SINASTRIJA" in report
    assert person_a.name in report
    assert person_b.name in report
    assert "## 3. Kućni overlay (D1)" in report
    assert "## 4. Graha Drishti" in report
    assert "## 5. Stupanjske konjunkcije" in report
    assert "Tehnički dodatak" in report
