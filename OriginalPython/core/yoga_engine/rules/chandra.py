"""
Chandra (Mjesečeve) Yoge - BPHS, poglavlje "Various Yogas" (Sunapha/Anapha/
Durudhara/Kemadruma) i standardni dodaci (Gaja Kesari, Adhi Yoga, Chandra
Mangala, Amala od Chandre).

Zahtjev #10: Sunce se ISKLJUČUJE iz Sunapha/Anapha/Durudhara/Kemadruma
(klasično pravilo - "grah" u tim yogama znači bilo koji od preostalih 6
klasičnih planeta, ne Sunce). Kemadruma NIJE samo "prazna 2. i 12. od
Mjeseca" - implementirane su klasične iznimke/poništenja, vidi dolje.
"""

from typing import List

from core.yoga_engine.context import ChartContext, is_kendra, house_from, CLASSICAL_SEVEN
from core.yoga_engine.models import DebugLog, YogaDefinition, YogaResult, ReferencePoint
from core.yoga_engine.registry import register, select_from_group
from core.yoga_engine.strength import compute_planet_yoga_strength, classify_status

_NON_SUN_SIX = ["Mjesec", "Mars", "Merkur", "Jupiter", "Venera", "Saturn"]
_OTHER_SIX_FROM_MOON = ["Sunce", "Mars", "Merkur", "Jupiter", "Venera", "Saturn"]


def _planets_in_house_from_moon(chart: ChartContext, house: int, exclude_sun: bool = True) -> List[str]:
    moon_sign = chart.sign_index("Mjesec")
    pool = _OTHER_SIX_FROM_MOON[1:] if exclude_sun else _OTHER_SIX_FROM_MOON
    return [p for p in pool if house_from(moon_sign, chart.sign_index(p)) == house]


# ---------------------------------------------------------------------------
# Sunapha / Anapha / Durudhara
# ---------------------------------------------------------------------------

def _sunapha_anapha_durudhara(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    second = _planets_in_house_from_moon(chart, 2)
    twelfth = _planets_in_house_from_moon(chart, 12)
    log.check("Planet(i) osim Sunca u 2. od Mjeseca", bool(second), ", ".join(second) or "-")
    log.check("Planet(i) osim Sunca u 12. od Mjeseca", bool(twelfth), ", ".join(twelfth) or "-")

    results = []

    has_sunapha = bool(second) and not bool(twelfth)
    has_anapha = bool(twelfth) and not bool(second)
    has_durudhara = bool(second) and bool(twelfth)

    def _strength_for(planets: List[str], houses: List[int]) -> float:
        vals = [compute_planet_yoga_strength(chart, p).total for p in planets]
        return sum(vals) / len(vals) if vals else 0.0

    results.append(YogaResult(
        id="sunapha", name="Sunapha Yoga", sanskrit_name="सुनफा योग", transliteration="Sunapha Yoga",
        present=has_sunapha, category="Chandra Yoga", planets=second if has_sunapha else [],
        houses=[2] if has_sunapha else [], reference=ReferencePoint.CHANDRA_LAGNA.value,
        strength=round(_strength_for(second, [2]), 1) if has_sunapha else 0.0,
        status=classify_status(has_sunapha, _strength_for(second, [2]) if has_sunapha else 0.0),
        reasons=[f"{p} je u 2. od Mjeseca (bez Sunca)." for p in second] if has_sunapha else [],
        source="BPHS", debug_log=list(log.lines) + [f"REZULTAT (Sunapha) = {'PRISUTNA' if has_sunapha else 'NIJE PRISUTNA'}"],
    ))
    results.append(YogaResult(
        id="anapha", name="Anapha Yoga", sanskrit_name="अनफा योग", transliteration="Anapha Yoga",
        present=has_anapha, category="Chandra Yoga", planets=twelfth if has_anapha else [],
        houses=[12] if has_anapha else [], reference=ReferencePoint.CHANDRA_LAGNA.value,
        strength=round(_strength_for(twelfth, [12]), 1) if has_anapha else 0.0,
        status=classify_status(has_anapha, _strength_for(twelfth, [12]) if has_anapha else 0.0),
        reasons=[f"{p} je u 12. od Mjeseca (bez Sunca)." for p in twelfth] if has_anapha else [],
        source="BPHS", debug_log=list(log.lines) + [f"REZULTAT (Anapha) = {'PRISUTNA' if has_anapha else 'NIJE PRISUTNA'}"],
    ))
    both = second + twelfth
    results.append(YogaResult(
        id="durudhara", name="Durudhara Yoga", sanskrit_name="दुरुधरा योग", transliteration="Durudhara Yoga",
        present=has_durudhara, category="Chandra Yoga", planets=both if has_durudhara else [],
        houses=[2, 12] if has_durudhara else [], reference=ReferencePoint.CHANDRA_LAGNA.value,
        strength=round(_strength_for(both, [2, 12]), 1) if has_durudhara else 0.0,
        status=classify_status(has_durudhara, _strength_for(both, [2, 12]) if has_durudhara else 0.0),
        reasons=(
            [f"{p} je u 2. od Mjeseca." for p in second] + [f"{p} je u 12. od Mjeseca." for p in twelfth]
        ) if has_durudhara else [],
        source="BPHS", debug_log=list(log.lines) + [f"REZULTAT (Durudhara) = {'PRISUTNA' if has_durudhara else 'NIJE PRISUTNA'}"],
    ))
    return results


for _id, _name, _sanskrit in [
    ("sunapha", "Sunapha Yoga", "सुनफा योग"),
    ("anapha", "Anapha Yoga", "अनफा योग"),
    ("durudhara", "Durudhara Yoga", "दुरुधरा योग"),
]:
    register(YogaDefinition(
        id=_id, sanskrit_name=_sanskrit, transliteration=_name, hr_name=_name,
        hr_description="Planet(i) osim Sunca u 2. i/ili 12. kući od Mjeseca (BPHS).",
        category="Chandra Yoga", source="BPHS", reference_point=ReferencePoint.CHANDRA_LAGNA.value,
    ))(select_from_group(_sunapha_anapha_durudhara, _id))


# ---------------------------------------------------------------------------
# Kemadruma - PUNO pravilo + klasične iznimke/poništenja
# ---------------------------------------------------------------------------

@register(YogaDefinition(
    id="kemadruma", sanskrit_name="केमद्रुम योग", transliteration="Kemadruma Yoga",
    hr_name="Kemadruma Yoga",
    hr_description=(
        "Nijedan planet (osim Sunca) u 2. ili 12. od Mjeseca (dakle ni Sunapha, ni "
        "Anapha, ni Durudhara) - NIJE automatski prisutna ako je zadovoljen bilo koji "
        "od klasičnih uvjeta poništenja (vidi cancellation_factors)."
    ),
    category="Chandra Yoga", source="BPHS", reference_point=ReferencePoint.CHANDRA_LAGNA.value,
    favorable=False,
))
def _kemadruma(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    second = _planets_in_house_from_moon(chart, 2)
    twelfth = _planets_in_house_from_moon(chart, 12)
    empty_2_12 = log.check("2. i 12. od Mjeseca prazni (bez Sunca)", not second and not twelfth)

    if not empty_2_12:
        log.result(False)
        return [YogaResult(
            id="kemadruma", name="Kemadruma Yoga", sanskrit_name="केमद्रुम योग", transliteration="Kemadruma Yoga",
            present=False, category="Chandra Yoga", planets=["Mjesec"], houses=[],
            reference=ReferencePoint.CHANDRA_LAGNA.value, strength=0.0, status=classify_status(False, 0.0),
            reasons=["2. i/ili 12. od Mjeseca nisu prazni - osnovni uvjet Kemadrume nije zadovoljen."],
            source="BPHS", debug_log=log.lines, favorable=False,
        )]

    moon_sign = chart.sign_index("Mjesec")
    kendra_from_moon = [p for p in CLASSICAL_SEVEN if p != "Mjesec" and is_kendra(house_from(moon_sign, chart.sign_index(p)))]
    cond_kendra_from_moon = log.check("Planet u kendri (1/4/7/10) OD MJESECA", bool(kendra_from_moon), ", ".join(kendra_from_moon) or "-")

    moon_house_from_lagna = chart.house_of("Mjesec")
    cond_moon_kendra_lagna = log.check("Mjesec u kendri od Lagne", is_kendra(moon_house_from_lagna), f"kuća {moon_house_from_lagna}")

    jupiter_aspects_moon = chart.same_sign("Jupiter", "Mjesec") or chart.planet_aspects("Jupiter", "Mjesec")
    cond_jupiter = log.check("Jupiter u konjunkciji/aspektu s Mjesecom", jupiter_aspects_moon)

    cond_moon_dignity = log.check("Mjesec uzvišen ili u vlastitom znaku", chart.is_exalted("Mjesec") or chart.is_own_sign("Mjesec"))

    sun_sign = chart.sign_index("Sunce")
    is_full_moon_by_sign = house_from(moon_sign, sun_sign) == 7
    cond_full_moon = log.check("Sunce u 7. od Mjeseca (Pun Mjesec po znaku)", is_full_moon_by_sign)

    cancellations = []
    if cond_kendra_from_moon:
        cancellations.append(f"Planet(i) u kendri od Mjeseca: {', '.join(kendra_from_moon)}.")
    if cond_moon_kendra_lagna:
        cancellations.append(f"Mjesec je u kendri ({moon_house_from_lagna}.) od Lagne.")
    if cond_jupiter:
        cancellations.append("Jupiter je u konjunkciji ili aspektu s Mjesecom.")
    if cond_moon_dignity:
        cancellations.append(f"Mjesec je {chart.dignity('Mjesec')}.")
    if cond_full_moon:
        cancellations.append("Sunce je u 7. od Mjeseca (Pun Mjesec po znaku).")

    cancelled = bool(cancellations)
    log.result(not cancelled)  # present (kao nepovoljna yoga) samo ako NIJE poništena

    present = not cancelled
    return [YogaResult(
        id="kemadruma", name="Kemadruma Yoga", sanskrit_name="केमद्रुम योग", transliteration="Kemadruma Yoga",
        present=present, category="Chandra Yoga", planets=["Mjesec"], houses=[moon_house_from_lagna],
        reference=ReferencePoint.CHANDRA_LAGNA.value,
        strength=70.0 if present else 0.0,
        status="poništena" if cancelled else classify_status(True, 70.0),
        reasons=["2. i 12. od Mjeseca su prazni (bez Sunca), nijedan klasični uvjet poništenja nije zadovoljen."] if present else [],
        cancellation_factors=cancellations,
        source="BPHS", debug_log=log.lines, favorable=False,
    )]


# ---------------------------------------------------------------------------
# Adhi Yoga
# ---------------------------------------------------------------------------

@register(YogaDefinition(
    id="adhi_yoga", sanskrit_name="अधि योग", transliteration="Adhi Yoga", hr_name="Adhi Yoga",
    hr_description="Prirodni dobrotvori (Merkur/Jupiter/Venera) u 6., 7. i/ili 8. kući od Mjeseca.",
    category="Chandra Yoga", source="BPHS", reference_point=ReferencePoint.CHANDRA_LAGNA.value,
))
def _adhi_yoga(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    moon_sign = chart.sign_index("Mjesec")
    benefics = ["Merkur", "Jupiter", "Venera"]
    houses_covered = {}
    for h in (6, 7, 8):
        occupants = [p for p in benefics if house_from(moon_sign, chart.sign_index(p)) == h]
        if occupants:
            houses_covered[h] = occupants
        log.check(f"Dobrotvor u {h}. od Mjeseca", bool(occupants), ", ".join(occupants) or "-")

    present = bool(houses_covered)
    log.result(present)
    n_houses = len(houses_covered)
    strength = 0.0
    if present:
        strength = min(100.0, 40.0 + n_houses * 20.0)
    reasons = [f"{h}. od Mjeseca: {', '.join(ps)}." for h, ps in sorted(houses_covered.items())]
    if n_houses == 3:
        reasons.append("Sve tri kuće (6./7./8.) od Mjeseca zauzete dobrotvorima - najjača varijanta.")

    return [YogaResult(
        id="adhi_yoga", name="Adhi Yoga", sanskrit_name="अधि योग", transliteration="Adhi Yoga",
        present=present, category="Chandra Yoga", planets=[p for ps in houses_covered.values() for p in ps],
        houses=sorted(houses_covered.keys()), reference=ReferencePoint.CHANDRA_LAGNA.value,
        strength=round(strength, 1), status=classify_status(present, strength), reasons=reasons,
        source="BPHS", debug_log=log.lines,
    )]


# ---------------------------------------------------------------------------
# Gaja Kesari Yoga
# ---------------------------------------------------------------------------

@register(YogaDefinition(
    id="gajakesari", sanskrit_name="गजकेसरी योग", transliteration="Gaja Kesari Yoga",
    hr_name="Gaja Kesari Yoga",
    hr_description="Jupiter u kendri (1/4/7/10) od Mjeseca.",
    category="Chandra Yoga", source="BPHS", reference_point=ReferencePoint.CHANDRA_LAGNA.value,
    planets_involved=["Mjesec", "Jupiter"],
))
def _gajakesari(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    moon_sign = chart.sign_index("Mjesec")
    jup_sign = chart.sign_index("Jupiter")
    house = house_from(moon_sign, jup_sign)
    present = log.check("Jupiter u kendri od Mjeseca", is_kendra(house), f"{house}. kuća")
    log.result(present)

    reasons: List[str] = []
    strength = 0.0
    weakening: List[str] = []
    if present:
        reasons.append(f"Jupiter je u {house}. kući (kendra) od Mjeseca.")
        not_debilitated = not chart.is_debilitated("Jupiter")
        if not_debilitated:
            reasons.append("Jupiter nije u padu.")
        else:
            weakening.append("Jupiter je u padu - značajno slabi yogu.")
        if chart.is_waxing_moon():
            reasons.append("Mjesec je rastući (Shukla paksha).")
        b = compute_planet_yoga_strength(chart, "Jupiter", house_number=house)
        strength = b.total
        if chart.is_combust("Jupiter"):
            weakening.append("Jupiter je kombust.")

    return [YogaResult(
        id="gajakesari", name="Gaja Kesari Yoga", sanskrit_name="गजकेसरी योग", transliteration="Gaja Kesari Yoga",
        present=present, category="Chandra Yoga", planets=["Mjesec", "Jupiter"], houses=[house] if present else [],
        reference=ReferencePoint.CHANDRA_LAGNA.value, strength=round(strength, 1),
        status=classify_status(present, strength), reasons=reasons, weakening_factors=weakening,
        source="BPHS", debug_log=log.lines,
    )]


# ---------------------------------------------------------------------------
# Chandra Mangala Yoga
# ---------------------------------------------------------------------------

@register(YogaDefinition(
    id="chandra_mangala", sanskrit_name="चन्द्र मंगल योग", transliteration="Chandra Mangala Yoga",
    hr_name="Chandra Mangala Yoga",
    hr_description="Mjesec i Mars u istoj rashi (konjunkcija) - donosi poduzetnički duh i financijsku dobit.",
    category="Chandra Yoga", source="Saravali", reference_point=ReferencePoint.LAGNA.value,
    planets_involved=["Mjesec", "Mars"],
))
def _chandra_mangala(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    present = log.check("Mjesec i Mars u istom znaku", chart.same_sign("Mjesec", "Mars"))
    log.result(present)
    house = chart.house_of("Mjesec") if present else 0
    strength = 0.0
    reasons = []
    if present:
        reasons.append(f"Mjesec i Mars su oboje u znaku {chart.positions['Mjesec'].sign} ({house}. kuća od Lagne).")
        vals = [compute_planet_yoga_strength(chart, "Mjesec").total, compute_planet_yoga_strength(chart, "Mars").total]
        strength = sum(vals) / 2
    return [YogaResult(
        id="chandra_mangala", name="Chandra Mangala Yoga", sanskrit_name="चन्द्र मंगल योग",
        transliteration="Chandra Mangala Yoga", present=present, category="Chandra Yoga",
        planets=["Mjesec", "Mars"], houses=[house] if present else [], reference=ReferencePoint.LAGNA.value,
        strength=round(strength, 1), status=classify_status(present, strength), reasons=reasons,
        source="Saravali", debug_log=log.lines,
    )]


# ---------------------------------------------------------------------------
# Amala Yoga (varijanta "od Chandre")
# ---------------------------------------------------------------------------

@register(YogaDefinition(
    id="amala_from_moon", sanskrit_name="अमल योग", transliteration="Amala Yoga (od Chandre)",
    hr_name="Amala Yoga (od Chandre)",
    hr_description="Prirodni dobrotvor SAM (bez drugih planeta) u 10. kući od Mjeseca - trajan ugled.",
    category="Chandra Yoga", source="Phaladipika", reference_point=ReferencePoint.CHANDRA_LAGNA.value,
    variant="Phaladīpikā varijanta (od Chandre; postoji i varijanta od Lagne)",
))
def _amala_from_moon(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    moon_sign = chart.sign_index("Mjesec")
    tenth_occupants = [p for p in CLASSICAL_SEVEN if p != "Mjesec" and house_from(moon_sign, chart.sign_index(p)) == 10]
    log.check("Planeti u 10. od Mjeseca", True, ", ".join(tenth_occupants) or "-")

    benefics_there = [p for p in tenth_occupants if chart.is_natural_benefic(p)]
    alone = len(tenth_occupants) == 1
    present = log.check("Točno jedan prirodni dobrotvor, sam, u 10. od Mjeseca", alone and bool(benefics_there))
    log.result(present)

    strength = 0.0
    reasons = []
    if present:
        reasons.append(f"{benefics_there[0]} je sam u 10. kući od Mjeseca.")
        strength = compute_planet_yoga_strength(chart, benefics_there[0], house_number=10).total

    return [YogaResult(
        id="amala_from_moon", name="Amala Yoga (od Chandre)", sanskrit_name="अमल योग",
        transliteration="Amala Yoga (od Chandre)", present=present, category="Chandra Yoga",
        planets=benefics_there if present else [], houses=[10] if present else [],
        reference=ReferencePoint.CHANDRA_LAGNA.value, strength=round(strength, 1),
        status=classify_status(present, strength), reasons=reasons, source="Phaladipika",
        variant="Phaladīpikā varijanta (od Chandre)", debug_log=log.lines,
    )]
