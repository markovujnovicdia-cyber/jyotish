from core.chara_karaka import compute_chara_karakas, get_atmakaraka, get_darakaraka
from tests.conftest import make_planet_position


def _positions(degrees_in_sign):
    """degrees_in_sign: {planet: degree_in_sign (0-30)} - stavlja svaki u svoj vlastiti znak (indeks proizvoljan, ovdje 0)."""
    return {p: make_planet_position(30 * i + deg) for i, (p, deg) in enumerate(degrees_in_sign.items())}


def test_normal_atmakaraka_is_highest_degree():
    positions = _positions({
        "Sunce": 5.0, "Mjesec": 12.0, "Mars": 29.5, "Merkur": 2.0,
        "Jupiter": 18.0, "Venera": 7.0, "Saturn": 15.0,
    })
    result = compute_chara_karakas(positions, scheme="7_karaka")
    assert result[0].planet == "Mars"
    assert result[0].karaka_name == "Atmakaraka"
    assert result[-1].karaka_name == "Darakaraka"
    assert result[-1].planet == "Merkur"  # najniži stupanj (2.0)


def test_get_atmakaraka_and_darakaraka_helpers():
    positions = _positions({
        "Sunce": 10.0, "Mjesec": 25.0, "Mars": 1.0, "Merkur": 8.0,
        "Jupiter": 20.0, "Venera": 15.0, "Saturn": 3.0,
    })
    ak = get_atmakaraka(positions)
    dk = get_darakaraka(positions)
    assert ak.planet == "Mjesec"
    assert dk.planet == "Mars"


def test_edge_case_7_karaka_excludes_rahu_even_if_present():
    positions = _positions({
        "Sunce": 5.0, "Mjesec": 12.0, "Mars": 29.5, "Merkur": 2.0,
        "Jupiter": 18.0, "Venera": 7.0, "Saturn": 15.0, "Rahu": 29.9,
    })
    result = compute_chara_karakas(positions, scheme="7_karaka")
    assert len(result) == 7
    assert all(r.planet != "Rahu" for r in result)


def test_8_karaka_scheme_includes_rahu():
    positions = _positions({
        "Sunce": 5.0, "Mjesec": 12.0, "Mars": 20.0, "Merkur": 2.0,
        "Jupiter": 18.0, "Venera": 7.0, "Saturn": 15.0, "Rahu": 25.0,
    })
    result = compute_chara_karakas(positions, scheme="8_karaka")
    assert len(result) == 8
    # Rahu na SIROVOM stupnju 25.0 nije najviši (Mars 20.0 je viši od svih
    # OSTALIH, ali Rahuov RANGIRAJUĆI stupanj je obrnut: 30-25=5.0, dakle
    # nizak) - Mars (20.0, nitko drugi ne obrće) ostaje Atmakaraka.
    assert result[0].planet == "Mars"
    assert result[0].karaka_name == "Atmakaraka"
    assert result[-1].karaka_name == "Darakaraka"


def test_edge_case_rahu_degree_is_reversed_for_ranking():
    """
    ISPRAVAK: Rahu je uvijek retrogradan, pa se u "8_karaka" shemi za
    RANGIRANJE koristi obrnut stupanj (30 - stvarni stupanj) - Rahu na
    NISKOM sirovom stupnju (2.0) ima VISOK rangirajući stupanj (28.0) i
    treba postati Atmakaraka, unatoč tome što mu je PRIKAZANI (stvarni)
    stupanj nizak.
    """
    positions = _positions({
        "Sunce": 5.0, "Mjesec": 12.0, "Mars": 20.0, "Merkur": 2.0,
        "Jupiter": 18.0, "Venera": 7.0, "Saturn": 15.0, "Rahu": 2.0,
    })
    result = compute_chara_karakas(positions, scheme="8_karaka")
    assert result[0].planet == "Rahu"
    assert result[0].karaka_name == "Atmakaraka"
    # Prikazani stupanj ostaje STVARAN (neobrnut), samo se rang temelji na obrnutom.
    assert result[0].degree_in_sign == 2.0


def test_negative_case_ketu_never_used_as_karaka():
    positions = _positions({
        "Sunce": 5.0, "Mjesec": 12.0, "Mars": 20.0, "Merkur": 2.0,
        "Jupiter": 18.0, "Venera": 7.0, "Saturn": 15.0, "Rahu": 10.0, "Ketu": 29.99,
    })
    result_7 = compute_chara_karakas(positions, scheme="7_karaka")
    result_8 = compute_chara_karakas(positions, scheme="8_karaka")
    assert all(r.planet != "Ketu" for r in result_7)
    assert all(r.planet != "Ketu" for r in result_8)


def test_tie_break_by_speed_order():
    """Izjednačeni stupnjevi - brži planet (Mjesec) treba dobiti viši rang od sporijeg (Saturn)."""
    positions = _positions({
        "Sunce": 10.0, "Mjesec": 15.0, "Mars": 10.0, "Merkur": 10.0,
        "Jupiter": 10.0, "Venera": 10.0, "Saturn": 15.0,
    })
    # Mjesec i Saturn oboje na 15.0 - Mjesec je brži (SPEED_ORDER), treba biti prvi od njih dvoje
    result = compute_chara_karakas(positions, scheme="7_karaka")
    ranks = {r.planet: r.rank for r in result}
    assert ranks["Mjesec"] < ranks["Saturn"]
