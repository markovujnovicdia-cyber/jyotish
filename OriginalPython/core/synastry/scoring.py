"""
Kategorijsko bodovanje sinastrije (poglavlje 4 specifikacije).

Devet kategorija (0-100, polazna vrijednost core.synastry.scoring_config.
BASE_SCORE=50), izvedeno iz VEĆ IZRAČUNATIH struktura (Graha Drishti,
konjunkcije, kućni overlay, Ashtakoota, Kuja Dosha, nakšatra sinastrija,
D9 ponovljeni obrasci) - ovaj modul NE računa nikakve nove astronomske
podatke, samo agregira postojeće rezultate u transparentan rezultat.

ISPRAVAK (rekalibracija - bivši rezultati poput 97-99/100 za gotovo svaku
kategoriju, "previše zasićeno bodovanje"): dosadašnji sustav je imao TRI
neovisne slabosti koje su se zbrajale:

1. `pair_key` se gradio kao `frozenset({ime_planeta_a, ime_planeta_b})` -
   BEZ oznake osobe. Kako su nazivi planeta (Mars, Venera...) identični u
   obje karte, ovo je pogrešno spajalo/isključivalo RAZLIČITE fizičke
   kontakte (npr. "A-Mars → B-Venera" i "B-Mars → A-Venera" su dijelili
   isti ključ). Sada se koristi core.synastry.deduplication.contact_key
   (person-svjestan).
2. Djelomični (three_quarter/half/quarter) Graha Drishti aspekti su nosili
   preveliku težinu (linearno c.strength: 0.75/0.5/0.25) - sada
   core.synastry.scoring_config.DRISHTI_WEIGHT (0.30/0.18/0.08) i
   MAX_PARTIAL_DRISHTI_SHARE ograničavaju njihov udio.
3. Nije bilo gornje ograde po paru (MAX_PAIR_CONTRIBUTION_PER_CATEGORY),
   diminishing-returns pri zbrajanju (DIMINISHING_RETURN_FACTOR), ni
   provjere broja NEOVISNIH slojeva prije dopuštanja rezultata >80/>90
   (SCORE_GATE_80_MIN_LAYERS/SCORE_GATE_90_MIN_LAYERS).

Dvostruko brojanje iste ULOGE istog fizičkog planeta (npr. Saturn je i
Darakaraka i vladar 7. kuće) se sprječava preko
core.synastry.deduplication.role_multiplier - dodatne uloge POJAČAVAJU
već izbrojani kontakt (ograničen multiplikator), ne dodaju novi neovisan
bod.
"""

import math
from typing import Dict, List, Optional, Set

from core.synastry.deduplication import (
    RoleMap, combined_role_multiplier, role_multiplier,
    key_from_drishti_contact, key_from_conjunction,
)
from core.synastry.models import (
    AshtakootaResult, CategoryScore, ConjunctionContact, GrahaDrishtiContact,
    HouseOverlayRow, KujaDoshaComparison, NakshatraSynastryResult, ScoringFactor,
    SynastryScoreResult, VargaSynastryResult,
)
from core.synastry.scoring_config import (
    BASE_SCORE, SATURATION_SCALE, CATEGORY_NAMES, NOT_YET_AVAILABLE_CATEGORIES,
    DRISHTI_CATEGORY_WEIGHTS, DRISHTI_SINGLE_PLANET_WEIGHTS, SEVENTH_HOUSE_ASPECT_BONUS,
    DRISHTI_WEIGHT, SPECIAL_FULL_MULTIPLIER,
    CONJUNCTION_SINGLE_PLANET_WEIGHTS, EXACT_CONJUNCTION_MULTIPLIER,
    OVERLAY_HOUSE_WEIGHTS, OVERLAY_PLANET_MULTIPLIER,
    OVERLAY_CHALLENGING_PLANETS, OVERLAY_CHALLENGING_HOUSES, OVERLAY_CHALLENGING_WEIGHT,
    KUTA_CATEGORY_WEIGHTS, KUJA_DOSHA_CONFLICT_WEIGHT, KUJA_DOSHA_MARRIAGE_PENALTY,
    NAKSHATRA_REPEATED_THEME_WEIGHT, NAKSHATRA_SAME_LORD_WEIGHT,
    NAKSHATRA_MUTUAL_DISPOSITOR_WEIGHT, NAKSHATRA_DISPOSITOR_CONFIRMED_WEIGHT,
    D1_D9_REPEAT_BONUS_CAP,
    MAX_PAIR_CONTRIBUTION_PER_CATEGORY, MAX_PARTIAL_DRISHTI_SHARE,
    MAX_CATEGORIES_PER_PAIR, SECONDARY_CATEGORY_FRACTION,
    DIMINISHING_RETURN_FACTOR,
    SCORE_GATE_80_MIN_LAYERS, SCORE_GATE_90_MIN_LAYERS,
    HIGH_CONFLICT_THRESHOLD, MARRIAGE_HIGH_CEILING_WITHOUT_STABILIZERS,
    NATURAL_MALEFICS, MALEFIC_AFFLICTION_FACTOR, KUTA_NEUTRAL_FRACTION,
)
from core.aspects import is_special_full_aspect

# Interni "bucket" oblik prije dedupliciranja: {category: {pair_key: [ScoringFactor, ...]}}
_Bucket = Dict[str, Dict[str, List[ScoringFactor]]]

CONFLICT_CATEGORY = "Konflikt i pritisak"
MARRIAGE_CATEGORY = "Bračni potencijal"


def _add(bucket: _Bucket, category: str, pair_key: str, description: str, weight: float,
         contribution: float, polarity: str, layer: str, is_partial_drishti: bool = False):
    bucket.setdefault(category, {}).setdefault(pair_key, []).append(
        ScoringFactor(
            description=description, pair_key=pair_key, weight=weight, contribution=contribution,
            polarity=polarity, layer=layer, is_partial_drishti=is_partial_drishti,
        )
    )


def _cap_categories(cat_weights: Dict[str, float]) -> Dict[str, float]:
    """
    Jedan fizički kontakt smije PUNOM težinom doprinijeti u najviše
    MAX_CATEGORIES_PER_PAIR kategorija (spec 10.1/10.2/11) - ostale
    kategorije u kojima bi isti kontakt teoretski nešto značio dobivaju
    samo mali sekundarni doprinos (SECONDARY_CATEGORY_FRACTION).
    """
    if len(cat_weights) <= MAX_CATEGORIES_PER_PAIR:
        return cat_weights
    ranked = sorted(cat_weights.items(), key=lambda kv: abs(kv[1]), reverse=True)
    capped = {}
    for i, (cat, w) in enumerate(ranked):
        capped[cat] = w if i < MAX_CATEGORIES_PER_PAIR else w * SECONDARY_CATEGORY_FRACTION
    return capped


def _drishti_tier(strength: float) -> str:
    return {1.0: "full", 0.75: "three_quarter", 0.5: "half", 0.25: "quarter"}.get(strength, "quarter")


def _collect_drishti_signals(bucket: _Bucket, contacts: List[GrahaDrishtiContact], role_map: RoleMap):
    for c in contacts:
        tier = _drishti_tier(c.strength)
        is_partial = tier != "full"
        strength_multiplier = DRISHTI_WEIGHT.get(tier, c.strength)
        if is_special_full_aspect(c.from_planet, c.house_distance):
            strength_multiplier *= SPECIAL_FULL_MULTIPLIER

        planet_a, planet_b = (c.from_planet, c.to_planet) if c.source_person == "A" else (c.to_planet, c.from_planet)
        pair_key = key_from_drishti_contact(c)
        role_mult = combined_role_multiplier(role_map, "A", planet_a, "B", planet_b)

        pair = frozenset({c.from_planet, c.to_planet})
        cat_weights: Dict[str, float] = dict(DRISHTI_CATEGORY_WEIGHTS.get(pair, {}))
        for planet in sorted(pair):  # sorted - frozenset iteracija ovisi o hash seedu, ovo drži rezultat deterministicnim
            for cat, w in DRISHTI_SINGLE_PLANET_WEIGHTS.get(planet, {}).items():
                cat_weights[cat] = cat_weights.get(cat, 0.0) + w
        cat_weights = _cap_categories(cat_weights)

        desc = (
            f"Graha Drishti {c.from_planet} ({c.source_person}) → {c.to_planet} ({c.target_person}) - "
            f"{c.house_distance}. kuća, {c.strength_label}"
        )
        for cat, w in cat_weights.items():
            polarity = "challenging" if cat == CONFLICT_CATEGORY else "positive"
            contribution = w * strength_multiplier * role_mult
            _add(bucket, cat, pair_key, desc, w, contribution, polarity, layer="drishti", is_partial_drishti=is_partial)

        # ISPRAVAK 2: 7. kuća (izravno partnerstvo) više NIJE automatski
        # pozitivan bonus bez obzira KOJI planeti sudjeluju - malefik na toj
        # osi (posebno OBA malefika, npr. Mars-Saturn opozicija) klasično
        # nosi napetost/test braka, ne čistu potvrdu.
        if c.house_distance == 7:
            malefics_here = pair & NATURAL_MALEFICS
            for cat, w in SEVENTH_HOUSE_ASPECT_BONUS.items():
                if len(malefics_here) == 0:
                    contribution = w * strength_multiplier * role_mult
                    _add(bucket, cat, pair_key + ":7th", desc, w, contribution, "positive", layer="drishti", is_partial_drishti=is_partial)
                else:
                    sign = -1.0 if len(malefics_here) == 2 else (1.0 - 2.0 * MALEFIC_AFFLICTION_FACTOR)
                    contribution = w * sign * strength_multiplier * role_mult
                    note = " - oba malefika na osi, nosi napetost" if len(malefics_here) == 2 else " - malefik na osi, nosi napetost, ne čistu potvrdu"
                    _add(bucket, cat, pair_key + ":7th", desc + note, w, contribution, "challenging" if contribution < 0 else "positive", layer="drishti", is_partial_drishti=is_partial)

        # Aflikcija (ISPRAVAK 2): malefik koji aspektira "mekog" značitelja
        # (Mjesec/Merkur/Venera/Jupiter) NARUŠAVA baš tu kategoriju - ne
        # ostaje samo "manje pozitivno", nego dobiva vlastiti, neovisan
        # izazovan doprinos. Izuzeci: (a) par već posebno tretiran u
        # DRISHTI_CATEGORY_WEIGHTS za tu kategoriju, (b) kategorija u kojoj
        # je MALEFIK SAM po sebi već pozitivan značitelj (npr. Mars je i
        # svoj vlastiti signifikator "Privlačnost i kemija" - Venera-Mars
        # kontakt se NE kažnjava, to je klasično SAM svoj signal).
        malefics_in_pair = pair & NATURAL_MALEFICS
        if len(pair) == 2 and len(malefics_in_pair) == 1:
            non_malefic = next(iter(pair - malefics_in_pair))
            malefic = next(iter(malefics_in_pair))
            special_pair_categories = set(DRISHTI_CATEGORY_WEIGHTS.get(pair, {}).keys())
            malefic_own_categories = set(DRISHTI_SINGLE_PLANET_WEIGHTS.get(malefic, {}).keys())
            for cat, base_w in DRISHTI_SINGLE_PLANET_WEIGHTS.get(non_malefic, {}).items():
                if cat == CONFLICT_CATEGORY or cat in special_pair_categories or cat in malefic_own_categories:
                    continue
                affliction_w = base_w * MALEFIC_AFFLICTION_FACTOR
                affliction_contribution = -affliction_w * strength_multiplier * role_mult
                _add(
                    bucket, cat, pair_key + ":affliction",
                    desc + f" - {malefic} narušava ovaj kontakt ({non_malefic})",
                    affliction_w, affliction_contribution, "challenging", layer="drishti",
                    is_partial_drishti=is_partial,
                )


def _collect_conjunction_signals(bucket: _Bucket, conjunctions: List[ConjunctionContact], role_map: RoleMap):
    for c in conjunctions:
        pair_key = key_from_conjunction(c)
        role_mult = combined_role_multiplier(role_map, "A", c.person_a_object, "B", c.person_b_object)
        pair = frozenset({c.person_a_object, c.person_b_object})
        cat_weights: Dict[str, float] = {}
        for obj in sorted(pair):
            for cat, w in CONJUNCTION_SINGLE_PLANET_WEIGHTS.get(obj, {}).items():
                cat_weights[cat] = cat_weights.get(cat, 0.0) + w
        cat_weights = _cap_categories(cat_weights)

        multiplier = EXACT_CONJUNCTION_MULTIPLIER if c.is_exact else 1.0
        desc = f"Konjunkcija {c.person_a_object} (A) - {c.person_b_object} (B), {c.degree_distance:.1f}°" + (" (egzaktna)" if c.is_exact else "")
        for cat, w in cat_weights.items():
            polarity = "challenging" if cat == CONFLICT_CATEGORY else "positive"
            contribution = w * multiplier * role_mult
            _add(bucket, cat, pair_key, desc, w, contribution, polarity, layer="conjunction")

        # Aflikcija (ISPRAVAK 2) - vidi analogni blok u _collect_drishti_signals.
        malefics_in_pair = pair & NATURAL_MALEFICS
        if len(pair) == 2 and len(malefics_in_pair) == 1:
            non_malefic = next(iter(pair - malefics_in_pair))
            malefic = next(iter(malefics_in_pair))
            malefic_own_categories = set(CONJUNCTION_SINGLE_PLANET_WEIGHTS.get(malefic, {}).keys())
            for cat, base_w in CONJUNCTION_SINGLE_PLANET_WEIGHTS.get(non_malefic, {}).items():
                if cat == CONFLICT_CATEGORY or cat in malefic_own_categories:
                    continue
                affliction_w = base_w * MALEFIC_AFFLICTION_FACTOR
                affliction_contribution = -affliction_w * multiplier * role_mult
                _add(
                    bucket, cat, pair_key + ":affliction",
                    desc + f" - {malefic} narušava ovu konjunkciju ({non_malefic})",
                    affliction_w, affliction_contribution, "challenging", layer="conjunction",
                )


def _collect_overlay_signals(bucket: _Bucket, overlay_rows: List[HouseOverlayRow], role_map: RoleMap):
    for r in overlay_rows:
        cat_weights = OVERLAY_HOUSE_WEIGHTS.get(r.whole_sign_house)
        planet_role_mult = role_multiplier(role_map.roles_for(r.source_person, r.planet))
        pair_key = f"overlay:{r.planet}({r.source_person})->{r.target_person}house{r.whole_sign_house}"
        desc = f"{r.planet} ({r.source_person}) u {r.whole_sign_house}. kući osobe {r.target_person}"

        if cat_weights:
            multiplier = OVERLAY_PLANET_MULTIPLIER.get(r.planet, 1.0)
            for cat, w in cat_weights.items():
                # ISPRAVAK 2: malefik u 7. kući (izravno partnerstvo) nije
                # jednostavno "dobro za brak" - nosi napetost/test, isti
                # princip kao aflikcija kod Graha Drishti/konjunkcija.
                if cat == MARRIAGE_CATEGORY and r.whole_sign_house == 7 and r.planet in OVERLAY_CHALLENGING_PLANETS:
                    contribution = -w * MALEFIC_AFFLICTION_FACTOR * planet_role_mult
                    _add(
                        bucket, cat, pair_key + ":affliction",
                        desc + " - malefik u 7. kući nosi napetost, ne čistu potvrdu",
                        w, contribution, "challenging", layer="overlay",
                    )
                else:
                    contribution = w * multiplier * planet_role_mult
                    _add(bucket, cat, pair_key, desc, w, contribution, "positive", layer="overlay")

        # ISPRAVAK (spec 8): overlay više NIJE automatski isključivo "positive" -
        # malefik u 8./12. kući dodaje i izazovni (Konflikt i pritisak) signal.
        if r.planet in OVERLAY_CHALLENGING_PLANETS and r.whole_sign_house in OVERLAY_CHALLENGING_HOUSES:
            for cat, w in OVERLAY_CHALLENGING_WEIGHT.items():
                contribution = w * planet_role_mult
                _add(
                    bucket, cat, pair_key + ":challenge",
                    desc + " - malefik u 8./12. kući nosi i izazovan (ne samo pozitivan) naglasak",
                    w, contribution, "challenging", layer="overlay",
                )


def _collect_ashtakoota_signals(bucket: _Bucket, ashtakoota: AshtakootaResult):
    by_name = {k.name: k for k in ashtakoota.kutas}
    for kuta_name, info in KUTA_CATEGORY_WEIGHTS.items():
        kuta = by_name.get(kuta_name)
        if kuta is None or kuta.max_points == 0:
            continue
        fraction = kuta.points / kuta.max_points
        # ISPRAVAK 2: centrirano oko KUTA_NEUTRAL_FRACTION (0.5), ne oko 0 -
        # kuta na 0% (klasičan dosha, npr. Nadi) sada AKTIVNO oduzima puni
        # max_contribution umjesto da samo doprinese "0".
        signed_fraction = (fraction - KUTA_NEUTRAL_FRACTION) / (1.0 - KUTA_NEUTRAL_FRACTION)
        contribution = info["max_contribution"] * signed_fraction
        pair_key = f"ashtakoota:{kuta_name}"
        desc = f"Ashtakoota - {kuta_name}: {kuta.points:.1f}/{kuta.max_points:.0f}"
        polarity = "positive" if contribution >= 0 else "challenging"
        _add(bucket, info["category"], pair_key, desc, info["max_contribution"], contribution, polarity, layer="ashtakoota")


def _collect_kuja_dosha_signals(bucket: _Bucket, kuja: KujaDoshaComparison):
    max_severity = max(kuja.person_a.severity_score, kuja.person_b.severity_score)
    if max_severity > 0:
        contribution = KUJA_DOSHA_CONFLICT_WEIGHT * (max_severity / 100.0)
        _add(
            bucket, CONFLICT_CATEGORY, "kuja_dosha",
            f"Kuja Dosha (najveća ozbiljnost: {max_severity:.0f}/100)",
            KUJA_DOSHA_CONFLICT_WEIGHT, contribution, "challenging", layer="kuja",
        )
        # ISPRAVAK (spec 12): kazna na Bračni potencijal je sada RAZMJERNA
        # (1 - balancing_fraction), ne sve-ili-ništa - asimetrična obostrana
        # Kuja Dosha (npr. blaga vs jaka) i dalje nosi DIO kazne.
        penalty_scale = 1.0 - kuja.balancing_fraction
        if max_severity >= 66.0 and penalty_scale > 0.0:
            penalty = KUJA_DOSHA_MARRIAGE_PENALTY * penalty_scale
            _add(
                bucket, MARRIAGE_CATEGORY, "kuja_dosha_marriage",
                f"Kuja Dosha prisutna (uravnoteženje: {kuja.balancing_fraction * 100:.0f}%)",
                KUJA_DOSHA_MARRIAGE_PENALTY, -penalty, "challenging", layer="kuja",
            )


def _collect_nakshatra_signals(bucket: _Bucket, nakshatra_result: NakshatraSynastryResult):
    for theme in nakshatra_result.repeated_themes:
        pair_key = f"nakshatra_theme:{theme.nakshatra}"
        desc = f"Ponovljena nakšatra ({theme.nakshatra}) kroz: {', '.join(theme.points_involved)}"
        _add(bucket, "Karmička/intenzivna povezanost", pair_key, desc, NAKSHATRA_REPEATED_THEME_WEIGHT, NAKSHATRA_REPEATED_THEME_WEIGHT, "positive", layer="nakshatra")

    # NAPOMENA (spec 3): SAMO potvrđene kategorije (scored=True) nose bod -
    # "dispositor_symbolic" (kategorija 5, slaba simbolička napomena) je
    # NAMJERNO izostavljena ovdje.
    for link in nakshatra_result.cross_links:
        if not link.scored:
            continue
        pair_key = f"nakshatra_{link.relation_type}:{link.source_label}-{link.target_label}"
        if link.relation_type == "mutual_dispositor":
            _add(bucket, "Karmička/intenzivna povezanost", pair_key,
                 f"Uzajamna dispozicija: {link.source_label} - {link.target_label}",
                 NAKSHATRA_MUTUAL_DISPOSITOR_WEIGHT, NAKSHATRA_MUTUAL_DISPOSITOR_WEIGHT, "positive", layer="nakshatra")
        elif link.relation_type == "same_nakshatra_lord":
            _add(bucket, "Emocionalna povezanost", pair_key,
                 f"Isti vladar nakšatre: {link.source_label} - {link.target_label}",
                 NAKSHATRA_SAME_LORD_WEIGHT, NAKSHATRA_SAME_LORD_WEIGHT, "positive", layer="nakshatra")
        elif link.relation_type == "dispositor_confirmed":
            _add(bucket, "Karmička/intenzivna povezanost", pair_key,
                 f"Potvrđena vladar-nakšatre veza: {link.source_label} - {link.target_label}",
                 NAKSHATRA_DISPOSITOR_CONFIRMED_WEIGHT, NAKSHATRA_DISPOSITOR_CONFIRMED_WEIGHT, "positive", layer="nakshatra")


def _apply_d1_d9_bonus(bucket: _Bucket, confirmed_pair_keys: Set[str]) -> Set[str]:
    """
    ISPRAVAK (spec 9): D1↔D9 potvrda VIŠE NE dodaje nov, neovisan bod -
    umjesto toga POJAČAVA (do +D1_D9_REPEAT_BONUS_CAP udjela) doprinos
    POSTOJEĆEG D1 para u SVIM kategorijama u kojima se taj par već pojavljuje.
    Vraća skup pair_key-eva koji su stvarno pronađeni u bucketu (za brojanje
    "d9" kao neovisnog sloja u _finalize_category).
    """
    matched: Set[str] = set()
    if not confirmed_pair_keys:
        return matched
    for category_buckets in bucket.values():
        for pair_key, factors in category_buckets.items():
            if pair_key in confirmed_pair_keys:
                matched.add(pair_key)
                for f in factors:
                    f.contribution *= (1.0 + D1_D9_REPEAT_BONUS_CAP)
    return matched


def _finalize_category(
    category: str, pair_buckets: Dict[str, List[ScoringFactor]], d9_confirmed_pairs: Set[str],
    emphasis_multiplier: float = 1.0,
) -> CategoryScore:
    counted: List[ScoringFactor] = []
    excluded: List[str] = []
    for pair_key, factors in pair_buckets.items():
        if len(factors) == 1:
            chosen = factors[0]
        else:
            chosen = max(factors, key=lambda f: abs(f.contribution))
            for f in factors:
                if f is not chosen:
                    excluded.append(f"{f.description} (isključeno - jači nalaz za isti par već brojan)")
        # Gornja ograda po paru (spec 10.5/10.11)
        if abs(chosen.contribution) > MAX_PAIR_CONTRIBUTION_PER_CATEGORY:
            chosen.contribution = math.copysign(MAX_PAIR_CONTRIBUTION_PER_CATEGORY, chosen.contribution)
        counted.append(chosen)

    # MAX_PARTIAL_DRISHTI_SHARE (spec 5/10.6): djelomični Graha Drishti aspekti
    # smiju činiti najviše ovoliko udjela u UKUPNOM apsolutnom doprinosu.
    full_abs = sum(abs(f.contribution) for f in counted if not f.is_partial_drishti)
    partial_abs = sum(abs(f.contribution) for f in counted if f.is_partial_drishti)
    if partial_abs > 0:
        current_share = partial_abs / (full_abs + partial_abs)
        if current_share > MAX_PARTIAL_DRISHTI_SHARE:
            k = (MAX_PARTIAL_DRISHTI_SHARE * full_abs) / (partial_abs * (1 - MAX_PARTIAL_DRISHTI_SHARE))
            for f in counted:
                if f.is_partial_drishti:
                    f.contribution *= k

    # Diminishing returns (spec 10.4): sortirano po jačini, svaki sljedeći
    # doprinos broji se s progresivno manjim množiteljem.
    def _diminishing_sum(values: List[float]) -> float:
        total = 0.0
        factor = 1.0
        for v in sorted(values, key=abs, reverse=True):
            total += v * factor
            factor *= DIMINISHING_RETURN_FACTOR
        return total

    # Vrsta odnosa (spec 1) - BLAGA prilagodba naglaska (core.synastry.
    # relationship_profiles), primijenjena PRIJE tanh/gate koraka tako da
    # gate-ovi i dalje ispravno rade na PRILAGOĐENOJ vrijednosti. NIKAD ne
    # dira sirove GrahaDrishtiContact/ConjunctionContact/HouseOverlayRow
    # podatke - samo skalira već izračunati zbroj doprinosa OVE kategorije.
    raw_deviation = _diminishing_sum([f.contribution for f in counted]) * emphasis_multiplier
    positive_total = _diminishing_sum([f.contribution for f in counted if f.polarity == "positive"]) * emphasis_multiplier
    challenge_total = _diminishing_sum([abs(f.contribution) for f in counted if f.polarity == "challenging"]) * emphasis_multiplier

    scaled_deviation = 50.0 * math.tanh(raw_deviation / SATURATION_SCALE)
    score = BASE_SCORE + scaled_deviation
    positive_score = BASE_SCORE + 50.0 * math.tanh(positive_total / SATURATION_SCALE)
    challenge_score = BASE_SCORE + 50.0 * math.tanh(challenge_total / SATURATION_SCALE)

    # Neovisni slojevi (spec 10.7/10.8) - distinct .layer vrijednosti među
    # BROJANIM faktorima, plus "d9" ako je bilo koji od tih parova
    # potvrđen D1↔D9 ponovljenom temom.
    layers = {f.layer for f in counted}
    if any(f.pair_key in d9_confirmed_pairs for f in counted):
        layers.add("d9")
    independent_layers = len(layers)

    dominant_polarity = "challenging" if category == CONFLICT_CATEGORY else "positive"
    confirmations = sum(1 for f in counted if f.polarity == dominant_polarity)
    contradictions = [f for f in counted if f.polarity != dominant_polarity and f.polarity != "neutral"]
    contradictions_count = len(contradictions)
    has_strong_contradiction = any(abs(f.contribution) >= MAX_PAIR_CONTRIBUTION_PER_CATEGORY * 0.5 for f in contradictions) or contradictions_count >= 2

    # Score gate (spec 10.7/10.8): rezultat >80/>90 zahtijeva dovoljno
    # neovisnih slojeva (i, za >90, odsustvo jake kontradikcije).
    if score > MARRIAGE_HIGH_CEILING_WITHOUT_STABILIZERS and (independent_layers < SCORE_GATE_90_MIN_LAYERS or has_strong_contradiction):
        score = MARRIAGE_HIGH_CEILING_WITHOUT_STABILIZERS
    elif score > 80.0 and independent_layers < SCORE_GATE_80_MIN_LAYERS:
        score = 80.0

    if independent_layers >= SCORE_GATE_90_MIN_LAYERS and not has_strong_contradiction:
        confidence = "visoka"
    elif independent_layers >= 2:
        confidence = "srednja"
    else:
        confidence = "niska"

    top_positive = sorted((f for f in counted if f.polarity == "positive"), key=lambda f: -f.contribution)[:3]
    top_challenge = sorted((f for f in counted if f.polarity == "challenging"), key=lambda f: f.contribution)[:3]

    return CategoryScore(
        category=category, score=round(score, 1), factors=counted,
        excluded_duplicates=excluded,
        method=(
            f"Polazna vrijednost {BASE_SCORE:.0f}/100, zatim diminishing-returns zbroj najjačeg "
            f"doprinosa po svakom jedinstvenom (person-svjesnom) paru (dedupliciranje sprječava "
            f"dvostruko brojanje iste veze), ograničen po paru (max {MAX_PAIR_CONTRIBUTION_PER_CATEGORY:.0f}) "
            f"i po udjelu djelomičnih aspekata (max {MAX_PARTIAL_DRISHTI_SHARE * 100:.0f}%), propušten kroz "
            f"zasićujuću krivulju (tanh), s gornjom ogradom kad nema dovoljno neovisnih slojeva."
        ),
        positive_score=round(positive_score, 1), challenge_score=round(challenge_score, 1),
        net_score=round(score, 1), confidence=confidence,
        independent_layers=independent_layers, confirmations=confirmations,
        contradictions_count=contradictions_count,
        top_positive_notes=[f.description for f in top_positive],
        top_challenge_notes=[f.description for f in top_challenge],
    )


def compute_synastry_scores(
    drishti_contacts: List[GrahaDrishtiContact],
    conjunctions: List[ConjunctionContact],
    overlay_rows: List[HouseOverlayRow],
    ashtakoota: AshtakootaResult,
    kuja_comparison: KujaDoshaComparison,
    nakshatra_result: NakshatraSynastryResult,
    navamsha_result: Optional[VargaSynastryResult] = None,
    role_map: Optional[RoleMap] = None,
    category_emphasis: Optional[Dict[str, float]] = None,
) -> SynastryScoreResult:
    """
    category_emphasis: BLAGI (core.synastry.relationship_profiles -
    MIN/MAX_CATEGORY_EMPHASIS_MULTIPLIER, tipično 0.85-1.15) multiplikator
    po kategoriji, izveden iz odabrane vrste odnosa (spec 1) - primjenjuje
    se PRIJE tanh/gate koraka. NIKAD ne mijenja ulazne astronomske
    kontakte, samo naglasak/težinu već izračunatih doprinosa.
    """
    role_map = role_map or RoleMap()
    category_emphasis = category_emphasis or {}
    bucket: _Bucket = {cat: {} for cat in CATEGORY_NAMES}

    _collect_drishti_signals(bucket, drishti_contacts, role_map)
    _collect_conjunction_signals(bucket, conjunctions, role_map)
    _collect_overlay_signals(bucket, overlay_rows, role_map)
    _collect_ashtakoota_signals(bucket, ashtakoota)
    _collect_kuja_dosha_signals(bucket, kuja_comparison)
    _collect_nakshatra_signals(bucket, nakshatra_result)

    confirmed_keys = set(navamsha_result.repeated_pattern_pair_keys) if navamsha_result is not None else set()
    d9_confirmed_pairs = _apply_d1_d9_bonus(bucket, confirmed_keys)

    categories = {
        cat: _finalize_category(
            cat, bucket.get(cat, {}), d9_confirmed_pairs,
            emphasis_multiplier=category_emphasis.get(cat, 1.0),
        )
        for cat in CATEGORY_NAMES
    }

    # Konflikt/Bračni potencijal međuovisnost (spec 10.9): visok konflikt bez
    # jasnih stabilizirajućih pokazatelja spušta strop Bračnog potencijala.
    conflict_score = categories[CONFLICT_CATEGORY].score
    marriage = categories[MARRIAGE_CATEGORY]
    if conflict_score > HIGH_CONFLICT_THRESHOLD and marriage.score > MARRIAGE_HIGH_CEILING_WITHOUT_STABILIZERS:
        if marriage.independent_layers < SCORE_GATE_90_MIN_LAYERS:
            marriage.score = MARRIAGE_HIGH_CEILING_WITHOUT_STABILIZERS
            marriage.net_score = MARRIAGE_HIGH_CEILING_WITHOUT_STABILIZERS

    return SynastryScoreResult(categories=categories, not_available=list(NOT_YET_AVAILABLE_CATEGORIES))
