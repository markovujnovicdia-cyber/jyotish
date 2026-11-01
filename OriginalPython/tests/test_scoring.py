from core.synastry.conjunctions import find_conjunctions
from core.synastry.deduplication import build_role_map
from core.synastry.models import (
    AshtakootaResult, ConjunctionContact, GrahaDrishtiContact, HouseOverlayRow,
    KujaDoshaAssessment, KujaDoshaComparison, KutaScore,
    NakshatraSynastryResult, VargaSynastryResult,
)
from core.synastry.scoring import compute_synastry_scores
from core.synastry.scoring_config import BASE_SCORE, CATEGORY_NAMES, SCORE_GATE_80_MIN_LAYERS


def _empty_ashtakoota():
    """
    NAPOMENA (ISPRAVAK 2): kuta doprinos je sada CENTRIRAN oko 50% bodova
    (core.synastry.scoring_config.KUTA_NEUTRAL_FRACTION) - 0 bodova više
    NIJE "nema signala", nego stvaran, aktivan negativan (dosha) nalaz.
    Ovaj fixture postavlja SVAKU kutu na točno pola njenog maksimuma da
    ostane istinski NEUTRALAN placeholder za testove koji ne testiraju
    Ashtakootu samu (kao prije rekalibracije).
    """
    kutas = [
        KutaScore(name=n, points=m / 2.0, max_points=m, rule_used="", table_reference="", interpretation="", limitation="")
        for n, m in [
            ("Varna", 1.0), ("Vashya", 2.0), ("Tara (Dina)", 3.0), ("Yoni", 4.0),
            ("Graha Maitri", 5.0), ("Gana", 6.0), ("Bhakoot (Rashi)", 7.0), ("Nadi", 8.0),
        ]
    ]
    return AshtakootaResult(
        person_a_moon_nakshatra="Ashwini", person_b_moon_nakshatra="Bharani",
        kutas=kutas, total_points=18.0, max_points=36.0, cancellations=[],
    )


def _no_kuja_dosha():
    assessment = lambda label: KujaDoshaAssessment(
        person_label=label, houses_involved={}, afflicted_from=[], severity="nema",
        severity_score=0.0, reasons=[], possible_cancellations=[],
    )
    return KujaDoshaComparison(person_a=assessment("A"), person_b=assessment("B"), mutual_balancing=False, balancing_note="")


def _empty_nakshatra_result():
    return NakshatraSynastryResult(profiles_a={}, profiles_b={}, cross_links=[], repeated_themes=[], lord_graph_edges=[])


def test_normal_all_categories_present_at_base_score_when_no_signals():
    result = compute_synastry_scores([], [], [], _empty_ashtakoota(), _no_kuja_dosha(), _empty_nakshatra_result())
    assert set(result.categories.keys()) == set(CATEGORY_NAMES)
    for cat in CATEGORY_NAMES:
        assert result.categories[cat].score == BASE_SCORE
    assert result.not_available == ["Trenutačna prediktivna aktivacija"]


def test_venus_mars_drishti_raises_attraction_score():
    contact = GrahaDrishtiContact(
        source_person="A", target_person="B", from_planet="Venera", to_planet="Mars",
        house_distance=7, strength=1.0, strength_label="puni (100%)",
        from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
    )
    result = compute_synastry_scores([contact], [], [], _empty_ashtakoota(), _no_kuja_dosha(), _empty_nakshatra_result())
    assert result.categories["Privlačnost i kemija"].score > BASE_SCORE


def test_edge_case_dedup_prevents_triple_counting_same_pair():
    """
    Venera-Mars konjunkcija I Graha Drishti ISTOG para trebaju brojati
    samo NAJJAČI doprinos za tu kategoriju, ne zbroj oba.
    """
    drishti = GrahaDrishtiContact(
        source_person="A", target_person="B", from_planet="Venera", to_planet="Mars",
        house_distance=7, strength=1.0, strength_label="puni (100%)",
        from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
    )
    conjunction = ConjunctionContact(
        person_a_object="Venera", person_b_object="Mars", longitude_a=10.0, longitude_b=10.5,
        sign="Ovan", degree_distance=0.5, orb_used=6.0, is_exact=True,
        same_nakshatra=True, same_pada=True, special_flags=[],
    )
    result_both = compute_synastry_scores([drishti], [conjunction], [], _empty_ashtakoota(), _no_kuja_dosha(), _empty_nakshatra_result())
    result_drishti_only = compute_synastry_scores([drishti], [], [], _empty_ashtakoota(), _no_kuja_dosha(), _empty_nakshatra_result())
    result_conj_only = compute_synastry_scores([], [conjunction], [], _empty_ashtakoota(), _no_kuja_dosha(), _empty_nakshatra_result())

    score_both = result_both.categories["Privlačnost i kemija"].score
    score_drishti = result_drishti_only.categories["Privlačnost i kemija"].score
    score_conj = result_conj_only.categories["Privlačnost i kemija"].score

    # Da se brojalo oba (bez dedupa), score_both bi bio priblizno zbroj priraštaja obaju - provjeravamo da NIJE
    naive_sum_increase = (score_drishti - BASE_SCORE) + (score_conj - BASE_SCORE)
    actual_increase = score_both - BASE_SCORE
    assert actual_increase < naive_sum_increase
    assert actual_increase == max(score_drishti - BASE_SCORE, score_conj - BASE_SCORE)
    assert len(result_both.categories["Privlačnost i kemija"].excluded_duplicates) >= 1


def test_negative_case_no_signals_gives_neutral_score():
    result = compute_synastry_scores([], [], [], _empty_ashtakoota(), _no_kuja_dosha(), _empty_nakshatra_result())
    assert result.categories["Bračni potencijal"].score == BASE_SCORE
    assert result.categories["Bračni potencijal"].factors == []


def test_edge_case_real_chart_with_many_contacts_does_not_flatline_at_100(person_a, person_b):
    """
    Regresijski test za stvarni nalaz: puni cjevovod (kao u UI-u) na
    stvarnim osobama davao je TOČNO 100.0/100 za 7 od 9 kategorija dok se
    koristilo tvrdo rezanje (min/max) - karte bogate kontaktima (uobičajeno
    kod stvarnih ljudi) inače gotovo uvijek udare u strop, što čini
    rezultat neinformativnim. Zasićujuća krivulja (tanh) mora spriječiti
    to zaravnjivanje.
    """
    from core.natal import get_natal_context
    from core.chara_karaka import get_atmakaraka, get_darakaraka
    from core.synastry.overlays import compute_house_overlay
    from core.synastry.graha_drishti import build_graha_drishti_contacts
    from core.synastry.ashtakoota import compute_ashtakoota
    from core.synastry.kuja_dosha import compare_kuja_dosha
    from core.synastry.nakshatra_matching import compute_nakshatra_synastry
    from core.synastry.divisional_synastry import compute_navamsha_synastry
    from core.synastry.config import SynastryConfig

    ctx_a = get_natal_context(person_a)
    ctx_b = get_natal_context(person_b)
    config = SynastryConfig()

    overlay_a_to_b = compute_house_overlay(ctx_a, ctx_b, "A", "B")
    overlay_b_to_a = compute_house_overlay(ctx_b, ctx_a, "B", "A")
    drishti = build_graha_drishti_contacts(ctx_a, ctx_b, "A", "B", config) + \
              build_graha_drishti_contacts(ctx_b, ctx_a, "B", "A", config)
    points_a = {n: p.longitude for n, p in ctx_a.positions.items()}
    points_b = {n: p.longitude for n, p in ctx_b.positions.items()}
    conjunctions = find_conjunctions(points_a, points_b, config)

    karaka_a = {p: pos for p, pos in ctx_a.positions.items() if p != "Ketu"}
    karaka_b = {p: pos for p, pos in ctx_b.positions.items() if p != "Ketu"}
    dk_a, ak_a = get_darakaraka(karaka_a).planet, get_atmakaraka(karaka_a).planet
    dk_b, ak_b = get_darakaraka(karaka_b).planet, get_atmakaraka(karaka_b).planet

    ashtakoota = compute_ashtakoota(ctx_a.positions["Mjesec"].longitude, ctx_b.positions["Mjesec"].longitude)
    kuja = compare_kuja_dosha(ctx_a, ctx_b, config)
    nakshatra_result = compute_nakshatra_synastry(ctx_a, ctx_b, "Saturn", "Mjesec", dk_a, dk_b)
    navamsha_result = compute_navamsha_synastry(
        ctx_a, ctx_b, config, "Saturn", "Mjesec", dk_a, dk_b, ak_a, ak_b, drishti, conjunctions,
    )

    result = compute_synastry_scores(
        drishti, conjunctions, overlay_a_to_b + overlay_b_to_a, ashtakoota, kuja, nakshatra_result, navamsha_result,
    )
    flatlined = [cat for cat in CATEGORY_NAMES if result.categories[cat].score >= 99.95]
    assert flatlined == [], f"Kategorije zaravnjene na strop: {flatlined}"


def test_kuja_dosha_raises_conflict_and_lowers_marriage_when_unbalanced():
    assessment_a = KujaDoshaAssessment(
        person_label="A", houses_involved={}, afflicted_from=["Ascendent"], severity="jaka",
        severity_score=100.0, reasons=[], possible_cancellations=[],
    )
    assessment_b = KujaDoshaAssessment(
        person_label="B", houses_involved={}, afflicted_from=[], severity="nema",
        severity_score=0.0, reasons=[], possible_cancellations=[],
    )
    kuja = KujaDoshaComparison(person_a=assessment_a, person_b=assessment_b, mutual_balancing=False, balancing_note="")
    result = compute_synastry_scores([], [], [], _empty_ashtakoota(), kuja, _empty_nakshatra_result())
    assert result.categories["Konflikt i pritisak"].score > BASE_SCORE
    assert result.categories["Bračni potencijal"].score < BASE_SCORE


def test_score_bounded_between_0_and_100():
    many_contacts = [
        GrahaDrishtiContact(
            source_person="A", target_person="B", from_planet="Rahu", to_planet="Ketu",
            house_distance=7, strength=1.0, strength_label="puni (100%)",
            from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
        )
    ] * 50  # namjerno pretjerano - test granice, ne dedup ponasanja (razliciti "isti" objekti ali isti pair_key -> dedup)
    result = compute_synastry_scores(many_contacts, [], [], _empty_ashtakoota(), _no_kuja_dosha(), _empty_nakshatra_result())
    for cat in CATEGORY_NAMES:
        assert 0.0 <= result.categories[cat].score <= 100.0


def test_edge_case_dual_role_planet_counts_contact_once_with_bonus_not_twice():
    """
    Regresijski test (spec 4): Jupiter osobe A koji je ISTODOBNO Darakaraka i
    vladar 7. kuće ostaje JEDAN fizički kontakt - dodatna uloga smije
    POJAČATI (ograničen multiplikator) doprinos, ne dodati nov, neovisan bod.
    (Koristi se benefik, ne Saturn - ISPRAVAK 2 uveo je poseban, NAMJERNO
    izazovan tretman malefika na 7. osi, vidi test_seventh_house_malefic_*
    - taj signal bi ovdje kolidirao s onim što se testira.)
    """
    contact = GrahaDrishtiContact(
        source_person="A", target_person="B", from_planet="Jupiter", to_planet="Mjesec",
        house_distance=7, strength=1.0, strength_label="puni (100%)",
        from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
    )
    baseline = compute_synastry_scores([contact], [], [], _empty_ashtakoota(), _no_kuja_dosha(), _empty_nakshatra_result())

    role_map = build_role_map(
        darakaraka_a="Jupiter", atmakaraka_a="Sunce", seventh_lord_a="Jupiter",
        darakaraka_b="Mars", atmakaraka_b="Venera", seventh_lord_b="Merkur",
    )
    with_roles = compute_synastry_scores(
        [contact], [], [], _empty_ashtakoota(), _no_kuja_dosha(), _empty_nakshatra_result(),
        role_map=role_map,
    )

    # "Bračni potencijal" dobiva JEDINI doprinos od 7. Graha Drishti bonusa
    # (core.synastry.scoring_config.SEVENTH_HOUSE_ASPECT_BONUS) - Ashtakoota
    # (prazna ovdje, ali svejedno bi dodala redove) ne mapira ništa u tu
    # kategoriju, pa je čist test JEDNOG fizičkog kontakta.
    marriage_baseline = baseline.categories["Bračni potencijal"]
    marriage_with_roles = with_roles.categories["Bračni potencijal"]
    # I dalje TOČNO jedan brojan faktor za taj par (nije se udvostručio).
    assert len(marriage_with_roles.factors) == len(marriage_baseline.factors) == 1
    # No, doprinos je JAČI zbog dvostruke uloge (role_multiplier), ne identičan.
    assert marriage_with_roles.score > marriage_baseline.score


def test_edge_case_lone_partial_drishti_contributes_nothing_without_other_support():
    """
    Regresijski test (spec 5/10.6): DJELOMIČNI (1/4) Graha Drishti aspekt,
    SAM (bez ikakvog drugog nalaza u toj kategoriji), ne smije samostalno
    proizvesti bod - MAX_PARTIAL_DRISHTI_SHARE ograničava djelomične
    aspekte na udio "cjeline" koja ovdje uopće ne postoji (nema punih
    nalaza za usporedbu).
    """
    quarter_contact = GrahaDrishtiContact(
        source_person="A", target_person="B", from_planet="Venera", to_planet="Mars",
        house_distance=3, strength=0.25, strength_label="1/4 (25%)",
        from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
    )
    result = compute_synastry_scores([quarter_contact], [], [], _empty_ashtakoota(), _no_kuja_dosha(), _empty_nakshatra_result())
    assert result.categories["Privlačnost i kemija"].score == BASE_SCORE


def test_edge_case_partial_drishti_share_capped_when_combined_with_full_aspect():
    """
    Regresijski test (spec 5/10.6): kad postoji I pun I djelomičan nalaz u
    istoj kategoriji, djelomični ne smije doprinijeti više od
    MAX_PARTIAL_DRISHTI_SHARE udjela ukupnog (apsolutnog) doprinosa.
    """
    from core.synastry.scoring_config import MAX_PARTIAL_DRISHTI_SHARE

    # Oba kontakta doprinose "Emocionalna povezanost" (Mjesec je uključen u
    # obje, različiti parovi -> različiti pair_key, ne dedupliciraju se).
    full_contact = GrahaDrishtiContact(
        source_person="A", target_person="B", from_planet="Mjesec", to_planet="Mjesec",
        house_distance=7, strength=1.0, strength_label="puni (100%)",
        from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
    )
    quarter_contact = GrahaDrishtiContact(
        source_person="A", target_person="B", from_planet="Mjesec", to_planet="Sunce",
        house_distance=3, strength=0.25, strength_label="1/4 (25%)",
        from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
    )
    result = compute_synastry_scores(
        [full_contact, quarter_contact], [], [], _empty_ashtakoota(), _no_kuja_dosha(), _empty_nakshatra_result(),
    )
    factors = result.categories["Emocionalna povezanost"].factors
    full_abs = sum(abs(f.contribution) for f in factors if not f.is_partial_drishti)
    partial_abs = sum(abs(f.contribution) for f in factors if f.is_partial_drishti)
    assert partial_abs > 0  # ima doprinos (nije nula, jer sad postoji "cjelina" za usporedbu)
    assert partial_abs / (full_abs + partial_abs) <= MAX_PARTIAL_DRISHTI_SHARE + 1e-6


def test_score_gate_blocks_over_80_when_only_one_independent_layer():
    """
    Regresijski test (spec 10.7): puno RAZLIČITIH Graha Drishti parova (svi
    isti "drishti" sloj) ne smije samo brojem gurnuti kategoriju iznad 80 -
    treba barem SCORE_GATE_80_MIN_LAYERS neovisnih VRSTA slojeva.
    """
    planets = ["Sunce", "Mjesec", "Mars", "Merkur", "Jupiter", "Venera", "Saturn"]
    contacts = []
    for i, p in enumerate(planets):
        contacts.append(GrahaDrishtiContact(
            source_person="A", target_person="B", from_planet=p, to_planet=planets[(i + 1) % len(planets)],
            house_distance=7, strength=1.0, strength_label="puni (100%)",
            from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
        ))
    result = compute_synastry_scores(contacts, [], [], _empty_ashtakoota(), _no_kuja_dosha(), _empty_nakshatra_result())
    for cat in CATEGORY_NAMES:
        cat_score = result.categories[cat]
        if cat_score.independent_layers < SCORE_GATE_80_MIN_LAYERS:
            assert cat_score.score <= 80.0, f"{cat} premašio 80 s manje od {SCORE_GATE_80_MIN_LAYERS} neovisna sloja"
