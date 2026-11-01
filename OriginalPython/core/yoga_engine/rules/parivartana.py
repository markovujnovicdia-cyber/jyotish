"""
Parivartana Yoga (razmjena znakova između vladara kuća) - Phaladīpikā
klasifikacija u 3 vrste (zahtjev #15).

Pravilo: dva planeta A i B čine Parivartanu ako A sjedi u znaku kojim
vlada B, I ISTOVREMENO B sjedi u znaku kojim vlada A (core.yoga_engine.
context.ChartContext.has_exchange). Koriste se ISKLJUČIVO 7 klasičnih
graha - Rahu/Ketu nikad nisu "vladari" nijednog znaka pa ne mogu sudjelovati.

Kad planet vlada DVJEMA kućama (Mars/Venera/Merkur/Jupiter/Saturn), kuća
RELEVANTNA za KONKRETNU razmjenu je ona čiji je znak fizički zauzet DRUGIM
planetom u paru (ne nužno "prva" ili "manja" kuća tog planeta) - ispravno
prati sve lordship relacije (zahtjev #15). Ako planet ima i DRUGU kuću
kojom vlada, a koja NIJE dio ove konkretne razmjene, ta se činjenica
zasebno navodi (informativno, ne mijenja klasifikaciju OVE razmjene).

Klasifikacija (Phaladīpikā varijanta - vidi napomenu o alternativnoj,
strožoj definiciji "Maha" ispod):
  - Maha Parivartana: NIJEDNA od dvije uključene kuće nije dusthana (6./8./12.)
  - Dainya Parivartana: OBJE uključene kuće su dusthana
  - Khala Parivartana: JEDNA kuća je dusthana, druga nije (miješano)

NAPOMENA o varijanti: neki izvori definiraju "Maha" STROŽE - samo kad su
OBJE kuće kendra ILI trikona (1/4/5/7/9/10), tretirajući 2./3./11. kao
"srednje" (što bi njihovu kombinaciju s kendrom/trikonom svrstalo u Khala
umjesto Maha). Ovdje je odabrana ŠIRA, češće citirana verzija (dusthana
vs. ne-dusthana) - označeno kao Phaladīpikā varijanta, obje verzije nisu
kontradiktorne u ishodu za većinu parova, razlikuju se samo kad je jedna
kuća 2./3./11. a druga kendra/trikona.
"""

from typing import List

from core.houses import houses_ruled_by_planet
from core.yoga_engine.context import ChartContext, CLASSICAL_SEVEN, house_from, is_dusthana
from core.yoga_engine.models import DebugLog, YogaDefinition, YogaResult, ReferencePoint
from core.yoga_engine.registry import register
from core.yoga_engine.strength import compute_planet_yoga_strength, classify_status


def _classify(house1: int, house2: int) -> str:
    d1, d2 = is_dusthana(house1), is_dusthana(house2)
    if d1 and d2:
        return "Dainya Parivartana"
    if d1 or d2:
        return "Khala Parivartana"
    return "Maha Parivartana"


def find_all_parivartanas(chart: ChartContext) -> List[dict]:
    found = []
    for i, p1 in enumerate(CLASSICAL_SEVEN):
        for p2 in CLASSICAL_SEVEN[i + 1:]:
            if not chart.has_exchange(p1, p2):
                continue
            house1 = house_from(chart.ascendant_sign_index, chart.sign_index(p2))
            house2 = house_from(chart.ascendant_sign_index, chart.sign_index(p1))
            found.append({"p1": p1, "p2": p2, "house1": house1, "house2": house2,
                          "type": _classify(house1, house2)})
    return found


@register(YogaDefinition(
    id="parivartana_yoga", sanskrit_name="परिवर्तन योग", transliteration="Parivartana Yoga",
    hr_name="Parivartana Yoga",
    hr_description="Razmjena znakova između dva vladara kuća - svaka pronađena razmjena prikazana zasebno.",
    category="Parivartana Yoga", source="Phaladipika", reference_point=ReferencePoint.LAGNA.value,
    variant="Phaladīpikā varijanta (Maha/Khala/Dainya po dusthana kriteriju)",
))
def _parivartana_rule(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    exchanges = find_all_parivartanas(chart)
    log.note(f"Pronađeno razmjena: {len(exchanges)}")

    if not exchanges:
        log.result(False)
        return [YogaResult(
            id="parivartana_yoga", name="Parivartana Yoga", sanskrit_name="परिवर्तन योग",
            transliteration="Parivartana Yoga", present=False, category="Parivartana Yoga",
            planets=[], houses=[], reference=ReferencePoint.LAGNA.value, strength=0.0,
            status=classify_status(False, 0.0), reasons=["Nijedna razmjena znakova nije pronađena među 7 klasičnih vladara."],
            source="Phaladipika", debug_log=log.lines,
        )]

    results = []
    for idx, ex in enumerate(exchanges, start=1):
        p1, p2, h1, h2, ptype = ex["p1"], ex["p2"], ex["house1"], ex["house2"], ex["type"]
        log.check(f"{p1} (vladar {h1}.) <-> {p2} (vladar {h2}.)", True, ptype)
        other_houses_p1 = [h for h in houses_ruled_by_planet(p1, chart.ascendant_sign_index) if h != h1]
        other_houses_p2 = [h for h in houses_ruled_by_planet(p2, chart.ascendant_sign_index) if h != h2]
        reasons = [
            f"{p1} sjedi u znaku {chart.positions[p2].sign} (vlada ga {p2}), a {p2} sjedi u znaku "
            f"{chart.positions[p1].sign} (vlada ga {p1}) - razmjena {h1}. i {h2}. kuće.",
        ]
        if other_houses_p1:
            reasons.append(f"{p1} također vlada {', '.join(f'{h}.' for h in other_houses_p1)} kućom/kućama (nije dio ove razmjene).")
        if other_houses_p2:
            reasons.append(f"{p2} također vlada {', '.join(f'{h}.' for h in other_houses_p2)} kućom/kućama (nije dio ove razmjene).")

        strength = (compute_planet_yoga_strength(chart, p1, house_number=chart.house_of(p1)).total +
                    compute_planet_yoga_strength(chart, p2, house_number=chart.house_of(p2)).total) / 2
        favorable = ptype != "Dainya Parivartana"

        results.append(YogaResult(
            id="parivartana_yoga", name=f"Parivartana Yoga #{idx}: {ptype} ({p1}↔{p2})",
            sanskrit_name="परिवर्तन योग", transliteration=f"{ptype} ({p1}-{p2})",
            present=True, category="Parivartana Yoga", planets=[p1, p2], houses=sorted([h1, h2]),
            reference=ReferencePoint.LAGNA.value, strength=round(strength, 1),
            status=classify_status(True, strength), reasons=reasons, source="Phaladipika",
            variant=f"{ptype} (Phaladīpikā, dusthana-kriterij)", debug_log=list(log.lines),
            favorable=favorable, instance_label=f"#{idx}",
        ))
    log.result(True)
    return results
