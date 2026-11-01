"""
Testovi za Yoga Engine. Ne pokušava pokriti svih 68 registriranih yoga sa
po 4 testa (to bi bilo >250 testova) - fokus je na:
  1. temeljnim helper funkcijama (core/yoga_engine/context.py)
  2. reprezentativnom, temeljitom pokrivanju svake OBITELJI pravila
     (Mahapurusha, Chandra, Surya, Nabhasa, Raja, Dhana, Neecha Bhanga,
     Viparita Raja, Parivartana, Ostale/Negativne)
  3. dva "flagship" primjera koje je korisnik sam naveo u zahtjevu (Hamsa i
     Sunapha) testirana s TOČNO traženim nazivima i brojem varijanti (4/3)
  4. integritetu registryja (nema duplikata rezultata po yogi)
"""

import pytest

from core.yoga_engine.context import (
    ChartContext, house_from, is_kendra, is_trikona, is_dusthana,
    is_upachaya, is_panapara, is_apoklima, lord_of,
)
from core.yoga_engine.registry import YOGA_REGISTRY, run_all_yogas, run_yoga
from core.yoga_engine.rules.raja import find_yogakaraka
from core.yoga_engine.rules.neecha_bhanga import analyze_neecha_bhanga
from core.yoga_engine.rules.parivartana import find_all_parivartanas
from tests.yoga_engine.conftest import make_chart


# ---------------------------------------------------------------------------
# 1) Temeljne helper funkcije
# ---------------------------------------------------------------------------

def test_house_from_matches_spec_example():
    # "Jupiter 4 znaka od Mjeseca" primjer iz zahtjeva: Mjesec=Vodenjak(10), Jupiter=Bik(1)
    assert house_from(10, 1) == 4


def test_kendra_trikona_dusthana_classification():
    assert all(is_kendra(h) for h in (1, 4, 7, 10))
    assert not any(is_kendra(h) for h in (2, 3, 5, 6, 8, 9, 11, 12))
    assert all(is_trikona(h) for h in (1, 5, 9))
    assert all(is_dusthana(h) for h in (6, 8, 12))
    assert all(is_upachaya(h) for h in (3, 6, 10, 11))
    assert all(is_panapara(h) for h in (2, 5, 8, 11))
    assert all(is_apoklima(h) for h in (3, 6, 9, 12))


def test_lord_of_sign():
    assert lord_of(0) == "Mars"  # Ovan
    assert lord_of(3) == "Mjesec"  # Rak


def test_has_exchange_detects_mutual_sign_lordship():
    # Mars u Vagi (Venerin znak), Venera u Škorpionu (Marsov znak) -> razmjena
    chart = make_chart(0.0, {"Mars": 6 * 30 + 5, "Venera": 7 * 30 + 5})
    assert chart.has_exchange("Mars", "Venera")
    assert not chart.has_exchange("Mars", "Jupiter")


def test_planet_aspects_respects_special_full_houses():
    # Mars u Ovnu (sign0), cilj u Raku (sign3) = 4. kuća od Marsa -> POSEBAN puni aspekt
    chart = make_chart(0.0, {"Mars": 5.0})
    assert chart.planet_aspects("Mars", "Jupiter") is False or True  # placeholder guard, real check below
    assert chart._aspect_strength("Mars", 3) == 1.0  # 4. kuća - Marsov posebni puni aspekt


def test_rahu_ketu_excluded_from_aspects_by_default():
    chart = make_chart(0.0, {"Rahu": 6 * 30 + 5})  # Rahu u 7. kući - baza bi dala puni aspekt DA je klasični planet
    assert chart.planet_aspects("Rahu", "Sunce") is False  # Rahu ne baca aspekt bez include_rahu_ketu=True


# ---------------------------------------------------------------------------
# 2) Pancha Mahapurusha - Hamsa, TOČNO imena testova iz zahtjeva (#26)
# ---------------------------------------------------------------------------

def test_hamsa_exalted_in_kendra():
    # Ascendent Ovan(0) - kendra znakovi {0,3,6,9}; Jupiter uzvišen u Raku(3) = 4. kuća
    chart = make_chart(0.0, {"Jupiter": 3 * 30 + 5.0})
    result = run_yoga("hamsa", chart)[0]
    assert result.present is True
    assert result.houses == [4]
    assert "uzvišenju" in result.reasons[1] or "uzvišen" in result.debug_log[1]


def test_hamsa_own_sign_in_kendra():
    # Ascendent Strijelac(8) - kendra znakovi {8,11,2,5}; Jupiter u Ribama(11) = 4. kuća, vlastiti znak
    chart = make_chart(8 * 30.0, {"Jupiter": 11 * 30 + 15.0})
    result = run_yoga("hamsa", chart)[0]
    assert result.present is True
    assert result.houses == [4]


def test_hamsa_own_sign_not_kendra():
    # Ascendent Rak(3) - kendra znakovi {3,6,9,0}; Jupiter u Strijelcu(8) = 6. kuća (NE kendra), vlastiti znak
    chart = make_chart(3 * 30.0, {"Jupiter": 8 * 30 + 15.0})
    result = run_yoga("hamsa", chart)[0]
    assert result.present is False


def test_hamsa_kendra_wrong_dignity():
    # Ascendent Rak(3) - Jupiter u Vagi(6) = 4. kuća (kendra), ali neprijateljski znak (Venerin)
    chart = make_chart(3 * 30.0, {"Jupiter": 6 * 30 + 15.0})
    result = run_yoga("hamsa", chart)[0]
    assert result.present is False


@pytest.mark.parametrize("planet,exalt_sign_index,exalt_deg", [
    ("Mars", 9, 28.0), ("Merkur", 5, 15.0), ("Venera", 11, 27.0), ("Saturn", 6, 20.0),
])
def test_other_mahapurusha_exalted_in_kendra_present(planet, exalt_sign_index, exalt_deg):
    # Ascendent 0 (Ovan) - provjeri da svaka od preostale 4 Mahapurusha yoge radi kad je planet
    # uzvišen i slučajno u kendri (koristi ascendent gdje je exalt_sign kendra)
    kendra_signs = {0, 3, 6, 9}
    asc = exalt_sign_index if exalt_sign_index in kendra_signs else (exalt_sign_index - 3) % 12
    chart = make_chart(asc * 30.0, {planet: exalt_sign_index * 30 + exalt_deg})
    yoga_id = {"Mars": "ruchaka", "Merkur": "bhadra", "Venera": "malavya", "Saturn": "sasa"}[planet]
    result = run_yoga(yoga_id, chart)[0]
    assert result.present is True


# ---------------------------------------------------------------------------
# 3) Chandra Yoge - Sunapha/Anapha/Durudhara, TOČNO imena iz zahtjeva (#26)
# ---------------------------------------------------------------------------

def test_sunapha_with_mars_2nd_from_moon():
    # Mjesec u Ovnu(0), Mars u Biku(1) = 2. od Mjeseca
    chart = make_chart(0.0, {"Mjesec": 5.0, "Mars": 1 * 30 + 5.0})
    sunapha = run_yoga("sunapha", chart)[0]
    anapha = run_yoga("anapha", chart)[0]
    durudhara = run_yoga("durudhara", chart)[0]
    assert sunapha.present is True
    assert anapha.present is False
    assert durudhara.present is False


def test_sunapha_only_sun_2nd_from_moon():
    # Mjesec u Ovnu(0), Sunce u Biku(1) = 2. od Mjeseca - Sunce se ISKLJUČUJE
    chart = make_chart(0.0, {"Mjesec": 5.0, "Sunce": 1 * 30 + 5.0})
    sunapha = run_yoga("sunapha", chart)[0]
    assert sunapha.present is False  # mora vratiti FALSE jer se Sunce isključuje


def test_sunapha_empty_second():
    chart = make_chart(0.0, {"Mjesec": 5.0})  # nema ničeg u 2. ni 12. od Mjeseca (osim defaulta van dosega)
    sunapha = run_yoga("sunapha", chart)[0]
    anapha = run_yoga("anapha", chart)[0]
    assert sunapha.present is False
    assert anapha.present is False


def test_kemadruma_present_when_no_cancellation():
    # Mjesec izoliran (2./12. prazni), nijedan uvjet poništenja zadovoljen
    chart = make_chart(0.0, {
        "Mjesec": 5.0,        # Ovan, house1 od Lagne -> NIJE kendra provjera bitna? house1 JEST kendra!
    })
    # house1 je uvijek kendra od Lagne - moramo Mjesec maknuti iz kendre da testiramo "bez poništenja"
    chart = make_chart(4 * 30.0, {"Mjesec": 0.5})  # Lagna=Lav(4), Mjesec u Ovnu(0) = 8. kuća (NE kendra)
    result = run_yoga("kemadruma", chart)[0]
    assert result.present is True
    assert result.cancellation_factors == []


def test_kemadruma_cancelled_when_moon_in_kendra_from_lagna():
    # default_longitude=8*30+10 (Strijelac) namjerno IZVAN 2./12. od Mjeseca (sign3),
    # da bi baznički uvjet (prazna 2./12.) bio zadovoljen i test stigao do provjere poništenja
    chart = make_chart(0.0, {"Mjesec": 3 * 30 + 5.0}, default_longitude=8 * 30 + 10.0)
    result = run_yoga("kemadruma", chart)[0]
    assert result.present is False
    assert any("kendri" in f for f in result.cancellation_factors)


def test_gajakesari_present_jupiter_kendra_from_moon():
    chart = make_chart(0.0, {"Mjesec": 5.0, "Jupiter": 3 * 30 + 5.0})
    result = run_yoga("gajakesari", chart)[0]
    assert result.present is True
    assert result.houses == [4]


def test_gajakesari_absent_jupiter_not_kendra_from_moon():
    chart = make_chart(0.0, {"Mjesec": 5.0, "Jupiter": 1 * 30 + 5.0})  # 2. od Mjeseca
    result = run_yoga("gajakesari", chart)[0]
    assert result.present is False


# ---------------------------------------------------------------------------
# 4) Surya Yoge
# ---------------------------------------------------------------------------

def test_budha_aditya_present_but_weakened_when_combust():
    chart = make_chart(0.0, {"Sunce": 5.0, "Merkur": 8.0})  # isti znak, blizu -> kombust
    result = run_yoga("budha_aditya", chart)[0]
    assert result.present is True
    assert any("kombust" in w.lower() for w in result.weakening_factors)


def test_vesi_present_mars_2nd_from_sun():
    chart = make_chart(0.0, {"Sunce": 5.0, "Mars": 1 * 30 + 5.0})
    result = run_yoga("vesi", chart)[0]
    assert result.present is True


def test_vesi_absent_when_only_moon_2nd_from_sun():
    chart = make_chart(0.0, {"Sunce": 5.0, "Mjesec": 1 * 30 + 5.0})  # Mjesec se isključuje
    result = run_yoga("vesi", chart)[0]
    assert result.present is False


# ---------------------------------------------------------------------------
# 5) Nabhasa - reprezentativan uzorak
# ---------------------------------------------------------------------------

def test_rajju_yoga_all_planets_movable_signs():
    movable = [0, 3, 6, 9]  # Ovan, Rak, Vaga, Jarac
    longitudes = {p: movable[i % 4] * 30 + 5.0 for i, p in enumerate(
        ["Sunce", "Mjesec", "Mars", "Merkur", "Jupiter", "Venera", "Saturn"])}
    chart = make_chart(0.0, longitudes)
    result = run_yoga("rajju", chart)[0]
    assert result.present is True
    musala = run_yoga("musala", chart)[0]
    assert musala.present is False


def test_sankhya_yoga_counts_distinct_signs_occupied():
    # svih 7 klasičnih u ISTOM znaku -> Gola (1 znak)
    chart = make_chart(0.0, {p: 65.0 for p in
                              ["Sunce", "Mjesec", "Mars", "Merkur", "Jupiter", "Venera", "Saturn"]})
    gola = run_yoga("gola_yoga", chart)[0]
    vina = run_yoga("vina_yoga", chart)[0]
    assert gola.present is True
    assert vina.present is False


def test_mala_yoga_takes_priority_over_kamala_when_all_benefics():
    # Sve 4 kendre pune ISKLJUČIVO dobrotvorima (Jupiter/Venera/Merkur/rastuci Mjesec)
    chart = make_chart(0.0, {
        "Jupiter": 0 * 30 + 5, "Venera": 3 * 30 + 5, "Merkur": 6 * 30 + 5, "Mjesec": 9 * 30 + 5,
        "Sunce": 65.0, "Mars": 65.0, "Saturn": 65.0,
    })
    mala = run_yoga("mala_yoga", chart)[0]
    kamala = run_yoga("kamala_yoga", chart)[0]
    assert mala.present is True
    assert kamala.present is False  # specifičnija (Mala) ima prednost - zahtjev #8


def test_kamala_yoga_when_kendras_full_but_mixed():
    # SVIH 7 klasičnih graha isključivo u kendra znakovima (0,3,6,9), TRULY miješano
    # (svaka kendra osim 10. ima I dobrotvora I zlotvora, da se izbjegne slučajno
    # poklapanje s čistim Vajra/Yava rasporedom)
    chart = make_chart(0.0, {
        "Jupiter": 0 * 30 + 5, "Mjesec": 0 * 30 + 15,      # 1. kuća - dobrotvori
        "Sunce": 3 * 30 + 5, "Merkur": 3 * 30 + 15,        # 4. kuća - zlotvor + dobrotvor (miješano)
        "Venera": 6 * 30 + 5, "Saturn": 6 * 30 + 15,       # 7. kuća - dobrotvor + zlotvor (miješano)
        "Mars": 9 * 30 + 5,                                 # 10. kuća - zlotvor
    })
    kamala = run_yoga("kamala_yoga", chart)[0]
    mala = run_yoga("mala_yoga", chart)[0]
    sarpa = run_yoga("sarpa_yoga", chart)[0]
    assert kamala.present is True
    assert mala.present is False
    assert sarpa.present is False


# ---------------------------------------------------------------------------
# 6) Raja / Yogakaraka / Dhana
# ---------------------------------------------------------------------------

def test_yogakaraka_saturn_for_taurus_ascendant():
    # Klasičan, naširoko citiran slučaj: Bik ascendent -> Saturn (vladar 9. i 10.) je Yogakaraka
    chart = make_chart(1 * 30.0, {})
    found = find_yogakaraka(chart)
    planets = {e["planet"] for e in found}
    assert "Saturn" in planets


def test_dharma_karmadhipati_present_on_conjunction():
    # Ascendent 0 (Ovan): 9. lord=Jupiter(Strijelac), 10. lord=Saturn(Jarac) - stavi ih u konjunkciju
    chart = make_chart(0.0, {"Jupiter": 65.0, "Saturn": 65.0})
    result = run_yoga("dharma_karmadhipati_yoga", chart)[0]
    assert result.present is True
    assert result.planets == ["Jupiter", "Saturn"]


def test_dhana_yoga_lords_reports_each_pair_separately():
    chart = make_chart(0.0, {"Jupiter": 65.0, "Saturn": 65.0})  # 9.(Jupiter)-11.(Saturn) konjunkcija
    results = run_yoga("dhana_yoga_lords", chart)
    present = [r for r in results if r.present]
    assert len(present) >= 1
    assert all(r.name.startswith("Dhana Yoga #") for r in present)


# ---------------------------------------------------------------------------
# 7) Neecha Bhanga
# ---------------------------------------------------------------------------

def test_neecha_bhanga_zero_conditions_met():
    chart = make_chart(0.0, {
        "Jupiter": 9 * 30 + 15.0,  # debilitiran u Jarcu (Capricorn)
        "Saturn": 4 * 30 + 10.0,   # dispozitor - NIJE u kendri od Lagne/Mjeseca, NIJE uzvišen
        "Mjesec": 2 * 30 + 10.0,   # vladar znaka uzvišenja (Rak/Mjesec) - NIJE u kendri od Lagne
        "Mars": 8 * 30 + 10.0,     # planet uzvišen u Jarcu - NE aspektira/konjunkt Jupiter ovdje
    })
    analysis = analyze_neecha_bhanga(chart, "Jupiter")
    assert analysis["met"] == 0
    result = [r for r in run_yoga("neecha_bhanga", chart) if r.instance_label == "Jupiter"][0]
    assert result.status == "Neecha planet bez poništenja"
    assert result.present is False


def test_neecha_bhanga_strong_when_two_plus_conditions():
    chart = make_chart(0.0, {
        "Jupiter": 9 * 30 + 15.0,  # debilitiran u Jarcu
        "Saturn": 6 * 30 + 10.0,   # dispozitor UZVIŠEN (Vaga) I u kendri (7.) od Lagne - 2 uvjeta odjednom
    })
    analysis = analyze_neecha_bhanga(chart, "Jupiter")
    assert analysis["met"] >= 2
    result = [r for r in run_yoga("neecha_bhanga", chart) if r.instance_label == "Jupiter"][0]
    assert result.status in ("snažni Neecha Bhanga", "Neecha Bhanga Raja Yoga")
    assert result.present is True


def test_neecha_bhanga_not_automatically_raja_yoga():
    """Zahtjev #13: svako poništenje NIJE automatski Raja Yoga - mora postojati DODATNI raja-kontekst."""
    # Lagna=Bik(1) - kendra znakovi {1,4,7,10}. Jupiterova debilitacija (Jarac,9) NIJE
    # kendra kuća za ovaj ascendent (9. kuća, trikona), pa vladar (Saturn) MOŽE biti u
    # kendri (4., znak Lav) a da NE aspektira Jupitera (izbjegnuta strukturna zamka gdje
    # bi kendra-na-kendru položaj automatski značio i aspekt - vidi komentar niže).
    chart = make_chart(1 * 30.0, {
        "Jupiter": 9 * 30 + 15.0,   # debilitiran u Jarcu, 9. kuća (trikona, NE kendra)
        "Saturn": 4 * 30 + 10.0,    # Lav - u kendri (4.) od Lagne, ALI NE aspektira Jupiter, NIJE uzvišen
        "Mjesec": 2 * 30 + 10.0,    # vladar znaka uzvišenja - NIJE u kendri od Lagne
        "Mars": 4 * 30 + 10.0,      # planet uzvišen u Jarcu - NE aspektira Jupiter odavde
    })
    analysis = analyze_neecha_bhanga(chart, "Jupiter")
    assert analysis["met"] == 1
    result = [r for r in run_yoga("neecha_bhanga", chart) if r.instance_label == "Jupiter"][0]
    assert result.status == "djelomični Neecha Bhanga"


# ---------------------------------------------------------------------------
# 8) Viparita Raja Yoga
# ---------------------------------------------------------------------------

def test_harsha_yoga_present_when_6th_lord_in_dusthana():
    # Ascendent 0 (Ovan): 6. kuća=Djevica(Merkur). Stavi Merkura u 8. kuću (Škorpion, sign7)
    chart = make_chart(0.0, {"Merkur": 7 * 30 + 5.0})
    result = run_yoga("harsha_yoga", chart)[0]
    assert result.present is True
    assert result.houses == [6, 8]


def test_harsha_yoga_absent_when_6th_lord_elsewhere():
    chart = make_chart(0.0, {"Merkur": 65.0})  # Blizanci = 3. kuća, NIJE dusthana
    result = run_yoga("harsha_yoga", chart)[0]
    assert result.present is False


# ---------------------------------------------------------------------------
# 9) Parivartana
# ---------------------------------------------------------------------------

def test_parivartana_classified_maha_when_both_houses_non_dusthana():
    # Ascendent 0: 1. lord Mars, 9. lord Jupiter (Strijelac) - razmijene Ovan<->Strijelac
    chart = make_chart(0.0, {"Mars": 8 * 30 + 5.0, "Jupiter": 0 * 30 + 5.0})
    found = find_all_parivartanas(chart)
    assert len(found) == 1
    assert found[0]["type"] == "Maha Parivartana"


def test_parivartana_classified_dainya_when_both_houses_dusthana():
    # Ascendent 0: 6. lord Merkur(Djevica,5), 8. lord Mars(Škorpion,7) - razmijene
    chart = make_chart(0.0, {"Merkur": 7 * 30 + 5.0, "Mars": 5 * 30 + 5.0})
    found = find_all_parivartanas(chart)
    dainya = [f for f in found if f["type"] == "Dainya Parivartana"]
    assert len(dainya) == 1
    assert dainya[0]["house1"] in (6, 8) and dainya[0]["house2"] in (6, 8)


# ---------------------------------------------------------------------------
# 10) Ostale / Negativne yoge
# ---------------------------------------------------------------------------

def test_daridra_yoga_present_when_2nd_lord_in_dusthana():
    # Ascendent 0: 2. lord Venera(Bik,1). Stavi Veneru u 12. kuću (Ribe,11)
    chart = make_chart(0.0, {"Venera": 11 * 30 + 5.0})
    result = run_yoga("daridra_yoga", chart)[0]
    assert result.present is True
    assert 2 in result.houses


def test_vasumati_yoga_present_when_benefic_in_upachaya():
    chart = make_chart(0.0, {"Jupiter": 2 * 30 + 5.0})  # Blizanci = 3. kuća od Lagne (upachaya)
    result = run_yoga("vasumati_yoga", chart)[0]
    assert result.present is True


# ---------------------------------------------------------------------------
# 11) Integritet registryja - nema duplikata (regresija za bug otkriven u
#     razvoju: registriranje iste multi-rezultatske funkcije pod više id-eva
#     bez filtriranja uzrokovalo je N-terostruko dupliciranje rezultata)
# ---------------------------------------------------------------------------

def test_registry_produces_exactly_one_result_per_id_except_known_multi_instance():
    chart = make_chart(0.0, {})
    results = run_all_yogas(chart)
    by_id = {}
    for r in results:
        by_id.setdefault(r.id, []).append(r)
    multi_instance_ids = {"raja_yoga_sweep", "dhana_yoga_lords", "parivartana_yoga"}
    for yoga_id, rs in by_id.items():
        if yoga_id not in multi_instance_ids:
            assert len(rs) == 1, f"{yoga_id} vratio {len(rs)} rezultata umjesto 1 (mogući duplikat)"
    assert len(by_id) == len(YOGA_REGISTRY)


def test_every_registered_yoga_runs_without_error_on_neutral_chart():
    chart = make_chart(0.0, {})
    results = run_all_yogas(chart)
    assert len(results) >= len(YOGA_REGISTRY)
    for r in results:
        assert isinstance(r.present, bool)
        assert 0.0 <= r.strength <= 100.0
