import json

from core.natal import get_natal_context
from core.synastry.config import SynastryConfig
from core.synastry.export import build_csv_contacts, build_csv_timeline, build_json_export, build_pdf_report
from core.synastry.models import TimelinePoint


def _full_pipeline(person_a, person_b):
    from core.synastry.overlays import compute_house_overlay
    from core.synastry.graha_drishti import build_graha_drishti_contacts
    from core.synastry.conjunctions import find_conjunctions
    from core.synastry.interpretation import enrich_graha_drishti_contacts, enrich_conjunction_contacts
    from core.synastry.nakshatra_matching import compute_nakshatra_synastry
    from core.synastry.ashtakoota import compute_ashtakoota
    from core.synastry.kuja_dosha import compare_kuja_dosha
    from core.synastry.relationship_significators import compute_relationship_significators
    from core.synastry.divisional_synastry import compute_navamsha_synastry
    from core.synastry.scoring import compute_synastry_scores
    from core.chara_karaka import get_atmakaraka, get_darakaraka
    from core.constants import RASHI, RASHI_LORD

    ctx_a = get_natal_context(person_a)
    ctx_b = get_natal_context(person_b)
    config = SynastryConfig()

    overlay_a_to_b = compute_house_overlay(ctx_a, ctx_b, "A", "B")
    overlay_b_to_a = compute_house_overlay(ctx_b, ctx_a, "B", "A")
    drishti_a_to_b = enrich_graha_drishti_contacts(build_graha_drishti_contacts(ctx_a, ctx_b, "A", "B", config))
    drishti_b_to_a = enrich_graha_drishti_contacts(build_graha_drishti_contacts(ctx_b, ctx_a, "B", "A", config))
    points_a = {n: p.longitude for n, p in ctx_a.positions.items()}
    points_b = {n: p.longitude for n, p in ctx_b.positions.items()}
    conjunctions = enrich_conjunction_contacts(find_conjunctions(points_a, points_b, config))

    seventh_lord_a = RASHI_LORD[RASHI[(ctx_a.ascendant_sign_index + 6) % 12]]
    seventh_lord_b = RASHI_LORD[RASHI[(ctx_b.ascendant_sign_index + 6) % 12]]
    karaka_a = {p: pos for p, pos in ctx_a.positions.items() if p != "Ketu"}
    karaka_b = {p: pos for p, pos in ctx_b.positions.items() if p != "Ketu"}
    dk_a, dk_b = get_darakaraka(karaka_a).planet, get_darakaraka(karaka_b).planet
    ak_a, ak_b = get_atmakaraka(karaka_a).planet, get_atmakaraka(karaka_b).planet

    nakshatra_result = compute_nakshatra_synastry(ctx_a, ctx_b, seventh_lord_a, seventh_lord_b, dk_a, dk_b)
    ashtakoota_result = compute_ashtakoota(ctx_a.positions["Mjesec"].longitude, ctx_b.positions["Mjesec"].longitude)
    kuja_comparison = compare_kuja_dosha(ctx_a, ctx_b, config)
    significators_result = compute_relationship_significators(ctx_a, ctx_b, config, drishti_a_to_b + drishti_b_to_a, conjunctions)
    navamsha_result = compute_navamsha_synastry(
        ctx_a, ctx_b, config, seventh_lord_a, seventh_lord_b, dk_a, dk_b, ak_a, ak_b,
        drishti_a_to_b + drishti_b_to_a, conjunctions,
    )
    score_result = compute_synastry_scores(
        drishti_a_to_b + drishti_b_to_a, conjunctions, overlay_a_to_b + overlay_b_to_a,
        ashtakoota_result, kuja_comparison, nakshatra_result, navamsha_result,
    )
    return dict(
        config=config, overlay_a_to_b=overlay_a_to_b, overlay_b_to_a=overlay_b_to_a,
        drishti_a_to_b=drishti_a_to_b, drishti_b_to_a=drishti_b_to_a, conjunctions=conjunctions,
        nakshatra_result=nakshatra_result, ashtakoota_result=ashtakoota_result,
        kuja_comparison=kuja_comparison, significators_result=significators_result,
        navamsha_result=navamsha_result, score_result=score_result,
    )


def test_normal_json_export_is_valid_json_with_required_fields(person_a, person_b):
    data = _full_pipeline(person_a, person_b)
    text = build_json_export(person_a, person_b, "Brak", **data)
    parsed = json.loads(text)
    assert "algorithm_version" in parsed
    assert "calculation_date_utc" in parsed
    assert parsed["settings"]["ayanamsha"] == "Lahiri"
    assert parsed["settings"]["node_type"] == "Mean Node"
    assert parsed["input"]["person_a"]["name"] == person_a.name
    assert parsed["input"]["person_b"]["name"] == person_b.name
    assert "house_overlay_a_to_b" in parsed["results"]
    assert "categories" in parsed["scoring"]


def test_edge_case_json_export_works_with_optional_fields_none(person_a, person_b):
    data = _full_pipeline(person_a, person_b)
    text = build_json_export(
        person_a, person_b, "Brak", data["config"],
        data["overlay_a_to_b"], data["overlay_b_to_a"],
        data["drishti_a_to_b"], data["drishti_b_to_a"], data["conjunctions"],
    )
    parsed = json.loads(text)
    assert "nakshatra_synastry" not in parsed["results"]
    assert "scoring" not in parsed


def test_csv_contacts_has_header_and_rows(person_a, person_b):
    data = _full_pipeline(person_a, person_b)
    csv_text = build_csv_contacts(data["drishti_a_to_b"], data["drishti_b_to_a"], data["conjunctions"])
    lines = csv_text.strip().split("\r\n")
    assert lines[0].startswith("Vrsta,")
    assert len(lines) > 1


def test_csv_timeline_negative_case_empty_points_gives_header_only():
    csv_text = build_csv_timeline([])
    lines = csv_text.strip().split("\r\n")
    assert len(lines) == 1
    assert lines[0].startswith("Datum,")


def test_csv_timeline_with_points():
    points = [
        TimelinePoint(date_label="2026-01-01", total_strength=1.5, active_slow_transits=["Saturn"],
                      active_dasha_lords=["Venera"], themes=["Stabilnost"], top_notes=["test"]),
    ]
    csv_text = build_csv_timeline(points)
    assert "2026-01-01" in csv_text
    assert "Saturn" in csv_text


def test_pdf_report_produces_nonempty_bytes(person_a, person_b):
    report_text = "# SINASTRIJA - Test\n\n## 1. Osnovni podaci\n- test č ć š ž đ\n"
    pdf_bytes = build_pdf_report(report_text, "Sinastrija - Test")
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 100
    assert pdf_bytes[:4] == b"%PDF"
