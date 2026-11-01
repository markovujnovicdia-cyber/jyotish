"""
Ostale imenovane klasične yoge (zahtjev #17) - katalog s POSTOJEĆIM,
implementiranim pravilima za yoge gdje mi je klasična formulacija dovoljno
sigurna, PLUS eksplicitno neimplementirane (mark_pending_review) za one
gdje se izvori razilaze ili mi definicija nije dovoljno sigurna iz sjećanja
(zahtjev #2, #29 - NE izmišljati).

IMPLEMENTIRANO (razumna sigurnost, standardna/naširoko citirana formulacija):
  - Lakshmi Yoga, Saraswati Yoga, Kalanidhi Yoga, Vasumati Yoga,
    Lagnadhi Yoga, Chamara Yoga.

NAMJERNO NEIMPLEMENTIRANO (vidi PENDING_REVIEW, requires_source_review):
  Shankha, Bheri, Kahala, Parvata, Gauri, Matsya, Kurma, Khadga, Kusuma,
  Kalpadruma, Trimurti, Srinatha, Sharada, Suparijata, Virinchi, Pushkala -
  izvori se razilaze ili mi preciznu formulaciju nisam dovoljno siguran da
  je klasično potvrđena.
"""

from typing import List

from core.yoga_engine.context import ChartContext, CLASSICAL_SEVEN, KENDRA_HOUSES, TRIKONA_HOUSES, UPACHAYA_HOUSES, house_from
from core.yoga_engine.models import DebugLog, YogaDefinition, YogaResult, ReferencePoint
from core.yoga_engine.registry import register, mark_pending_review
from core.yoga_engine.strength import compute_planet_yoga_strength, classify_status


@register(YogaDefinition(
    id="lakshmi_yoga", sanskrit_name="लक्ष्मी योग", transliteration="Lakshmi Yoga", hr_name="Lakshmi Yoga",
    hr_description="Lagna lord jak (vlastiti/uzvišen) I 9. lord (Bhagyesha) jak, u kendri ili trikoni.",
    category="Ostale klasične yoge", source="Phaladipika",
    variant="Phaladīpikā varijanta (uobičajena formulacija)", reference_point=ReferencePoint.LAGNA.value,
))
def _lakshmi_yoga(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    lagna_lord = chart.house_lord(1)
    lord9 = chart.house_lord(9)
    lagna_strong = log.check(f"Lagna lord ({lagna_lord}) je jak (vlastiti/uzvišen)",
                              chart.is_own_sign(lagna_lord) or chart.is_exalted(lagna_lord))
    lord9_strong = log.check(f"9. lord ({lord9}) je jak (vlastiti/uzvišen)",
                              chart.is_own_sign(lord9) or chart.is_exalted(lord9))
    house9lord = chart.house_of(lord9)
    lord9_in_good_house = log.check(f"9. lord je u kendri/trikoni", house9lord in (KENDRA_HOUSES | TRIKONA_HOUSES),
                                     f"{house9lord}. kuća")
    present = lagna_strong and lord9_strong and lord9_in_good_house
    log.result(present)
    reasons, strength = [], 0.0
    if present:
        reasons = [
            f"Lagna lord ({lagna_lord}) je {chart.dignity(lagna_lord)}.",
            f"9. lord ({lord9}) je {chart.dignity(lord9)}, u {house9lord}. kući.",
        ]
        strength = (compute_planet_yoga_strength(chart, lagna_lord).total +
                    compute_planet_yoga_strength(chart, lord9, house_number=house9lord).total) / 2
    return [YogaResult(
        id="lakshmi_yoga", name="Lakshmi Yoga", sanskrit_name="लक्ष्मी योग", transliteration="Lakshmi Yoga",
        present=present, category="Ostale klasične yoge", planets=[lagna_lord, lord9] if present else [],
        houses=[1, house9lord] if present else [], reference=ReferencePoint.LAGNA.value,
        strength=round(strength, 1), status=classify_status(present, strength), reasons=reasons,
        source="Phaladipika", variant="Phaladīpikā varijanta", debug_log=log.lines,
    )]


@register(YogaDefinition(
    id="saraswati_yoga", sanskrit_name="सरस्वती योग", transliteration="Saraswati Yoga", hr_name="Saraswati Yoga",
    hr_description="Jupiter, Venera i Merkur u kendri/trikoni/2. kući, uz jakog Jupitera.",
    category="Ostale klasične yoge", source="BPHS/Saravali", reference_point=ReferencePoint.LAGNA.value,
))
def _saraswati_yoga(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    target_houses = KENDRA_HOUSES | TRIKONA_HOUSES | {2}
    positions = {p: chart.house_of(p) for p in ("Jupiter", "Venera", "Merkur")}
    all_placed = all(h in target_houses for h in positions.values())
    for p, h in positions.items():
        log.check(f"{p} u kendri/trikoni/2. kući", h in target_houses, f"{h}. kuća")
    jupiter_strong = chart.is_own_sign("Jupiter") or chart.is_exalted("Jupiter") or chart.is_moolatrikona("Jupiter")
    log.check("Jupiter jak (vlastiti/uzvišen/Moolatrikona)", jupiter_strong)
    present = all_placed and jupiter_strong
    log.result(present)
    reasons, strength = [], 0.0
    if present:
        reasons = [f"{p} je u {h}. kući." for p, h in positions.items()]
        reasons.append(f"Jupiter je {chart.dignity('Jupiter')}.")
        strength = sum(compute_planet_yoga_strength(chart, p, house_number=h).total for p, h in positions.items()) / 3
    return [YogaResult(
        id="saraswati_yoga", name="Saraswati Yoga", sanskrit_name="सरस्वती योग", transliteration="Saraswati Yoga",
        present=present, category="Ostale klasične yoge", planets=list(positions.keys()) if present else [],
        houses=sorted(set(positions.values())) if present else [], reference=ReferencePoint.LAGNA.value,
        strength=round(strength, 1), status=classify_status(present, strength), reasons=reasons,
        source="BPHS/Saravali", debug_log=log.lines,
    )]


@register(YogaDefinition(
    id="kalanidhi_yoga", sanskrit_name="कलानिधि योग", transliteration="Kalanidhi Yoga", hr_name="Kalanidhi Yoga",
    hr_description="Jupiter u 2./5./9. kući, u konjunkciji ili aspektu s Venerom i Merkurom.",
    category="Ostale klasične yoge", source="BPHS", reference_point=ReferencePoint.LAGNA.value,
))
def _kalanidhi_yoga(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    jup_house = chart.house_of("Jupiter")
    in_house = log.check("Jupiter u 2./5./9. kući", jup_house in (2, 5, 9), f"{jup_house}. kuća")
    venus_ok = chart.same_sign("Jupiter", "Venera") or chart.planet_aspects("Venera", "Jupiter") or chart.planet_aspects("Jupiter", "Venera")
    mercury_ok = chart.same_sign("Jupiter", "Merkur") or chart.planet_aspects("Merkur", "Jupiter") or chart.planet_aspects("Jupiter", "Merkur")
    log.check("Venera u konjunkciji/aspektu s Jupiterom", venus_ok)
    log.check("Merkur u konjunkciji/aspektu s Jupiterom", mercury_ok)
    present = in_house and venus_ok and mercury_ok
    log.result(present)
    reasons, strength = [], 0.0
    if present:
        reasons = [f"Jupiter je u {jup_house}. kući, povezan s Venerom i Merkurom."]
        strength = compute_planet_yoga_strength(chart, "Jupiter", house_number=jup_house).total
    return [YogaResult(
        id="kalanidhi_yoga", name="Kalanidhi Yoga", sanskrit_name="कलानिधि योग", transliteration="Kalanidhi Yoga",
        present=present, category="Ostale klasične yoge", planets=["Jupiter", "Venera", "Merkur"] if present else [],
        houses=[jup_house] if present else [], reference=ReferencePoint.LAGNA.value, strength=round(strength, 1),
        status=classify_status(present, strength), reasons=reasons, source="BPHS", debug_log=log.lines,
    )]


@register(YogaDefinition(
    id="vasumati_yoga", sanskrit_name="वसुमती योग", transliteration="Vasumati Yoga", hr_name="Vasumati Yoga",
    hr_description="Prirodni dobrotvori u upachaya kućama (3./6./10./11.) od Lagne ili od Mjeseca.",
    category="Ostale klasične yoge", source="BPHS", reference_point=ReferencePoint.LAGNA.value,
))
def _vasumati_yoga(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    benefics = [p for p in CLASSICAL_SEVEN if chart.is_natural_benefic(p)]
    from_lagna = [p for p in benefics if chart.house_of(p) in UPACHAYA_HOUSES]
    moon_sign = chart.sign_index("Mjesec")
    from_moon = [p for p in benefics if house_from(moon_sign, chart.sign_index(p)) in UPACHAYA_HOUSES]
    log.check("Dobrotvori u upachaya od Lagne", bool(from_lagna), ", ".join(from_lagna) or "-")
    log.check("Dobrotvori u upachaya od Mjeseca", bool(from_moon), ", ".join(from_moon) or "-")
    present = bool(from_lagna) or bool(from_moon)
    log.result(present)
    chosen = from_lagna if from_lagna else from_moon
    ref = ReferencePoint.LAGNA.value if from_lagna else ReferencePoint.CHANDRA_LAGNA.value
    reasons = []
    strength = 0.0
    if present:
        reasons.append(f"Dobrotvori u upachaya kućama ({'od Lagne' if from_lagna else 'od Mjeseca'}): {', '.join(chosen)}.")
        strength = sum(compute_planet_yoga_strength(chart, p).total for p in chosen) / len(chosen)
    return [YogaResult(
        id="vasumati_yoga", name="Vasumati Yoga", sanskrit_name="वसुमती योग", transliteration="Vasumati Yoga",
        present=present, category="Ostale klasične yoge", planets=chosen if present else [], houses=[],
        reference=ref, strength=round(strength, 1), status=classify_status(present, strength), reasons=reasons,
        source="BPHS", debug_log=log.lines,
    )]


@register(YogaDefinition(
    id="lagnadhi_yoga", sanskrit_name="लग्नाधि योग", transliteration="Lagnadhi Yoga", hr_name="Lagnadhi Yoga",
    hr_description="Prirodni dobrotvori u 6./7./8. kući OD LAGNE (analogno Adhi Yogi, koja se broji od Mjeseca).",
    category="Ostale klasične yoge", source="BPHS",
    variant="analogija Adhi Yoge primijenjena na Lagnu umjesto na Mjesec", reference_point=ReferencePoint.LAGNA.value,
))
def _lagnadhi_yoga(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    houses_covered = {}
    for h in (6, 7, 8):
        occupants = [p for p in CLASSICAL_SEVEN if chart.is_natural_benefic(p) and chart.house_of(p) == h]
        if occupants:
            houses_covered[h] = occupants
        log.check(f"Dobrotvor u {h}. od Lagne", bool(occupants), ", ".join(occupants) or "-")
    present = bool(houses_covered)
    log.result(present)
    strength = min(100.0, 35.0 + 20.0 * len(houses_covered)) if present else 0.0
    reasons = [f"{h}. od Lagne: {', '.join(ps)}." for h, ps in sorted(houses_covered.items())]
    return [YogaResult(
        id="lagnadhi_yoga", name="Lagnadhi Yoga", sanskrit_name="लग्नाधि योग", transliteration="Lagnadhi Yoga",
        present=present, category="Ostale klasične yoge", planets=[p for ps in houses_covered.values() for p in ps],
        houses=sorted(houses_covered.keys()), reference=ReferencePoint.LAGNA.value, strength=round(strength, 1),
        status=classify_status(present, strength), reasons=reasons, source="BPHS", debug_log=log.lines,
    )]


@register(YogaDefinition(
    id="chamara_yoga", sanskrit_name="चामर योग", transliteration="Chamara Yoga", hr_name="Chamara Yoga",
    hr_description="Lagna lord je uzvišen, u kendri, i aspektiran/konjunkt s Jupiterom.",
    category="Ostale klasične yoge", source="Saravali", reference_point=ReferencePoint.LAGNA.value,
))
def _chamara_yoga(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    lagna_lord = chart.house_lord(1)
    house_now = chart.house_of(lagna_lord)
    exalted = log.check(f"Lagna lord ({lagna_lord}) je uzvišen", chart.is_exalted(lagna_lord))
    in_kendra = log.check(f"Lagna lord je u kendri", house_now in KENDRA_HOUSES, f"{house_now}. kuća")
    jupiter_linked = (lagna_lord != "Jupiter") and (chart.same_sign(lagna_lord, "Jupiter") or chart.planet_aspects("Jupiter", lagna_lord))
    log.check("Aspektiran/konjunkt s Jupiterom", jupiter_linked)
    present = exalted and in_kendra and jupiter_linked
    log.result(present)
    reasons, strength = [], 0.0
    if present:
        reasons = [f"Lagna lord ({lagna_lord}) je uzvišen, u {house_now}. kući (kendra), povezan s Jupiterom."]
        strength = compute_planet_yoga_strength(chart, lagna_lord, house_number=house_now).total
    return [YogaResult(
        id="chamara_yoga", name="Chamara Yoga", sanskrit_name="चामर योग", transliteration="Chamara Yoga",
        present=present, category="Ostale klasične yoge", planets=[lagna_lord, "Jupiter"] if present else [],
        houses=[house_now] if present else [], reference=ReferencePoint.LAGNA.value, strength=round(strength, 1),
        status=classify_status(present, strength), reasons=reasons, source="Saravali", debug_log=log.lines,
    )]


# ---------------------------------------------------------------------------
# Namjerno NEimplementirano - vidi docstring na vrhu datoteke
# ---------------------------------------------------------------------------

for _id, _sanskrit, _name, _note in [
    ("shankha_yoga", "शंख योग", "Shankha Yoga", "Više varijanti (5./6. lord odnos + snaga lagna/9. lorda) - nisam siguran koja je izvorna."),
    ("bheri_yoga", "भेरी योग", "Bheri Yoga", "Više varijanti u izvorima, nisam siguran u jedinstvenu formulaciju."),
    ("kahala_yoga", "कहल योग", "Kahala Yoga", "Formulacija (4./9. lord odnos + snaga lagna lorda) nije mi dovoljno sigurna za sve detalje."),
    ("parvata_yoga", "पर्वत योग", "Parvata Yoga", "Više varijanti (kendre/8-12 prazni ili dobrotvori) - nesiguran izbor."),
    ("gauri_yoga", "गौरी योग", "Gauri Yoga", "Formulacija preko Navamshe 7. lorda nije mi dovoljno sigurna."),
    ("matsya_yoga", "मत्स्य योग", "Matsya Yoga", "Nisam dovoljno siguran u točnu klasičnu formulaciju."),
    ("kurma_yoga", "कूर्म योग", "Kurma Yoga", "Nisam dovoljno siguran u točnu klasičnu formulaciju."),
    ("khadga_yoga", "खड्ग योग", "Khadga Yoga", "Nisam dovoljno siguran u točnu klasičnu formulaciju."),
    ("kusuma_yoga", "कुसुम योग", "Kusuma Yoga", "Nisam dovoljno siguran u točnu klasičnu formulaciju."),
    ("kalpadruma_yoga", "कल्पद्रुम योग", "Kalpadruma Yoga", "Jaimini yoga s više uvjetnih koraka (AK/Karakamsha lord lanac) - kompleksna, nisam dovoljno siguran u sve korake."),
    ("trimurti_yoga", "त्रिमूर्ति योग", "Trimurti Yoga", "Nisam pronašao dosljednu, jedinstvenu formulaciju u sjećanju."),
    ("srinatha_yoga", "श्रीनाथ योग", "Srinatha Yoga", "Nisam dovoljno siguran u točnu klasičnu formulaciju."),
    ("sharada_yoga", "शारदा योग", "Sharada Yoga", "Nisam dovoljno siguran u točnu klasičnu formulaciju."),
    ("suparijata_yoga", "सुपारिजात योग", "Suparijata Yoga", "Nisam dovoljno siguran u točnu klasičnu formulaciju."),
    ("virinchi_yoga", "विरिञ्चि योग", "Virinchi Yoga", "Nisam dovoljno siguran u točnu klasičnu formulaciju."),
    ("pushkala_yoga", "पुष्कल योग", "Pushkala Yoga", "Više izvora navodi različite uvjete (lagna lord + Mjesec/Lagna odnos) - nesiguran izbor."),
]:
    mark_pending_review(YogaDefinition(
        id=_id, sanskrit_name=_sanskrit, transliteration=_name, hr_name=_name,
        hr_description="Namjerno neimplementirano - vidi review_note.", category="Ostale klasične yoge",
        source="razni", reference_point=ReferencePoint.LAGNA.value, review_note=_note,
    ))
