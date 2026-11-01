"""
Integracijski test - referentni primjer iz zahtjeva za ispravak sinastrije:
Lea (04.11.1985. 01:15, Sisak) i Marko Vujnović (26.12.1976. 11:55, Sisak),
sideralni zodijak/Lahiri/Mean Node/Whole Sign/7-karaka (sve zadane postavke
aplikacije - core.synastry.config.SynastryConfig()).

Cilj OVOG testa nije provjeriti egzaktne brojeve (zahtjev eksplicitno kaže
da rezultat ne mora biti unaprijed fiksiran), nego STRUKTURNA svojstva koja
dokazuju da su bivše greške ispravljene:
  (a) promjena vrste odnosa NE mijenja astronomske položaje/sirove kontakte
  (b) A/B identitet je očuvan u svakom unakrsnom kontaktu
  (c) nijedna kategorija ne "flatlinea" na stropu (bivši nalaz: 97-99/100
      za gotovo svaku kategoriju)
  (d) grubi (bucket) kvalitativni profil je razuman (ne ekstreman u svim
      kategorijama istovremeno) - vidi _score_bucket.
"""

import pytest

from core.chara_karaka import get_atmakaraka, get_darakaraka
from core.constants import RASHI, RASHI_LORD
from core.natal import get_natal_context
from core.synastry.ashtakoota import compute_ashtakoota
from core.synastry.config import SynastryConfig
from core.synastry.conjunctions import find_conjunctions
from core.synastry.deduplication import build_role_map
from core.synastry.divisional_synastry import compute_navamsha_synastry
from core.synastry.graha_drishti import build_graha_drishti_contacts
from core.synastry.interpretation import (
    enrich_conjunction_contacts, enrich_graha_drishti_contacts,
    enrich_graha_drishti_contacts_with_axis_context,
)
from core.synastry.kuja_dosha import compare_kuja_dosha
from core.synastry.nakshatra_matching import compute_nakshatra_synastry
from core.synastry.overlays import compute_house_overlay, find_mutual_emphasis
from core.synastry.relationship_profiles import RELATIONSHIP_TYPE_KEYS, get_relationship_profile
from core.synastry.relationship_significators import compute_relationship_significators
from core.synastry.report import build_basic_report
from core.synastry.scoring import compute_synastry_scores
from core.synastry.scoring_config import CATEGORY_NAMES


def _seventh_lord(asc_idx: int) -> str:
    return RASHI_LORD[RASHI[(asc_idx + 6) % 12]]


def _house_lord(asc_idx: int, house_num: int) -> str:
    return RASHI_LORD[RASHI[(asc_idx + house_num - 1) % 12]]


def _run_full_pipeline(person_lea, person_marko, relationship_type_key: str):
    """Puni cjevovod - identičan onome u ui/pages_synastry.py - za zadanu vrstu odnosa."""
    ctx_a = get_natal_context(person_lea)
    ctx_b = get_natal_context(person_marko)
    config = SynastryConfig()

    overlay_a_to_b = compute_house_overlay(ctx_a, ctx_b, "A", "B")
    overlay_b_to_a = compute_house_overlay(ctx_b, ctx_a, "B", "A")
    mutual_notes = find_mutual_emphasis(overlay_a_to_b, overlay_b_to_a)

    drishti_a_to_b = enrich_graha_drishti_contacts(build_graha_drishti_contacts(ctx_a, ctx_b, "A", "B", config), ctx_a, ctx_b)
    drishti_b_to_a = enrich_graha_drishti_contacts(build_graha_drishti_contacts(ctx_b, ctx_a, "B", "A", config), ctx_a, ctx_b)

    points_a = {name: pos.longitude for name, pos in ctx_a.positions.items()}
    points_a["Lagna"] = ctx_a.ascendant_longitude
    points_b = {name: pos.longitude for name, pos in ctx_b.positions.items()}
    points_b["Lagna"] = ctx_b.ascendant_longitude
    seventh_lord_a, seventh_lord_b = _seventh_lord(ctx_a.ascendant_sign_index), _seventh_lord(ctx_b.ascendant_sign_index)
    conjunctions = enrich_conjunction_contacts(
        find_conjunctions(points_a, points_b, config, seventh_lord_a, seventh_lord_b)
    )

    karaka_a = {p: pos for p, pos in ctx_a.positions.items() if p != "Ketu"}
    karaka_b = {p: pos for p, pos in ctx_b.positions.items() if p != "Ketu"}
    darakaraka_a = get_darakaraka(karaka_a, config.chara_karaka_scheme).planet
    darakaraka_b = get_darakaraka(karaka_b, config.chara_karaka_scheme).planet
    atmakaraka_a = get_atmakaraka(karaka_a, config.chara_karaka_scheme).planet
    atmakaraka_b = get_atmakaraka(karaka_b, config.chara_karaka_scheme).planet

    nakshatra_result = compute_nakshatra_synastry(
        ctx_a, ctx_b, seventh_lord_a, seventh_lord_b, darakaraka_a, darakaraka_b,
        drishti_a_to_b + drishti_b_to_a, conjunctions,
    )
    ashtakoota_result = compute_ashtakoota(ctx_a.positions["Mjesec"].longitude, ctx_b.positions["Mjesec"].longitude)
    kuja_comparison = compare_kuja_dosha(ctx_a, ctx_b, config)
    significators_result = compute_relationship_significators(ctx_a, ctx_b, config, drishti_a_to_b + drishti_b_to_a, conjunctions)
    navamsha_result = compute_navamsha_synastry(
        ctx_a, ctx_b, config, seventh_lord_a, seventh_lord_b,
        darakaraka_a, darakaraka_b, atmakaraka_a, atmakaraka_b,
        drishti_a_to_b + drishti_b_to_a, conjunctions,
    )
    enrich_graha_drishti_contacts_with_axis_context(drishti_a_to_b, ctx_a, ctx_b, navamsha_result)
    enrich_graha_drishti_contacts_with_axis_context(drishti_b_to_a, ctx_a, ctx_b, navamsha_result)

    role_map = build_role_map(
        darakaraka_a=darakaraka_a, atmakaraka_a=atmakaraka_a, seventh_lord_a=seventh_lord_a,
        darakaraka_b=darakaraka_b, atmakaraka_b=atmakaraka_b, seventh_lord_b=seventh_lord_b,
        upapada_lord_a=significators_result.profile_a.upapada_lord,
        upapada_lord_b=significators_result.profile_b.upapada_lord,
        first_lord_a=RASHI_LORD[RASHI[ctx_a.ascendant_sign_index]], first_lord_b=RASHI_LORD[RASHI[ctx_b.ascendant_sign_index]],
        fifth_lord_a=_house_lord(ctx_a.ascendant_sign_index, 5), fifth_lord_b=_house_lord(ctx_b.ascendant_sign_index, 5),
        eighth_lord_a=_house_lord(ctx_a.ascendant_sign_index, 8), eighth_lord_b=_house_lord(ctx_b.ascendant_sign_index, 8),
        eleventh_lord_a=_house_lord(ctx_a.ascendant_sign_index, 11), eleventh_lord_b=_house_lord(ctx_b.ascendant_sign_index, 11),
        darapada_lord_a=RASHI_LORD[significators_result.profile_a.darapada_sign],
        darapada_lord_b=RASHI_LORD[significators_result.profile_b.darapada_sign],
    )

    profile = get_relationship_profile(relationship_type_key)
    score_result = compute_synastry_scores(
        drishti_a_to_b + drishti_b_to_a, conjunctions, overlay_a_to_b + overlay_b_to_a,
        ashtakoota_result, kuja_comparison, nakshatra_result, navamsha_result, role_map,
        profile.category_weight_multipliers,
    )

    return {
        "ctx_a": ctx_a, "ctx_b": ctx_b,
        "overlay_a_to_b": overlay_a_to_b, "overlay_b_to_a": overlay_b_to_a,
        "drishti_a_to_b": drishti_a_to_b, "drishti_b_to_a": drishti_b_to_a,
        "conjunctions": conjunctions, "nakshatra_result": nakshatra_result,
        "ashtakoota_result": ashtakoota_result, "kuja_comparison": kuja_comparison,
        "significators_result": significators_result, "navamsha_result": navamsha_result,
        "score_result": score_result, "profile": profile, "config": config,
        "mutual_notes": mutual_notes,
    }


@pytest.fixture
def lea_marko_love(person_lea, person_marko):
    return _run_full_pipeline(person_lea, person_marko, "ljubavni_partnerski")


def test_normal_relationship_type_does_not_change_astronomical_facts(person_lea, person_marko):
    """
    Spec 1: vrsta odnosa smije mijenjati SAMO naglasak/bodovanje, NIKAD
    astronomske položaje - usporedi "ljubavni/partnerski" naspram "poslovni"
    za ISTI par i provjeri da su ctx/sirovi kontakti bit-identični.
    """
    love = _run_full_pipeline(person_lea, person_marko, "ljubavni_partnerski")
    business = _run_full_pipeline(person_lea, person_marko, "poslovni")

    assert love["ctx_a"].ascendant_longitude == business["ctx_a"].ascendant_longitude
    assert love["ctx_b"].ascendant_longitude == business["ctx_b"].ascendant_longitude
    for planet in love["ctx_a"].positions:
        assert love["ctx_a"].positions[planet].longitude == business["ctx_a"].positions[planet].longitude

    assert len(love["drishti_a_to_b"]) == len(business["drishti_a_to_b"])
    for c1, c2 in zip(love["drishti_a_to_b"], business["drishti_a_to_b"]):
        assert c1.from_planet == c2.from_planet
        assert c1.to_planet == c2.to_planet
        assert c1.house_distance == c2.house_distance
        assert c1.strength == c2.strength

    assert len(love["conjunctions"]) == len(business["conjunctions"])
    assert [ (c.person_a_object, c.person_b_object, c.degree_distance) for c in love["conjunctions"] ] == \
           [ (c.person_a_object, c.person_b_object, c.degree_distance) for c in business["conjunctions"] ]

    # Bodovanje SMIJE biti drukčije (naglasak/emphasis) - to je jedina dopuštena razlika.
    assert love["score_result"].categories != business["score_result"].categories or \
           love["profile"].category_weight_multipliers != business["profile"].category_weight_multipliers


def test_normal_all_relationship_types_run_without_errors(person_lea, person_marko):
    for key in RELATIONSHIP_TYPE_KEYS:
        result = _run_full_pipeline(person_lea, person_marko, key)
        assert set(result["score_result"].categories.keys()) == set(CATEGORY_NAMES)


def test_normal_no_a_b_identity_violation_in_any_cross_contact(lea_marko_love):
    """Nijedan unakrsni Graha Drishti/konjunkcija kontakt ne smije imati source_person == target_person."""
    all_drishti = lea_marko_love["drishti_a_to_b"] + lea_marko_love["drishti_b_to_a"]
    for c in all_drishti:
        assert c.source_person != c.target_person

    for overlay in (lea_marko_love["overlay_a_to_b"], lea_marko_love["overlay_b_to_a"]):
        for r in overlay:
            assert r.source_person != r.target_person


def test_normal_no_category_flatlines_at_ceiling(lea_marko_love):
    """
    Regresijski test za prijavljenu grešku (97-99/100 za gotovo svaku
    kategoriju) - nijedna kategorija ne smije doseći strop.
    """
    categories = lea_marko_love["score_result"].categories
    flatlined = [cat for cat, cs in categories.items() if cs.score >= 95.0]
    assert flatlined == [], f"Kategorije preblizu stropu: {flatlined}"
    for cat, cs in categories.items():
        assert 0.0 <= cs.score <= 100.0


def test_normal_kuja_dosha_asymmetry_is_preserved(lea_marko_love):
    """Kuja Dosha usporedba ne smije tiho izjednačiti različit intenzitet kod dviju osoba."""
    kuja = lea_marko_love["kuja_comparison"]
    if kuja.person_a.severity != kuja.person_b.severity and kuja.mutual_balancing:
        assert 0.0 <= kuja.balancing_fraction < 1.0


def test_normal_nakshatra_symbolic_links_are_never_scored(lea_marko_love):
    """Kategorija 5 (dispositor_symbolic) ne smije nositi bod (scored=False za sve takve veze)."""
    for link in lea_marko_love["nakshatra_result"].cross_links:
        if link.relation_type == "dispositor_symbolic":
            assert link.scored is False


def test_normal_d1_d9_repeated_patterns_have_person_aware_keys(lea_marko_love):
    navamsha = lea_marko_love["navamsha_result"]
    assert len(navamsha.repeated_pattern_pair_keys) == len(navamsha.repeated_pattern_notes)
    for key in navamsha.repeated_pattern_pair_keys:
        assert key.startswith("A:") and "|B:" in key


def test_normal_qualitative_profile_is_not_uniformly_extreme(lea_marko_love):
    """
    Grubi (bucket) profil - NE traži egzaktne brojeve (zahtjev eksplicitno
    dopušta varijaciju), samo da profil pokazuje STVARNU diferencijaciju
    (ne "sve je 95+" kao u bivšoj grešci) i da su ključne kategorije iz
    referentnog profila prisutne i unutar razumnog (0-100) raspona.
    """
    categories = lea_marko_love["score_result"].categories
    scores = [cs.score for cs in categories.values()]
    # Barem vidljiva razlika između najnižeg i najvišeg rezultata (diferencijacija).
    assert max(scores) - min(scores) > 5.0
    for cat in ("Konflikt i pritisak", "Karmička/intenzivna povezanost", "Praktična kompatibilnost", "Stabilnost"):
        assert cat in categories


def test_normal_full_report_and_pdf_generate_without_errors(person_lea, person_marko, lea_marko_love):
    from core.synastry.export import build_pdf_report

    report_text = build_basic_report(
        person_lea.name, person_lea.birth_date, person_marko.name, person_marko.birth_date,
        lea_marko_love["ctx_a"], lea_marko_love["ctx_b"], lea_marko_love["profile"].label, lea_marko_love["config"],
        lea_marko_love["overlay_a_to_b"], lea_marko_love["overlay_b_to_a"], lea_marko_love["mutual_notes"],
        lea_marko_love["drishti_a_to_b"], lea_marko_love["drishti_b_to_a"], lea_marko_love["conjunctions"],
        lea_marko_love["nakshatra_result"], lea_marko_love["ashtakoota_result"], lea_marko_love["kuja_comparison"],
        lea_marko_love["significators_result"], lea_marko_love["navamsha_result"], lea_marko_love["score_result"],
        lea_marko_love["profile"],
    )
    assert "Lea" in report_text
    assert "Marko Vujnović" in report_text
    assert "## 12. Zaključak" in report_text or "Zaključak" in report_text
    assert "Osnovna priroda odnosa" in report_text
    assert "Vremenska napomena" in report_text

    pdf_bytes = build_pdf_report(report_text, "Sinastrija - Lea i Marko Vujnović")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
