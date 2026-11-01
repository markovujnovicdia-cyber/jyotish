"""
Daridra i druge nepovoljne yoge (zahtjev #18) - ISTA strogoća pravila kao
kod povoljnih yoga (formation bool + strength/status zasebno, nema
"djelomičnih" nalaza bez zadovoljenog uvjeta).

IMPLEMENTIRANO:
  - Daridra Yoga: vladar 2. i/ili 11. kuće smješten u dusthani (6./8./12.).
  - Shakata Yoga (Chandra-Guru) - NAPOMENA O SUKOBU NAZIVA: ovo je POTPUNO
    DRUGA yoga od "Sakata Yoga" u Nabhasa skupini (core/yoga_engine/rules/
    nabhasa.py, koja se odnosi na planete u 1./7. kući) - klasični izvori
    koriste isto ime za dvije različite formacije, pa je ovdje eksplicitno
    preimenovana da se izbjegne zabuna. Pravilo: Mjesec u 6./8./12. OD JUPITERA.
  - Kemadruma Yoga je već implementirana u core/yoga_engine/rules/chandra.py
    (zahtjev #10 je izričito smjestio Kemadrumu u Chandra yoge, ne ovdje).

NAMJERNO NEIMPLEMENTIRANO (zahtjev #29): Bala-Arishta, Duryoga, Ava, Nisswa,
Mriti, Kuhoo, Pamara, Dushkriti, Nirbhagya - ili nemam dovoljno sigurnu
klasičnu formulaciju iz sjećanja, ili se izvori razilaze (neki od ovih su
regionalno/tradicijski specifični termini rijeđi u glavnim BPHS/Phaladipika/
Saravali/Brihat Jataka/Jataka Parijata izvorima).
"""

from typing import List

from core.yoga_engine.context import ChartContext, DUSTHANA_HOUSES, CLASSICAL_SEVEN, house_from
from core.yoga_engine.models import DebugLog, YogaDefinition, YogaResult, ReferencePoint
from core.yoga_engine.registry import register, mark_pending_review
from core.yoga_engine.strength import compute_planet_yoga_strength, classify_status


@register(YogaDefinition(
    id="daridra_yoga", sanskrit_name="दरिद्र योग", transliteration="Daridra Yoga", hr_name="Daridra Yoga",
    hr_description="Vladar 2. i/ili 11. kuće smješten u dusthani (6./8./12.) - klasičan pokazatelj financijskih poteškoća.",
    category="Nepovoljne yoge", source="BPHS", reference_point=ReferencePoint.LAGNA.value, favorable=False,
))
def _daridra_yoga(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    hits = {}
    for h in (2, 11):
        lord = chart.house_lord(h)
        lord_house = chart.house_of(lord)
        in_dusthana = lord_house in DUSTHANA_HOUSES
        log.check(f"Vladar {h}. ({lord}) u dusthani", in_dusthana, f"trenutno u {lord_house}.")
        if in_dusthana:
            hits[h] = (lord, lord_house)
    present = bool(hits)
    log.result(present)
    reasons = [f"Vladar {h}. kuće ({lord}) je u {lh}. kući (dusthana)." for h, (lord, lh) in hits.items()]
    strength = 0.0
    if present:
        vals = [compute_planet_yoga_strength(chart, lord, house_number=lh).total for lord, lh in hits.values()]
        # ovdje je NIŽA planetova snaga zapravo JAČI pokazatelj Daridre - invertiramo za "ozbiljnost"
        strength = 100.0 - (sum(vals) / len(vals))
        malefic_extra = [
            lord for lord, _ in hits.values()
            if any(chart.same_sign(lord, m) or chart.planet_aspects(m, lord) for m in CLASSICAL_SEVEN + ["Rahu", "Ketu"]
                   if m != lord and chart.is_natural_malefic(m))
        ]
        if malefic_extra:
            reasons.append(f"Dodatno pod utjecajem zlotvora (konjunkcija/aspekt): {', '.join(set(malefic_extra))}.")
    return [YogaResult(
        id="daridra_yoga", name="Daridra Yoga", sanskrit_name="दरिद्र योग", transliteration="Daridra Yoga",
        present=present, category="Nepovoljne yoge", planets=[lord for lord, _ in hits.values()],
        houses=sorted(hits.keys()), reference=ReferencePoint.LAGNA.value, strength=round(strength, 1),
        status=classify_status(present, strength), reasons=reasons, source="BPHS", debug_log=log.lines,
        favorable=False,
    )]


@register(YogaDefinition(
    id="shakata_dosha_moon_jupiter", sanskrit_name="शकट योग (चन्द्र-गुरु)",
    transliteration="Shakata Yoga (Chandra-Guru)", hr_name="Shakata Yoga (Mjesec-Jupiter)",
    hr_description=(
        "Mjesec u 6./8./12. kući OD JUPITERA - RAZLIČITO od Nabhasa 'Sakata Yoga' "
        "(core/yoga_engine/rules/nabhasa.py, planeti u 1./7. kući) - isto ime, druga formacija."
    ),
    category="Nepovoljne yoge", source="BPHS", reference_point=ReferencePoint.CHANDRA_LAGNA.value, favorable=False,
))
def _shakata_dosha(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    jup_sign = chart.sign_index("Jupiter")
    house = house_from(jup_sign, chart.sign_index("Mjesec"))
    present = log.check("Mjesec u 6./8./12. od Jupitera", house in DUSTHANA_HOUSES, f"{house}. od Jupitera")
    log.result(present)
    strength = 0.0
    reasons = []
    if present:
        reasons.append(f"Mjesec je u {house}. kući od Jupitera (dusthana).")
        strength = 100.0 - compute_planet_yoga_strength(chart, "Mjesec").total
    return [YogaResult(
        id="shakata_dosha_moon_jupiter", name="Shakata Yoga (Mjesec-Jupiter)", sanskrit_name="शकट योग (चन्द्र-गुरु)",
        transliteration="Shakata Yoga (Chandra-Guru)", present=present, category="Nepovoljne yoge",
        planets=["Mjesec", "Jupiter"] if present else [], houses=[house] if present else [],
        reference=ReferencePoint.CHANDRA_LAGNA.value, strength=round(strength, 1), status=classify_status(present, strength),
        reasons=reasons, source="BPHS", debug_log=log.lines, favorable=False,
    )]


for _id, _sanskrit, _name, _note in [
    ("bala_arishta", "बाल अरिष्ट", "Bala-Arishta", "Više klasičnih varijanti (kombinacije za ranu ugroženost) - nedovoljno siguran izbor bez rizika krive dijagnoze."),
    ("duryoga", "दुर्योग", "Duryoga", "Generički pojam u nekim izvorima, nema jedinstvenu formulaciju koju mogu potvrditi."),
    ("ava_yoga", "अव योग", "Ava Yoga", "Rijedak/regionalno specifičan termin - nisam pronašao pouzdanu formulaciju u sjećanju."),
    ("nisswa_yoga", "निःस्व योग", "Nisswa Yoga", "Rijedak termin - nedovoljno siguran u točnu formulaciju."),
    ("mriti_yoga", "मृति योग", "Mriti Yoga", "Osjetljiva (smrt-vezana) yoga - namjerno NE nagađam formulaciju bez pouzdanog izvora."),
    ("kuhoo_yoga", "कुहू योग", "Kuhoo Yoga", "Rijedak termin - nedovoljno siguran u točnu formulaciju."),
    ("pamara_yoga", "पामर योग", "Pamara Yoga", "Rijedak termin - nedovoljno siguran u točnu formulaciju."),
    ("dushkriti_yoga", "दुष्कृति योग", "Dushkriti Yoga", "Rijedak termin - nedovoljno siguran u točnu formulaciju."),
    ("nirbhagya_yoga", "निर्भाग्य योग", "Nirbhagya Yoga", "Rijedak termin - nedovoljno siguran u točnu formulaciju."),
]:
    mark_pending_review(YogaDefinition(
        id=_id, sanskrit_name=_sanskrit, transliteration=_name, hr_name=_name,
        hr_description="Namjerno neimplementirano - vidi review_note.", category="Nepovoljne yoge",
        source="razni", reference_point=ReferencePoint.LAGNA.value, favorable=False, review_note=_note,
    ))
