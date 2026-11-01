from core.synastry.models import GrahaDrishtiContact, ConjunctionContact
from core.synastry.nakshatra_matching import (
    build_nakshatra_profile, find_same_nakshatra_links, find_same_nakshatra_lord_links,
    find_dispositor_links, find_repeated_themes, compute_nakshatra_synastry,
)
from tests.conftest import make_natal_context


def test_normal_profile_fields_are_populated():
    profile = build_nakshatra_profile("A", "Mjesec", "Mjesec", 5.0)  # Ashwini
    assert profile.nakshatra == "Ashwini"
    assert profile.pada == 2  # 5.0 / (13.3333/4=3.3333) -> pada 2
    assert profile.gana == "Deva"
    assert profile.yoni == "Konj"
    assert profile.nadi == "Vata"
    assert profile.devata == "Ashwini Kumaras"


def test_same_nakshatra_same_pada_detected():
    profiles_a = {"Mjesec": build_nakshatra_profile("A", "Mjesec", "Mjesec", 2.0)}
    profiles_b = {"Venera": build_nakshatra_profile("B", "Venera", "Venera", 2.5)}
    links = find_same_nakshatra_links(profiles_a, profiles_b)
    assert len(links) == 1
    assert links[0].relation_type == "same_pada"
    assert links[0].scored is True


def test_same_nakshatra_different_pada_detected():
    profiles_a = {"Mjesec": build_nakshatra_profile("A", "Mjesec", "Mjesec", 1.0)}    # pada 1
    profiles_b = {"Venera": build_nakshatra_profile("B", "Venera", "Venera", 10.0)}   # pada 3
    links = find_same_nakshatra_links(profiles_a, profiles_b)
    assert len(links) == 1
    assert links[0].relation_type == "same_nakshatra"


def test_same_nakshatra_lord_detected():
    """Dvije RAZLIČITE nakšatre, ali isti vladar - vlastita, potvrđena kategorija (2)."""
    profiles_a = {"Mjesec": build_nakshatra_profile("A", "Mjesec", "Mjesec", 110.0)}   # Ashlesha, vladar Merkur
    profiles_b = {"Venera": build_nakshatra_profile("B", "Venera", "Venera", 230.0)}   # Jyeshtha, vladar Merkur
    links = find_same_nakshatra_lord_links(profiles_a, profiles_b)
    assert len(links) == 1
    assert links[0].relation_type == "same_nakshatra_lord"
    assert links[0].scored is True


def test_dispositor_symbolic_without_confirmation_is_not_scored():
    """
    Regresijski test za bivšu grešku ("lažne nakšatra unakrsne veze"): SAMO
    "vladar nakšatre = planet druge osobe" (bez ikakvog dodatnog kontakta)
    smije proizvesti isključivo slabu, NEBODOVANU napomenu (kategorija 5).
    """
    profiles_a = {"Mjesec": build_nakshatra_profile("A", "Mjesec", "Mjesec", 110.0)}  # Ashlesha, vladar Merkur
    profiles_b = {"Merkur": build_nakshatra_profile("B", "Merkur", "Merkur", 40.0)}
    links = find_dispositor_links(profiles_a, profiles_b, graha_drishti_contacts=[], conjunctions=[])
    assert len(links) == 1
    assert links[0].relation_type == "dispositor_symbolic"
    assert links[0].scored is False


def test_dispositor_confirmed_by_real_aspect_is_scored():
    """Isti kandidat kao gore, ali SADA postoji stvaran Graha Drishti između te dvije točke -> kategorija 4."""
    profiles_a = {"Mjesec": build_nakshatra_profile("A", "Mjesec", "Mjesec", 110.0)}  # Ashlesha, vladar Merkur
    profiles_b = {"Merkur": build_nakshatra_profile("B", "Merkur", "Merkur", 40.0)}
    confirming_contact = GrahaDrishtiContact(
        source_person="A", target_person="B", from_planet="Mjesec", to_planet="Merkur",
        house_distance=7, strength=1.0, strength_label="puni (100%)",
        from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
    )
    links = find_dispositor_links(profiles_a, profiles_b, graha_drishti_contacts=[confirming_contact], conjunctions=[])
    assert len(links) == 1
    assert links[0].relation_type == "dispositor_confirmed"
    assert links[0].scored is True


def test_negative_case_no_dispositor_link_when_unrelated():
    profiles_a = {"Mjesec": build_nakshatra_profile("A", "Mjesec", "Mjesec", 110.0)}  # vladar Merkur
    profiles_b = {"Venera": build_nakshatra_profile("B", "Venera", "Venera", 40.0)}     # nije Merkur
    links = find_dispositor_links(profiles_a, profiles_b, graha_drishti_contacts=[], conjunctions=[])
    assert links == []


def test_mutual_dispositor_detected_when_reciprocal():
    # A's Mjesec je u Ashlesha (vladar Merkur) - B ima ulogu "Merkur".
    # B's Merkur je u Rohini (vladar Mjesec) - A ima ulogu "Mjesec". Uzajamna dispozicija.
    profiles_a = {"Mjesec": build_nakshatra_profile("A", "Mjesec", "Mjesec", 110.0)}   # Ashlesha, vladar Merkur
    profiles_b = {"Merkur": build_nakshatra_profile("B", "Merkur", "Merkur", 45.0)}     # Rohini, vladar Mjesec

    links = find_dispositor_links(profiles_a, profiles_b, graha_drishti_contacts=[], conjunctions=[])
    assert len(links) == 1
    assert links[0].relation_type == "mutual_dispositor"
    assert links[0].scored is True


def test_repeated_theme_detected_across_multiple_points():
    profiles_a = {
        "Mjesec": build_nakshatra_profile("A", "Mjesec", "Mjesec", 5.0),   # Ashwini
        "Venera": build_nakshatra_profile("A", "Venera", "Venera", 200.0),
    }
    profiles_b = {
        "Mars": build_nakshatra_profile("B", "Mars", "Mars", 8.0),  # Ashwini isto
    }
    themes = find_repeated_themes(profiles_a, profiles_b)
    ashwini_theme = next(t for t in themes if t.nakshatra == "Ashwini")
    assert len(ashwini_theme.points_involved) == 2


def test_full_nakshatra_synastry_runs_without_errors_on_real_context():
    ctx_a = make_natal_context(ascendant_longitude=10.0, planet_longitudes={
        "Sunce": 20.0, "Mjesec": 100.0, "Venera": 40.0, "Mars": 150.0,
    })
    ctx_b = make_natal_context(ascendant_longitude=190.0, planet_longitudes={
        "Sunce": 60.0, "Mjesec": 200.0, "Venera": 90.0, "Mars": 250.0,
    })
    result = compute_nakshatra_synastry(
        ctx_a, ctx_b,
        seventh_lord_a="Saturn", seventh_lord_b="Mjesec",
        darakaraka_a="Venera", darakaraka_b="Mars",
    )
    assert set(result.profiles_a.keys()) == {"Mjesec", "Ascendent", "Venera", "Mars", "Sunce", "Vladar 7.", "Darakaraka"}
    assert set(result.profiles_b.keys()) == {"Mjesec", "Ascendent", "Venera", "Mars", "Sunce", "Vladar 7.", "Darakaraka"}
