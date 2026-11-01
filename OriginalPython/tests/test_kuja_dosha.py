from core.synastry.config import SynastryConfig
from core.synastry.kuja_dosha import assess_kuja_dosha, compare_kuja_dosha
from tests.conftest import make_natal_context


def test_normal_no_affliction_when_mars_outside_dosha_houses():
    # Ascendent 0 (Ovan). Mjesec/Venera ostaju na zadanoj (65°, Blizanci).
    # Mars na 125° (Lav): 5. kuca od Ascendenta, 3. kuca od Mjeseca/Venere -
    # obje IZVAN {1,2,4,7,8,12}.
    ctx = make_natal_context(ascendant_longitude=0.0, planet_longitudes={"Mars": 125.0})
    config = SynastryConfig()
    result = assess_kuja_dosha(ctx, "A", config)
    assert result.severity == "nema"
    assert result.afflicted_from == []


def test_edge_case_mars_in_first_house_from_all_three_bases():
    """Mars u 1. kući gledano od Ascendenta, Mjeseca I Venere - 'jaka' dosha."""
    ctx = make_natal_context(ascendant_longitude=0.0, planet_longitudes={
        "Mars": 5.0, "Mjesec": 2.0, "Venera": 8.0,
    })
    config = SynastryConfig()
    result = assess_kuja_dosha(ctx, "A", config)
    assert result.severity == "jaka"
    assert set(result.afflicted_from) == {"Ascendent", "Mjesec", "Venera"}
    assert result.severity_score == 100.0


def test_negative_case_mars_in_own_sign_is_flagged_as_cancellation():
    """Mars u Ovnu (vlastiti znak) I u 1. kući od Ascendenta - treba prijaviti poništenje."""
    ctx = make_natal_context(ascendant_longitude=0.0, planet_longitudes={"Mars": 10.0})
    config = SynastryConfig()
    result = assess_kuja_dosha(ctx, "A", config)
    assert result.severity != "nema"
    assert any("vlastitoj karti" in c for c in result.possible_cancellations)


def test_configurable_houses_narrower_school():
    """Uža škola (samo 4 kuće: 2,4,7,8) - Mars u 1. kući NE smije se računati."""
    ctx = make_natal_context(ascendant_longitude=0.0, planet_longitudes={"Mars": 5.0})
    config = SynastryConfig(kuja_dosha_houses=frozenset({2, 4, 7, 8}))
    result = assess_kuja_dosha(ctx, "A", config)
    assert result.severity == "nema"


def test_mutual_balancing_when_both_afflicted():
    ctx_a = make_natal_context(ascendant_longitude=0.0, planet_longitudes={"Mars": 5.0})
    ctx_b = make_natal_context(ascendant_longitude=90.0, planet_longitudes={"Mars": 95.0})
    config = SynastryConfig()
    comparison = compare_kuja_dosha(ctx_a, ctx_b, config)
    assert comparison.person_a.severity != "nema"
    assert comparison.person_b.severity != "nema"
    assert comparison.mutual_balancing is True


def test_no_mutual_balancing_when_only_one_afflicted():
    ctx_a = make_natal_context(ascendant_longitude=0.0, planet_longitudes={"Mars": 5.0})
    ctx_b = make_natal_context(ascendant_longitude=0.0, planet_longitudes={"Mars": 125.0})
    config = SynastryConfig()
    comparison = compare_kuja_dosha(ctx_a, ctx_b, config)
    assert comparison.person_b.severity == "nema"
    assert comparison.mutual_balancing is False
    assert comparison.balancing_fraction == 0.0


def test_asymmetric_mutual_affliction_is_only_partially_balanced():
    """
    Regresijski test (spec 12): oboje imaju Kuja Doshu, ALI intenzitet NIJE
    jednak (A: "blaga" - samo Ascendent, B: "jaka" - sve tri osnove) -
    balancing_fraction mora ostati DJELOMIČAN (min/max severity), ne 1.0
    (potpuno uravnoteženje) samo zato što obje osobe imaju BILO KAKVU dosha.
    """
    ctx_a = make_natal_context(ascendant_longitude=0.0, planet_longitudes={"Mars": 5.0})  # samo Ascendent (blaga)
    ctx_b = make_natal_context(ascendant_longitude=0.0, planet_longitudes={
        "Mars": 5.0, "Mjesec": 2.0, "Venera": 8.0,
    })  # sve tri osnove (jaka)
    config = SynastryConfig()
    comparison = compare_kuja_dosha(ctx_a, ctx_b, config)
    assert comparison.person_a.severity == "blaga"
    assert comparison.person_b.severity == "jaka"
    assert comparison.mutual_balancing is True
    assert 0.0 < comparison.balancing_fraction < 0.9
    assert "NIJE jednak" in comparison.balancing_note or "DJELOMIČNO" in comparison.balancing_note
