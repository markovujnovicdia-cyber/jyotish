from core.synastry.config import SynastryConfig
from core.synastry.conjunctions import find_conjunctions


def test_normal_conjunction_within_orb():
    """Venera (A) i Mars (B) 3° razmaknuti, unutar orba (6°) - normalan slučaj."""
    config = SynastryConfig()
    a_points = {"Venera": 100.0}
    b_points = {"Mars": 103.0}
    results = find_conjunctions(a_points, b_points, config)
    assert len(results) == 1
    c = results[0]
    assert c.person_a_object == "Venera"
    assert c.person_b_object == "Mars"
    assert abs(c.degree_distance - 3.0) < 1e-9
    assert not c.is_exact


def test_edge_case_conjunction_crosses_sign_boundary():
    """
    29.5° Ovna (=29.5) naspram 0.5° Bika (=30.5) - samo 1° razmaka, ali
    RAZLIČITI znakovi. Mora se prepoznati kao (skoro egzaktna) konjunkcija
    jer se koristi apsolutna dužina, ne indeks znaka.
    """
    config = SynastryConfig()
    a_points = {"Sunce": 29.5}
    b_points = {"Mjesec": 30.5}
    results = find_conjunctions(a_points, b_points, config)
    assert len(results) == 1
    c = results[0]
    assert abs(c.degree_distance - 1.0) < 1e-9
    assert c.is_exact
    assert "/" in c.sign  # različiti znakovi su prikazani kao "Ovan / Bik"


def test_edge_case_conjunction_crosses_360_boundary():
    """359° naspram 2° (preko 0°/360° granice) = 3° razmaka."""
    config = SynastryConfig()
    a_points = {"Saturn": 359.0}
    b_points = {"Jupiter": 2.0}
    results = find_conjunctions(a_points, b_points, config)
    assert len(results) == 1
    assert abs(results[0].degree_distance - 3.0) < 1e-9


def test_negative_case_outside_orb():
    """Rahu/Ketu imaju uži orb (4°) - 5° razmaka NE smije dati konjunkciju."""
    config = SynastryConfig()
    a_points = {"Rahu": 10.0}
    b_points = {"Mjesec": 15.0}
    results = find_conjunctions(a_points, b_points, config)
    assert results == []


def test_orb_uses_stricter_of_the_two_planets():
    """Sunce ima orb 8°, Rahu ima orb 4° - par mora koristiti UŽI (4°)."""
    config = SynastryConfig()
    a_points = {"Sunce": 0.0}
    b_points = {"Rahu": 5.0}
    results = find_conjunctions(a_points, b_points, config)
    assert results == []  # 5° > min(8, 4) = 4°

    b_points_close = {"Rahu": 3.5}
    results_close = find_conjunctions(a_points, b_points_close, config)
    assert len(results_close) == 1


def test_special_flags_detects_node_and_saturn():
    config = SynastryConfig()
    a_points = {"Ketu": 200.0}
    b_points = {"Saturn": 201.0}
    results = find_conjunctions(a_points, b_points, config)
    assert len(results) == 1
    assert "Rahu/Ketu" in results[0].special_flags
    assert "Saturn" in results[0].special_flags


def test_special_flags_detects_seventh_lord_and_upapada():
    config = SynastryConfig()
    a_points = {"Merkur": 50.0, "UL": 51.0}
    b_points = {"A7": 50.5}
    results = find_conjunctions(a_points, b_points, config, seventh_lord_a="Merkur")
    by_pair = {(c.person_a_object, c.person_b_object): c for c in results}
    assert "vladar 7. kuće (A)" in by_pair[("Merkur", "A7")].special_flags
    assert "Upapada Lagna (UL)" in by_pair[("UL", "A7")].special_flags
    assert "Darapada (A7)" in by_pair[("UL", "A7")].special_flags


def test_same_nakshatra_and_pada_flags():
    """Dva stupnja unutar iste nakšatre I iste pade (Ashwini je 0-13.333, pada 1 je 0-3.333)."""
    config = SynastryConfig()
    a_points = {"Mjesec": 1.0}
    b_points = {"Venera": 1.5}
    results = find_conjunctions(a_points, b_points, config)
    assert len(results) == 1
    assert results[0].same_nakshatra is True
    assert results[0].same_pada is True
