from core.synastry.ashtakoota import (
    compute_ashtakoota, compute_varna_koota, compute_vashya_koota, compute_tara_koota,
    compute_yoni_koota, compute_graha_maitri_koota, compute_gana_koota, compute_bhakoot_koota,
    compute_nadi_koota,
)


def test_normal_full_ashtakoota_total_is_36_max():
    result = compute_ashtakoota(moon_longitude_a=45.0, moon_longitude_b=200.0)
    assert result.max_points == 36.0
    assert 0.0 <= result.total_points <= 36.0
    assert len(result.kutas) == 8
    assert {k.max_points for k in result.kutas} == {1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0}


def test_varna_koota_a_higher_or_equal_scores_full():
    # Rak (Brahmin, rang 4) vs Blizanci (Shudra, rang 1) - A ima visi rang
    kuta = compute_varna_koota("Rak", "Blizanci")
    assert kuta.points == 1.0


def test_varna_koota_a_lower_scores_zero():
    kuta = compute_varna_koota("Blizanci", "Rak")
    assert kuta.points == 0.0


def test_varna_koota_same_sign_always_full():
    kuta = compute_varna_koota("Lav", "Lav")
    assert kuta.points == 1.0


def test_vashya_koota_same_group_full_points():
    kuta = compute_vashya_koota("Ovan", "Bik")  # oba Chatushpada
    assert kuta.points == 2.0


def test_vashya_koota_different_unlisted_group_zero():
    kuta = compute_vashya_koota("Rak", "Lav")  # Jalachara vs Vanachara - nije u partial listi
    assert kuta.points == 0.0


def test_tara_koota_same_nakshatra_is_good_both_directions():
    """Ista nakshatra (index 0 oba) - Tara 1 (Janma) u oba smjera, NIJE u lošem skupu {3,5,7}."""
    kuta = compute_tara_koota(0, 0)
    assert kuta.points == 3.0


def test_tara_koota_bad_combination_scores_less():
    # udaljenost 3 nakšatre (index 0 -> 2): count=3 -> Vipat (loše)
    kuta = compute_tara_koota(0, 2)
    assert kuta.points < 3.0


def test_yoni_koota_same_animal_full_points():
    # Ashwini(0) i Shatabhisha(23) su oboje "Konj"
    kuta = compute_yoni_koota(0, 23)
    assert kuta.points == 4.0


def test_yoni_koota_enemy_pair_zero_points():
    # Ashwini(0)=Konj, Hasta(12)=Bivol - poznati neprijateljski par
    kuta = compute_yoni_koota(0, 12)
    assert kuta.points == 0.0


def test_yoni_koota_neutral_pair_partial_points():
    # Ashwini(0)=Konj, Bharani(1)=Slon - nije ni isto ni neprijateljsko
    kuta = compute_yoni_koota(0, 1)
    assert kuta.points == 2.0


def test_graha_maitri_same_lord_full_points():
    kuta = compute_graha_maitri_koota("Ovan", "Škorpion")  # oba Mars
    assert kuta.points == 5.0


def test_graha_maitri_mutual_enemies_zero():
    # Sunce (Lav) i Saturn (Jarac/Vodenjak) su prirodni neprijatelji u oba smjera
    kuta = compute_graha_maitri_koota("Lav", "Jarac")
    assert kuta.points == 0.0


def test_gana_koota_same_gana_full():
    kuta = compute_gana_koota(0, 4)  # Ashwini (Deva) i Mrigashira (Deva)
    assert kuta.points == 6.0


def test_gana_koota_deva_rakshasa_worst():
    kuta = compute_gana_koota(0, 2)  # Ashwini (Deva) i Krittika (Rakshasa)
    assert kuta.points == 0.0


def test_bhakoot_koota_bad_6_8_combination():
    kuta, bad = compute_bhakoot_koota("Ovan", "Djevica")  # Djevica je 6. znak od Ovna
    assert bad is True
    assert kuta.points == 0.0


def test_bhakoot_koota_good_combination():
    # Vaga je 7. znak od Ovna (opozicija) - k=6, NIJE u lošem skupu {1,4,5,7,8,11}
    kuta, bad = compute_bhakoot_koota("Ovan", "Vaga")
    assert bad is False
    assert kuta.points == 7.0


def test_bhakoot_koota_same_sign_is_fine():
    kuta, bad = compute_bhakoot_koota("Ovan", "Ovan")
    assert bad is False
    assert kuta.points == 7.0


def test_nadi_koota_same_nadi_zero():
    # Ashwini(0) i Ardra(5) su oboje Vata (vidi core.constants.NAKSHATRA_NADI)
    kuta, same = compute_nadi_koota(0, 5)
    assert same is True
    assert kuta.points == 0.0


def test_nadi_koota_different_nadi_full():
    # Ashwini(0)=Vata, Bharani(1)=Pitta
    kuta, same = compute_nadi_koota(0, 1)
    assert same is False
    assert kuta.points == 8.0


def test_bhakoot_dosha_present_without_cancellation_when_different_lords():
    """Ovan (Mars) i Djevica (Merkur) - 6/8 kombinacija (k=5, bad), RAZLIČITI vladari -> dosha ostaje."""
    result = compute_ashtakoota(moon_longitude_a=5.0, moon_longitude_b=155.0)  # Ovan i Djevica
    bhakoot = next(k for k in result.kutas if k.name == "Bhakoot (Rashi)")
    assert bhakoot.points == 0.0
    assert any("PRISUTNA" in c for c in result.cancellations)


def test_bhakoot_dosha_cancelled_when_same_lord():
    """Ovan i Škorpion oboje vladani Marsom, a udaljenost (8. znak, k=7) je bad par -> dosha poništena."""
    result = compute_ashtakoota(moon_longitude_a=5.0, moon_longitude_b=215.0)  # Ovan i Škorpion
    bhakoot = next(k for k in result.kutas if k.name == "Bhakoot (Rashi)")
    assert bhakoot.points == 7.0
    assert any("poništena" in c for c in result.cancellations)


def test_nadi_dosha_cancelled_when_exact_same_nakshatra():
    """Oba Mjeseca u ISTOJ nakšatri (Ashwini) - Nadi Dosha tradicionalno poništena."""
    result = compute_ashtakoota(moon_longitude_a=2.0, moon_longitude_b=10.0)  # oboje unutar Ashwini (0-13.33)
    nadi = next(k for k in result.kutas if k.name == "Nadi")
    assert nadi.points == 8.0
    assert any("poništena" in c for c in result.cancellations)
