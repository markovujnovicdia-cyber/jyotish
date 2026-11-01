"""
Raja Yoge (zahtjev #12) - detaljan modul koji ZASEBNO prijavljuje SVAKI
sambandha (odnos) između vladara kendre i vladara trikone, umjesto jedne
generičke stavke "Raja Yoga: DA/NE".

Klasično pravilo (BPHS, više poglavlja): odnos (konjunkcija, uzajaman
aspekt, jednosmjeran aspekt, Parivartana, ili fizički položaj jednog
vladara u kući drugoga) između vladara BILO KOJE kendre (1./4./7./10.) i
BILO KOJE trikone (1./5./9.) stvara Raja Yogu. Kad je isti planet vladar
i kendre i trikone istovremeno (Yogakaraka - zahtjev #20), to je ZASEBNA
kategorija (core.yoga_engine.rules.raja.find_yogakaraka), ne dio ovog
sweepa (ovaj modul traži odnos IZMEĐU DVA RAZLIČITA planeta).

Dharma-Karmadhipati Yoga (9. i 10. vladar) je klasično NAJVAŽNIJA pojedinačna
kombinacija unutar ovog skupa - prijavljena i kao dio općeg sweepa I kao
zasebna, imenovana yoga.

NAMJERNO IZOSTAVLJENO (zahtjev #29 - ne izmišljati): "Maha Raja Yoga" kao
zaseban, precizno omeđen klasični termin - izvori ga koriste nedosljedno
(često samo kao opisni pojam za posebno jaku Raja Yogu, ne kao vlastito
formacijsko pravilo), pa nije registriran kao zasebna yoga - vidi
PENDING_REVIEW niže i finalni izvještaj. Isto vrijedi za yoge iz Hora
Lagne/Ghatika Lagne (core/yoga_engine/context.py objašnjava zašto).
"""

from typing import List

from core.houses import houses_ruled_by_planet
from core.yoga_engine.context import ChartContext, CLASSICAL_SEVEN, KENDRA_HOUSES, TRIKONA_HOUSES
from core.yoga_engine.models import DebugLog, YogaDefinition, YogaResult, ReferencePoint
from core.yoga_engine.registry import register, mark_pending_review
from core.yoga_engine.strength import compute_planet_yoga_strength, classify_status

_PURE_KENDRA = {4, 7, 10}
_PURE_TRIKONA = {5, 9}


def find_yogakaraka(chart: ChartContext) -> List[dict]:
    """Planet koji istovremeno vlada BAREM jednom kendrom I BAREM jednom trikonom (2 RAZLIČITE kuće) - zahtjev #20."""
    asc = chart.ascendant_sign_index
    found = []
    for p in CLASSICAL_SEVEN:
        ruled = set(houses_ruled_by_planet(p, asc))
        if (ruled & _PURE_KENDRA and ruled & TRIKONA_HOUSES) or (ruled & KENDRA_HOUSES and ruled & _PURE_TRIKONA):
            found.append({"planet": p, "houses": sorted(ruled)})
    return found


def _relation_types(chart: ChartContext, a: str, b: str) -> List[str]:
    types = []
    if chart.has_exchange(a, b):
        types.append("Parivartana (razmjena znakova)")
        return types  # exchange je posebna, ne kombinira se s ostalim provjerama
    if chart.same_sign(a, b):
        types.append("konjunkcija (isti znak)")
        return types
    if chart.mutual_aspect(a, b):
        types.append("uzajaman aspekt")
    else:
        if chart.planet_aspects(a, b):
            types.append(f"{a} aspektira {b}")
        elif chart.planet_aspects(b, a):
            types.append(f"{b} aspektira {a}")
    a_houses = set(houses_ruled_by_planet(b, chart.ascendant_sign_index))
    if chart.house_of(a) in a_houses:
        types.append(f"{a} je fizički smješten u kući koju vlada {b}")
    b_houses = set(houses_ruled_by_planet(a, chart.ascendant_sign_index))
    if chart.house_of(b) in b_houses:
        types.append(f"{b} je fizički smješten u kući koju vlada {a}")
    return types


def _pair_strength(chart: ChartContext, a: str, b: str) -> float:
    return (compute_planet_yoga_strength(chart, a, house_number=chart.house_of(a)).total +
            compute_planet_yoga_strength(chart, b, house_number=chart.house_of(b)).total) / 2


@register(YogaDefinition(
    id="raja_yoga_sweep", sanskrit_name="राज योग", transliteration="Raja Yoga (opći pregled)",
    hr_name="Raja Yoga (odnos vladara kendre i trikone)",
    hr_description="Svaki pronađeni odnos (konjunkcija/aspekt/razmjena/položaj) između DVA RAZLIČITA vladara kendre i trikone, prikazan zasebno.",
    category="Raja Yoga", source="BPHS", reference_point=ReferencePoint.LAGNA.value,
))
def _raja_yoga_sweep(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    asc = chart.ascendant_sign_index
    kendra_lords = {h: chart.house_lord(h) for h in sorted(KENDRA_HOUSES)}
    trikona_lords = {h: chart.house_lord(h) for h in sorted(TRIKONA_HOUSES)}
    log.note(f"Vladari kendri: {kendra_lords}")
    log.note(f"Vladari trikona: {trikona_lords}")

    results: List[YogaResult] = []
    seen_pairs = set()
    for kh, kl in kendra_lords.items():
        for th, tl in trikona_lords.items():
            if kh == th or kl == tl:
                continue
            key = (kh, th)
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            rel_types = _relation_types(chart, kl, tl)
            present = bool(rel_types)
            log.check(f"Vladar {kh}. ({kl}) <-> vladar {th}. ({tl})", present, "; ".join(rel_types) or "-")
            if not present:
                continue
            strength = _pair_strength(chart, kl, tl)
            results.append(YogaResult(
                id="raja_yoga_sweep",
                name=f"Raja Yoga - vladar {kh}. i vladar {th}. ({', '.join(rel_types)})",
                sanskrit_name="राज योग", transliteration=f"Raja Yoga ({kh}-{th})",
                present=True, category="Raja Yoga", planets=[kl, tl], houses=sorted({kh, th}),
                reference=ReferencePoint.LAGNA.value, strength=round(strength, 1),
                status=classify_status(True, strength),
                reasons=[f"Vladar {kh}. kuće ({kl}) i vladar {th}. kuće ({tl}): {r}." for r in rel_types],
                source="BPHS", debug_log=list(log.lines), instance_label=f"{kh}-{th}",
            ))
    if not results:
        log.result(False)
        results.append(YogaResult(
            id="raja_yoga_sweep", name="Raja Yoga (odnos vladara kendre i trikone)", sanskrit_name="राज योग",
            transliteration="Raja Yoga", present=False, category="Raja Yoga", planets=[], houses=[],
            reference=ReferencePoint.LAGNA.value, strength=0.0, status=classify_status(False, 0.0),
            reasons=["Nijedan odnos između različitih vladara kendre i trikone nije pronađen."],
            source="BPHS", debug_log=log.lines,
        ))
    else:
        log.result(True)
    return results


@register(YogaDefinition(
    id="dharma_karmadhipati_yoga", sanskrit_name="धर्म कर्माधिपति योग",
    transliteration="Dharma-Karmadhipati Yoga", hr_name="Dharma-Karmadhipati Yoga",
    hr_description="Odnos između vladara 9. (Dharma) i vladara 10. (Karma) kuće - klasično najjača pojedinačna Raja Yoga kombinacija.",
    category="Raja Yoga", source="BPHS", reference_point=ReferencePoint.LAGNA.value,
    planets_involved=[],
))
def _dharma_karmadhipati(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    lord9 = chart.house_lord(9)
    lord10 = chart.house_lord(10)
    log.note(f"Vladar 9.: {lord9}, vladar 10.: {lord10}")
    if lord9 == lord10:
        log.note("Isti planet vlada i 9. i 10. kućom - to je Yogakaraka slučaj, ne odnos dva planeta.")
        return [YogaResult(
            id="dharma_karmadhipati_yoga", name="Dharma-Karmadhipati Yoga", sanskrit_name="धर्म कर्माधिपति योग",
            transliteration="Dharma-Karmadhipati Yoga", present=False, category="Raja Yoga",
            planets=[lord9], houses=[9, 10], reference=ReferencePoint.LAGNA.value, strength=0.0,
            status=classify_status(False, 0.0),
            reasons=[f"{lord9} vlada i 9. i 10. kućom istovremeno - vidi Yogakaraka, ne odnos dva planeta."],
            source="BPHS", debug_log=log.lines,
        )]

    rel_types = _relation_types(chart, lord9, lord10)
    present = bool(rel_types)
    log.check(f"Odnos {lord9} (9.) i {lord10} (10.)", present, "; ".join(rel_types) or "-")
    log.result(present)
    strength = _pair_strength(chart, lord9, lord10) if present else 0.0
    return [YogaResult(
        id="dharma_karmadhipati_yoga", name="Dharma-Karmadhipati Yoga", sanskrit_name="धर्म कर्माधिपति योग",
        transliteration="Dharma-Karmadhipati Yoga", present=present, category="Raja Yoga",
        planets=[lord9, lord10] if present else [], houses=[9, 10] if present else [],
        reference=ReferencePoint.LAGNA.value, strength=round(strength, 1), status=classify_status(present, strength),
        reasons=[f"Vladar 9. ({lord9}) i vladar 10. ({lord10}): {r}." for r in rel_types],
        source="BPHS", debug_log=log.lines,
    )]


@register(YogaDefinition(
    id="yogakaraka", sanskrit_name="योगकारक", transliteration="Yogakaraka",
    hr_name="Yogakaraka",
    hr_description="Planet koji istovremeno vlada kendrom I trikonom (dvije različite kuće) - najsnažniji pojedinačni raja-signifikator za dani ascendent.",
    category="Raja Yoga", source="BPHS", reference_point=ReferencePoint.LAGNA.value,
))
def _yogakaraka_rule(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    found = find_yogakaraka(chart)
    log.note(f"Yogakaraka kandidati: {found}")
    if not found:
        log.result(False)
        return [YogaResult(
            id="yogakaraka", name="Yogakaraka", sanskrit_name="योगकारक", transliteration="Yogakaraka",
            present=False, category="Raja Yoga", planets=[], houses=[], reference=ReferencePoint.LAGNA.value,
            strength=0.0, status=classify_status(False, 0.0),
            reasons=["Za ovaj ascendent nijedan planet ne vlada i kendrom i trikonom istovremeno."],
            source="BPHS", debug_log=log.lines,
        )]
    results = []
    for entry in found:
        p, houses = entry["planet"], entry["houses"]
        house_now = chart.house_of(p)
        b = compute_planet_yoga_strength(chart, p, house_number=house_now)
        reasons = [f"{p} vlada kućama {', '.join(f'{h}.' for h in houses)} (kendra i trikona istovremeno)."]
        reasons.append(f"{p} je trenutno u {house_now}. kući ({chart.positions[p].sign}).")
        results.append(YogaResult(
            id="yogakaraka", name=f"Yogakaraka: {p}", sanskrit_name="योगकारक", transliteration=f"Yogakaraka ({p})",
            present=True, category="Raja Yoga", planets=[p], houses=houses, reference=ReferencePoint.LAGNA.value,
            strength=round(b.total, 1), status=classify_status(True, b.total), reasons=reasons,
            source="BPHS", debug_log=log.lines, instance_label=p,
        ))
    log.result(True)
    return results


@register(YogaDefinition(
    id="atmakaraka_raja_yoga", sanskrit_name="आत्मकारक राज योग", transliteration="Atmakaraka Raja Yoga (Jaimini)",
    hr_name="Raja Yoga preko Atmakarake (Jaimini)",
    hr_description="Atmakaraka u konjunkciji ili uzajamnom aspektu s vladarom kendre ili trikone.",
    category="Raja Yoga", source="Jaimini", reference_point=ReferencePoint.LAGNA.value,
    variant="Jaimini varijanta - jednostavan, često citiran princip (AK povezan s kendra/trikona vladarom)",
))
def _atmakaraka_raja_yoga(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    ak = chart.atmakaraka
    all_lords = {h: chart.house_lord(h) for h in sorted(KENDRA_HOUSES | TRIKONA_HOUSES)}
    hits = []
    for h, lord in all_lords.items():
        if lord == ak:
            continue
        rel = _relation_types(chart, ak, lord)
        if rel:
            hits.append((h, lord, rel))
            log.check(f"Atmakaraka ({ak}) <-> vladar {h}. ({lord})", True, "; ".join(rel))
    present = bool(hits)
    log.result(present)
    strength = _pair_strength(chart, ak, hits[0][1]) if present else 0.0
    reasons = [f"Atmakaraka ({ak}) i vladar {h}. ({lord}): {'; '.join(r)}." for h, lord, r in hits]
    return [YogaResult(
        id="atmakaraka_raja_yoga", name="Raja Yoga preko Atmakarake (Jaimini)", sanskrit_name="आत्मकारक राज योग",
        transliteration="Atmakaraka Raja Yoga", present=present, category="Raja Yoga",
        planets=[ak] + [lord for _, lord, _ in hits] if present else [ak],
        houses=[h for h, _, _ in hits], reference=ReferencePoint.LAGNA.value, strength=round(strength, 1),
        status=classify_status(present, strength), reasons=reasons, source="Jaimini",
        variant="Jaimini varijanta", debug_log=log.lines,
    )]


# --- Namjerno neimplementirano - vidi docstring na vrhu datoteke ---
mark_pending_review(YogaDefinition(
    id="maha_raja_yoga", sanskrit_name="महा राज योग", transliteration="Maha Raja Yoga",
    hr_name="Maha Raja Yoga", hr_description="Termin se u izvorima koristi nedosljedno - nije registriran kao zasebno pravilo.",
    category="Raja Yoga", source="razni", reference_point=ReferencePoint.LAGNA.value,
    review_note="Izvori se razilaze je li ovo zaseban formacijski uvjet ili samo opisni naziv za vrlo jaku Raja Yogu - nisam siguran u jedinstveno klasično pravilo.",
))
mark_pending_review(YogaDefinition(
    id="karakamsha_raja_yoga", sanskrit_name="कारकांश राज योग", transliteration="Karakamsha Raja Yoga",
    hr_name="Raja Yoga iz Karakamsha Lagne", hr_description="Kombinacije preko Karakamsha Lagne koje BPHS/Jaimini izvori navode - nisam dovoljno siguran u točnu, jedinstvenu formulaciju.",
    category="Raja Yoga", source="Jaimini", reference_point=ReferencePoint.KARAKAMSHA.value,
    review_note="Više varijanti u izvorima (koji kendre od Karakamshe, koji planeti) - potrebna provjera protiv primarnog izvora prije implementacije.",
))
