"""
Dhana Yoge (zahtjev #16) - zaseban detektor, svaka kombinacija PRIKAZANA
ZASEBNO (npr. "Dhana Yoga #1: lord 2. povezan s lordom 11.", "#2: lord 5.
povezan s lordom 9."), NE spojene u jednu generičku stavku.

Klasično se prvenstveno analiziraju odnosi (konjunkcija/aspekt/razmjena/
položaj - ista mehanika kao core.yoga_engine.rules.raja._relation_types)
između vladara 1., 2., 5., 9. i 11. kuće - svih C(5,2)=10 mogućih parova.
Dodatno se zasebno provjerava klasični direktni pokazatelj: prirodni
dobrotvor SMJEŠTEN u 2. ili 11. kući (bez potrebe za odnosom vladara).
"""

from typing import List

from core.yoga_engine.context import ChartContext, CLASSICAL_SEVEN
from core.yoga_engine.models import DebugLog, YogaDefinition, YogaResult, ReferencePoint
from core.yoga_engine.registry import register
from core.yoga_engine.rules.raja import _relation_types, _pair_strength
from core.yoga_engine.strength import classify_status, compute_planet_yoga_strength

_DHANA_HOUSES = [1, 2, 5, 9, 11]


@register(YogaDefinition(
    id="dhana_yoga_lords", sanskrit_name="धन योग", transliteration="Dhana Yoga (vladari)",
    hr_name="Dhana Yoga (odnos vladara 1./2./5./9./11.)",
    hr_description="Svaki pronađeni odnos između vladara dvije od kuća 1./2./5./9./11., prikazan zasebno.",
    category="Dhana Yoga", source="BPHS", reference_point=ReferencePoint.LAGNA.value,
))
def _dhana_yoga_lords(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    lords = {h: chart.house_lord(h) for h in _DHANA_HOUSES}
    log.note(f"Vladari 1./2./5./9./11.: {lords}")

    results: List[YogaResult] = []
    counter = 0
    seen_planet_pairs = set()
    for i, h1 in enumerate(_DHANA_HOUSES):
        for h2 in _DHANA_HOUSES[i + 1:]:
            l1, l2 = lords[h1], lords[h2]
            if l1 == l2:
                continue  # isti planet vlada objema - to je pojačanje snage TOG planeta, ne "odnos"
            planet_pair = tuple(sorted([l1, l2]))
            rel_types = _relation_types(chart, l1, l2)
            log.check(f"Vladar {h1}. ({l1}) <-> vladar {h2}. ({l2})", bool(rel_types), "; ".join(rel_types) or "-")
            if not rel_types:
                continue
            counter += 1
            strength = _pair_strength(chart, l1, l2)
            results.append(YogaResult(
                id="dhana_yoga_lords",
                name=f"Dhana Yoga #{counter}: lord {h1}. povezan s lordom {h2}. ({', '.join(rel_types)})",
                sanskrit_name="धन योग", transliteration=f"Dhana Yoga ({h1}-{h2})",
                present=True, category="Dhana Yoga", planets=[l1, l2], houses=sorted([h1, h2]),
                reference=ReferencePoint.LAGNA.value, strength=round(strength, 1), status=classify_status(True, strength),
                reasons=[f"Vladar {h1}. ({l1}) i vladar {h2}. ({l2}): {r}." for r in rel_types],
                source="BPHS", debug_log=list(log.lines), instance_label=f"#{counter}",
            ))
    if not results:
        log.result(False)
        results.append(YogaResult(
            id="dhana_yoga_lords", name="Dhana Yoga (odnos vladara)", sanskrit_name="धन योग",
            transliteration="Dhana Yoga", present=False, category="Dhana Yoga", planets=[], houses=[],
            reference=ReferencePoint.LAGNA.value, strength=0.0, status=classify_status(False, 0.0),
            reasons=["Nijedan odnos između vladara 1./2./5./9./11. kuće nije pronađen."],
            source="BPHS", debug_log=log.lines,
        ))
    else:
        log.result(True)
    return results


@register(YogaDefinition(
    id="dhana_yoga_benefic_placement", sanskrit_name="धन योग (स्थान)", transliteration="Dhana Yoga (izravni položaj)",
    hr_name="Dhana Yoga (dobrotvor u 2./11. kući)",
    hr_description="Prirodni dobrotvor izravno smješten u 2. ili 11. kući od Lagne - klasičan izravan pokazatelj bogatstva.",
    category="Dhana Yoga", source="BPHS", reference_point=ReferencePoint.LAGNA.value,
))
def _dhana_yoga_benefic_placement(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    hits = {}
    for h in (2, 11):
        occupants = [p for p in CLASSICAL_SEVEN if chart.house_of(p) == h and chart.is_natural_benefic(p)]
        if occupants:
            hits[h] = occupants
        log.check(f"Dobrotvor u {h}. kući", bool(occupants), ", ".join(occupants) or "-")
    present = bool(hits)
    log.result(present)
    strength = 0.0
    if present:
        all_planets = [p for ps in hits.values() for p in ps]
        strength = sum(compute_planet_yoga_strength(chart, p, house_number=chart.house_of(p)).total for p in all_planets) / len(all_planets)
    reasons = [f"{', '.join(ps)} u {h}. kući." for h, ps in hits.items()]
    return [YogaResult(
        id="dhana_yoga_benefic_placement", name="Dhana Yoga (dobrotvor u 2./11. kući)",
        sanskrit_name="धन योग (स्थान)", transliteration="Dhana Yoga (izravni položaj)", present=present,
        category="Dhana Yoga", planets=[p for ps in hits.values() for p in ps], houses=sorted(hits.keys()),
        reference=ReferencePoint.LAGNA.value, strength=round(strength, 1), status=classify_status(present, strength),
        reasons=reasons, source="BPHS", debug_log=log.lines,
    )]
