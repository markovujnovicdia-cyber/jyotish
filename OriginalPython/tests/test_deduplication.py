from core.synastry.deduplication import (
    contact_key, parse_contact_key, key_from_drishti_contact, key_from_conjunction,
    RoleMap, role_multiplier, combined_role_multiplier, build_role_map,
    find_cross_contact, find_cross_conjunction,
    drishti_confirmation_strength, conjunction_confirmation_strength,
)
from core.synastry.models import GrahaDrishtiContact, ConjunctionContact


def test_normal_contact_key_is_person_aware_not_a_bare_frozenset():
    """
    Regresijski test za osnovnu grešku (spec 2/4): 'A-Mars aspektira B-Venera'
    i 'B-Mars aspektira A-Venera' su DVA RAZLIČITA fizička kontakta - ne
    smiju dijeliti isti ključ (kao što bi frozenset({'Mars','Venera'}) radio).
    """
    key_ab = contact_key("Mars", "Venera")   # A-Mars, B-Venera
    key_ba = contact_key("Venera", "Mars")   # A-Venera, B-Mars (drugi fizički kontakt!)
    assert key_ab != key_ba


def test_edge_case_parse_contact_key_roundtrips():
    key = contact_key("Saturn", "Merkur")
    planet_a, planet_b = parse_contact_key(key)
    assert planet_a == "Saturn"
    assert planet_b == "Merkur"


def test_normal_key_from_drishti_contact_resolves_direction_from_source_person():
    contact_a_to_b = GrahaDrishtiContact(
        source_person="A", target_person="B", from_planet="Saturn", to_planet="Merkur",
        house_distance=7, strength=1.0, strength_label="puni (100%)",
        from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
    )
    contact_b_to_a = GrahaDrishtiContact(
        source_person="B", target_person="A", from_planet="Merkur", to_planet="Saturn",
        house_distance=7, strength=1.0, strength_label="puni (100%)",
        from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
    )
    # Oba kontakta opisuju ISTI fizički par (A-Saturn, B-Merkur) - samo je
    # aspekt zabilježen u suprotnom smjeru poziva - MORAJU dati isti ključ.
    assert key_from_drishti_contact(contact_a_to_b) == key_from_drishti_contact(contact_b_to_a) == contact_key("Saturn", "Merkur")


def test_normal_key_from_conjunction_uses_person_a_object_and_person_b_object():
    c = ConjunctionContact(
        person_a_object="Venera", person_b_object="Mars", longitude_a=10.0, longitude_b=10.5,
        sign="Ovan", degree_distance=0.5, orb_used=6.0, is_exact=True,
        same_nakshatra=True, same_pada=True, special_flags=[],
    )
    assert key_from_conjunction(c) == contact_key("Venera", "Mars")


def test_normal_find_cross_contact_does_not_swap_persons():
    """
    Regresijski test za TOČAN primjer iz prijave: Darakaraka osobe A je
    Saturn, Atmakaraka osobe B je Merkur - traženi kontakt je Saturn(A) ->
    Merkur(B), NE Merkur(A) -> Saturn(B).
    """
    wrong_direction_contact = GrahaDrishtiContact(
        source_person="A", target_person="B", from_planet="Merkur", to_planet="Saturn",
        house_distance=7, strength=1.0, strength_label="puni (100%)",
        from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
    )
    correct_contact = GrahaDrishtiContact(
        source_person="A", target_person="B", from_planet="Saturn", to_planet="Merkur",
        house_distance=7, strength=1.0, strength_label="puni (100%)",
        from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
    )
    # Samo "pogrešan smjer" prisutan - traženje Saturn(A)->Merkur(B) NE smije pogoditi ovaj kontakt.
    assert find_cross_contact([wrong_direction_contact], "Saturn", "Merkur") == []
    # Ispravan kontakt prisutan - MORA se pronaći.
    assert find_cross_contact([correct_contact], "Saturn", "Merkur") == [correct_contact]


def test_negative_case_find_cross_conjunction_respects_person_sides():
    c = ConjunctionContact(
        person_a_object="Merkur", person_b_object="Saturn", longitude_a=10.0, longitude_b=10.5,
        sign="Ovan", degree_distance=0.5, orb_used=6.0, is_exact=True,
        same_nakshatra=True, same_pada=True, special_flags=[],
    )
    # A ima Merkur, B ima Saturn ovdje - traženje Saturn(A)-Merkur(B) NE smije pogoditi.
    assert find_cross_conjunction([c], "Saturn", "Merkur") == []
    assert find_cross_conjunction([c], "Merkur", "Saturn") == [c]


def test_normal_role_multiplier_formula():
    assert role_multiplier([]) == 1.0
    assert role_multiplier(["darakaraka"]) == 1.10
    assert round(role_multiplier(["darakaraka", "7th_lord"]), 2) == 1.15
    # Gornja ograda (1.25) - čak i s puno uloga, ne smije prijeći ogradu.
    assert role_multiplier(["darakaraka", "7th_lord", "UL_lord", "atmakaraka"]) <= 1.25


def test_edge_case_combined_role_multiplier_takes_stronger_side():
    role_map = build_role_map(
        darakaraka_a="Saturn", atmakaraka_a="Sunce", seventh_lord_a="Saturn",  # Saturn(A): 2 uloge
        darakaraka_b="Merkur", atmakaraka_b="Merkur", seventh_lord_b="Mjesec",  # Merkur(B): 1 uloga (dedup unutar add_role)
    )
    multiplier = combined_role_multiplier(role_map, "A", "Saturn", "B", "Merkur")
    # Saturn(A) nosi 2 uloge (darakaraka + 7th_lord) -> 1.15, jače od Merkur(B) (1 uloga -> 1.10)
    assert round(multiplier, 2) == 1.15


def test_normal_dedup_test_a_b_identity_never_crossed_for_all_cross_pairs():
    """Generički test: build_role_map nikad ne miješa ulogu osobe A s planetom osobe B i obrnuto."""
    role_map = build_role_map(
        darakaraka_a="Saturn", atmakaraka_a="Sunce", seventh_lord_a="Mars",
        darakaraka_b="Merkur", atmakaraka_b="Venera", seventh_lord_b="Mjesec",
    )
    assert role_map.roles_for("A", "Saturn") == ["darakaraka"]
    assert role_map.roles_for("B", "Saturn") == []   # Saturn nije ulogovan kod B u ovom primjeru
    assert role_map.roles_for("A", "Merkur") == []   # Merkur je uloga osobe B, ne A


def test_normal_confirmation_strength_scales_are_bounded():
    full = GrahaDrishtiContact(
        source_person="A", target_person="B", from_planet="Venera", to_planet="Mars",
        house_distance=7, strength=1.0, strength_label="puni (100%)",
        from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
    )
    quarter = GrahaDrishtiContact(
        source_person="A", target_person="B", from_planet="Venera", to_planet="Mars",
        house_distance=3, strength=0.25, strength_label="1/4 (25%)",
        from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
    )
    assert drishti_confirmation_strength(full) == 1.0
    assert drishti_confirmation_strength(quarter) < drishti_confirmation_strength(full)

    exact_conj = ConjunctionContact(
        person_a_object="Venera", person_b_object="Mars", longitude_a=10.0, longitude_b=10.5,
        sign="Ovan", degree_distance=0.5, orb_used=6.0, is_exact=True,
        same_nakshatra=False, same_pada=False, special_flags=[],
    )
    wide_conj = ConjunctionContact(
        person_a_object="Venera", person_b_object="Mars", longitude_a=10.0, longitude_b=15.0,
        sign="Ovan", degree_distance=5.0, orb_used=6.0, is_exact=False,
        same_nakshatra=False, same_pada=False, special_flags=[],
    )
    assert conjunction_confirmation_strength(exact_conj) > conjunction_confirmation_strength(wide_conj)
