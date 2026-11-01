from core.synastry.config import SynastryConfig
from core.synastry.models import NatalSynastryLink
from core.synastry.transit_activations import compute_link_activations, build_natal_synastry_links
from tests.conftest import make_planet_position


def _link(anchor_a=10.0, anchor_b=190.0):
    return NatalSynastryLink(
        link_id="test:0", link_type="conjunction",
        person_a_object="Venera (A)", person_b_object="Mars (B)",
        anchor_longitude_a=anchor_a, anchor_longitude_b=anchor_b,
        description="test veza",
    )


def test_normal_conjunction_activation_detected():
    link = _link(anchor_a=10.0, anchor_b=190.0)
    transit_positions = {"Jupiter": make_planet_position(10.5)}  # unutar Jupiterovog orba (5.0)
    config = SynastryConfig()
    activations = compute_link_activations([link], transit_positions, config)
    assert len(activations) == 1
    assert "konjunkcija" in activations[0].activation_types


def test_negative_case_no_activation_when_far_and_unrelated():
    link = _link(anchor_a=10.0, anchor_b=190.0)
    # Merkur na 45° - znak 1, udaljenost od oba sidrišta izvan Graha Drishti
    # skupa (3,4,5,7,8,9,10) i bez podudaranja znaka/nakšatre/dispozitora/vladara/D9.
    transit_positions = {"Merkur": make_planet_position(45.0)}
    config = SynastryConfig()
    activations = compute_link_activations([link], transit_positions, config)
    assert activations == []


def test_edge_case_graha_drishti_activation_detected():
    # Jupiter na 5° (znak 0), veza na 190° (znak 6) - udaljenost 7 (puni aspekt)
    link = _link(anchor_a=190.0, anchor_b=250.0)
    transit_positions = {"Jupiter": make_planet_position(5.0)}
    config = SynastryConfig()
    activations = compute_link_activations([link], transit_positions, config)
    assert len(activations) == 1
    assert "graha_drishti" in activations[0].activation_types


def test_same_sign_activation_detected():
    link = _link(anchor_a=45.0, anchor_b=250.0)  # anchor_a u znaku 1 (Bik)
    transit_positions = {"Saturn": make_planet_position(50.0)}  # takoder znak 1
    config = SynastryConfig()
    activations = compute_link_activations([link], transit_positions, config)
    assert len(activations) == 1
    assert "isti_znak" in activations[0].activation_types


def test_dispositor_activation_detected():
    # anchor_a u Ovnu (znak0, vladar Mars) - tranzitni Mars aktivira kao "dispozitor"
    link = _link(anchor_a=10.0, anchor_b=250.0)
    transit_positions = {"Mars": make_planet_position(150.0)}  # Mars u Djevici, daleko od anchor-a po stupnju/znaku
    config = SynastryConfig()
    activations = compute_link_activations([link], transit_positions, config)
    assert len(activations) == 1
    assert "dispozitor" in activations[0].activation_types


def test_nakshatra_lord_activation_detected():
    # anchor_a na 110° (Ashlesha, vladar Merkur) - tranzitni Merkur aktivira kao "vladar_nakshatre"
    link = _link(anchor_a=110.0, anchor_b=250.0)
    transit_positions = {"Merkur": make_planet_position(300.0)}  # daleko, drugi znak/nakšatra
    config = SynastryConfig()
    activations = compute_link_activations([link], transit_positions, config)
    assert len(activations) == 1
    assert "vladar_nakshatre" in activations[0].activation_types


def test_d9_activation_detected():
    from core.varga import d9_navamsha_sign_index
    # Odaberi anchor i transit longitude koji dijele D9 znak, ali RAZLIČIT D1 znak
    # anchor na 1.0 (D1 znak0, D9 znak0), transit na 32.0 (D1 znak1 - Bik, D9: 32/3.3333=9.6 -> D9 znak9)
    # Trazimo transit lon cija D9 vrijednost odgovara anchor D9 (0) ali D1 znak razlicit od anchor D1 znak (0)
    anchor_lon = 1.0
    anchor_d9 = d9_navamsha_sign_index(anchor_lon)
    # trazi lon u D1 znaku 1 (30-60) cija D9 odgovara anchor_d9
    candidate = None
    for deg in range(30, 60):
        if d9_navamsha_sign_index(float(deg)) == anchor_d9:
            candidate = float(deg)
            break
    assert candidate is not None
    link = _link(anchor_a=anchor_lon, anchor_b=250.0)
    transit_positions = {"Venera": make_planet_position(candidate)}
    config = SynastryConfig()
    activations = compute_link_activations([link], transit_positions, config)
    assert len(activations) == 1
    assert "d9_aktivacija" in activations[0].activation_types


def test_slow_planet_weighted_higher_than_fast():
    link = _link(anchor_a=10.0, anchor_b=190.0)
    config = SynastryConfig()
    saturn_activation = compute_link_activations([link], {"Saturn": make_planet_position(10.5)}, config)[0]
    moon_activation = compute_link_activations([link], {"Mjesec": make_planet_position(10.5)}, config)[0]
    assert saturn_activation.strength > moon_activation.strength
    assert saturn_activation.is_slow_planet is True
    assert moon_activation.is_slow_planet is False


def test_build_natal_synastry_links_integration(person_a, person_b):
    from core.natal import get_natal_context
    from core.synastry.graha_drishti import build_graha_drishti_contacts
    from core.synastry.conjunctions import find_conjunctions
    from core.synastry.interpretation import enrich_graha_drishti_contacts, enrich_conjunction_contacts
    from core.synastry.nakshatra_matching import compute_nakshatra_synastry
    from core.chara_karaka import get_darakaraka

    ctx_a = get_natal_context(person_a)
    ctx_b = get_natal_context(person_b)
    config = SynastryConfig()

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
    nakshatra_result = compute_nakshatra_synastry(ctx_a, ctx_b, "Saturn", "Mjesec", dk_a, dk_b)

    links = build_natal_synastry_links(ctx_a, ctx_b, drishti, conjunctions, nakshatra_result)
    assert len(links) == len(drishti) + len(conjunctions) + sum(
        1 for l in nakshatra_result.cross_links if l.relation_type in ("same_nakshatra", "same_pada")
    )
    for link in links:
        assert 0.0 <= link.anchor_longitude_a < 360.0
        assert 0.0 <= link.anchor_longitude_b < 360.0
