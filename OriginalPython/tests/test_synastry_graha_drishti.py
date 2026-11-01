from core.synastry.config import SynastryConfig
from core.synastry.graha_drishti import compute_cross_chart_drishti


def _rel_map(relations):
    return {(r.from_planet, r.to_planet): r for r in relations}


def test_normal_seventh_aspect_full_strength():
    """Svih 7 klasičnih grahe baca puni aspekt na 7. kuću od sebe (BPHS)."""
    config = SynastryConfig()
    from_idx = {"Merkur": 0}   # Ovan
    to_idx = {"Lagna": 6}       # Vaga = 7. znak od Ovna
    relations = compute_cross_chart_drishti(from_idx, to_idx, config)
    assert len(relations) == 1
    r = relations[0]
    assert r.from_planet == "Merkur" and r.to_planet == "Lagna"
    assert r.house_distance == 7
    assert r.strength == 1.0


def test_mars_special_aspects_4_and_8():
    config = SynastryConfig()
    from_idx = {"Mars": 0}
    to_idx = {"P4": 3, "P8": 7}  # 4. i 8. znak od Ovna
    relations = _rel_map(compute_cross_chart_drishti(from_idx, to_idx, config))
    assert relations[("Mars", "P4")].strength == 1.0
    assert relations[("Mars", "P8")].strength == 1.0


def test_jupiter_special_aspects_5_and_9():
    config = SynastryConfig()
    from_idx = {"Jupiter": 0}
    to_idx = {"P5": 4, "P9": 8}
    relations = _rel_map(compute_cross_chart_drishti(from_idx, to_idx, config))
    assert relations[("Jupiter", "P5")].strength == 1.0
    assert relations[("Jupiter", "P9")].strength == 1.0


def test_saturn_special_aspects_3_and_10():
    config = SynastryConfig()
    from_idx = {"Saturn": 0}
    to_idx = {"P3": 2, "P10": 9}
    relations = _rel_map(compute_cross_chart_drishti(from_idx, to_idx, config))
    assert relations[("Saturn", "P3")].strength == 1.0
    assert relations[("Saturn", "P10")].strength == 1.0


def test_negative_case_no_aspect_at_distance_two():
    """Udaljenost 2 (i 6, 11, 12) - nijedan klasični planet nema aspekt tu."""
    config = SynastryConfig()
    from_idx = {"Venera": 0}
    to_idx = {"P2": 1}
    relations = compute_cross_chart_drishti(from_idx, to_idx, config)
    assert relations == []


def test_node_mode_none_gives_no_node_relations():
    config = SynastryConfig(node_aspect_mode="none")
    from_idx = {"Rahu": 0}
    to_idx = {"Lagna": 6}
    relations = compute_cross_chart_drishti(from_idx, to_idx, config)
    assert relations == []


def test_node_mode_seventh_only():
    config = SynastryConfig(node_aspect_mode="seventh_only")
    from_idx = {"Rahu": 0, "Ketu": 6}
    to_idx = {"Lagna": 6}
    relations = _rel_map(compute_cross_chart_drishti(from_idx, to_idx, config))
    assert ("Rahu", "Lagna") in relations
    assert relations[("Rahu", "Lagna")].house_distance == 7
    assert relations[("Rahu", "Lagna")].strength == 1.0
    # Ketu je na istom znaku kao Lagna (distance 1) - ne baca aspekt u ovom modu
    assert ("Ketu", "Lagna") not in relations


def test_node_mode_5_7_9():
    config = SynastryConfig(node_aspect_mode="5_7_9")
    from_idx = {"Rahu": 0}
    to_idx = {"P5": 4, "P7": 6, "P9": 8, "P4": 3}
    relations = _rel_map(compute_cross_chart_drishti(from_idx, to_idx, config))
    assert relations[("Rahu", "P5")].strength == 1.0
    assert relations[("Rahu", "P7")].strength == 1.0
    assert relations[("Rahu", "P9")].strength == 1.0
    assert ("Rahu", "P4") not in relations  # 4. NIJE u 5/7/9 modu


def test_default_node_mode_is_seventh_only():
    assert SynastryConfig().node_aspect_mode == "seventh_only"
