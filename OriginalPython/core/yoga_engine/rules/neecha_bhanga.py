"""
Neecha Bhanga Yoga Engine (zahtjev #13) - za SVAKI debilitirani (pad) planet
provjerava se SVIH 5 klasičnih uvjeta poništenja (BPHS, standardna,
naširoko citirana lista - nije "moderno pojednostavljeno pravilo"):

  1. Vladar (dispozitor) znaka pada je u kendri (1/4/7/10) od Lagne ILI od Mjeseca.
  2. Vladar znaka UZVIŠENJA (tog planeta) je u kendri od Lagne ILI od Mjeseca.
  3. Debilitirani planet je u konjunkciji ILI aspektu sa svojim vladarom (dispozitorom).
  4. Debilitirani planet je u konjunkciji ILI aspektu s planetom koji se
     UZVIŠUJE baš u znaku ove debilitacije.
  5. Vladar (dispozitor) je SAM uzvišen (u svom znaku uzvišenja).

Rezultat NIJE binaran - zahtjev #13 eksplicitno traži razlikovanje 4
razine: "Neecha planet bez poništenja" (0 uvjeta), "djelomični Neecha
Bhanga" (1 uvjet), "snažni Neecha Bhanga" (2+ uvjeta), "Neecha Bhanga Raja
Yoga" (2+ uvjeta I planet dodatno sudjeluje u Raja Yogi - sam je Yogakaraka
ili je u odnosu s vladarom kendre/trikone). NIJE svako poništenje
automatski Raja Yoga (izričita napomena u zahtjevu #13).
"""

from typing import List

from core.yoga_engine.context import ChartContext, CLASSICAL_SEVEN, KENDRA_HOUSES, is_kendra, house_from
from core.yoga_engine.models import DebugLog, YogaDefinition, YogaResult, ReferencePoint
from core.yoga_engine.registry import register
from core.yoga_engine.rules.raja import find_yogakaraka, _relation_types
from core.yoga_engine.strength import compute_planet_yoga_strength
from core.planet_strength import EXALTATION
from core.constants import RASHI, RASHI_LORD


def _debilitation_sign_index(planet: str) -> int:
    exalt_sign, _ = EXALTATION[planet]
    return (RASHI.index(exalt_sign) + 6) % 12


def _exaltation_sign_index(planet: str) -> int:
    exalt_sign, _ = EXALTATION[planet]
    return RASHI.index(exalt_sign)


def _planet_exalted_in(sign_index: int):
    """Koji planet (ako ijedan) ima uzvišenje baš u zadanom znaku."""
    for p, (sign_name, _deg) in EXALTATION.items():
        if RASHI.index(sign_name) == sign_index:
            return p
    return None


def _in_kendra_from_lagna_or_moon(chart: ChartContext, planet: str) -> bool:
    """
    NAPOMENA (ispravak): kad je 'planet' baš Mjesec, "kendra OD MJESECA"
    provjera se namjerno PRESKAČE - udaljenost bilo koje točke od SAME
    SEBE je uvijek 0 (1. kuća = kendra), pa bi taj dio inače uvijek
    trivijalno vratio True kad god je dispozitor/vladar uzvišenja baš
    Mjesec (npr. Jupiterov/Marsov slučaj - Mjesec vlada Rakom, koji je
    Jupiterov znak uzvišenja I Marsov znak pada) - to bi umjetno naduvalo
    broj zadovoljenih uvjeta poništenja bez stvarnog astrološkog razloga.
    """
    from_lagna = is_kendra(chart.house_of(planet))
    if planet == "Mjesec":
        return from_lagna
    from_moon = is_kendra(house_from(chart.sign_index("Mjesec"), chart.sign_index(planet)))
    return from_lagna or from_moon


def analyze_neecha_bhanga(chart: ChartContext, planet: str) -> dict:
    debil_sign = _debilitation_sign_index(planet)
    dispositor = RASHI_LORD[RASHI[debil_sign]]
    exalt_sign = _exaltation_sign_index(planet)
    exalt_sign_lord = RASHI_LORD[RASHI[exalt_sign]]
    exalt_planet_here = _planet_exalted_in(debil_sign)

    conditions = []
    c1 = _in_kendra_from_lagna_or_moon(chart, dispositor)
    conditions.append(("Vladar znaka pada (dispozitor) u kendri od Lagne/Mjeseca", c1,
                        f"{dispositor} je vladar znaka {RASHI[debil_sign]}."))
    c2 = _in_kendra_from_lagna_or_moon(chart, exalt_sign_lord)
    conditions.append(("Vladar znaka uzvišenja u kendri od Lagne/Mjeseca", c2,
                        f"{exalt_sign_lord} vlada znakom uzvišenja ({RASHI[exalt_sign]})."))
    c3 = chart.same_sign(planet, dispositor) or chart.planet_aspects(dispositor, planet)
    conditions.append((f"{planet} u konjunkciji/aspektu sa svojim vladarom ({dispositor})", c3, ""))
    c4 = False
    if exalt_planet_here and exalt_planet_here != planet:
        c4 = chart.same_sign(planet, exalt_planet_here) or chart.planet_aspects(exalt_planet_here, planet)
    conditions.append((
        f"{planet} u konjunkciji/aspektu s planetom koji se uzvišuje u znaku njegovog pada"
        f"{f' ({exalt_planet_here})' if exalt_planet_here else ' (nema takvog planeta među 7 klasičnih)'}",
        c4, "",
    ))
    c5 = chart.is_exalted(dispositor)
    conditions.append((f"Vladar ({dispositor}) je sam uzvišen", c5, ""))

    met = sum(1 for _, ok, _ in conditions if ok)
    return {"dispositor": dispositor, "conditions": conditions, "met": met}


@register(YogaDefinition(
    id="neecha_bhanga", sanskrit_name="नीच भंग योग", transliteration="Neecha Bhanga Yoga",
    hr_name="Neecha Bhanga (poništenje pada)",
    hr_description="Za svaki debilitirani planet provjerava se 5 klasičnih uvjeta poništenja pada.",
    category="Neecha Bhanga", source="BPHS", reference_point=ReferencePoint.LAGNA.value,
))
def _neecha_bhanga_rule(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    debilitated = [p for p in CLASSICAL_SEVEN if chart.is_debilitated(p)]
    log.note(f"Debilitirani planeti: {debilitated or 'nijedan'}")

    if not debilitated:
        log.result(False)
        return [YogaResult(
            id="neecha_bhanga", name="Neecha Bhanga (poništenje pada)", sanskrit_name="नीच भंग योग",
            transliteration="Neecha Bhanga Yoga", present=False, category="Neecha Bhanga", planets=[], houses=[],
            reference=ReferencePoint.LAGNA.value, strength=0.0, status="nije primjenjivo",
            reasons=["Nijedan od 7 klasičnih planeta nije u padu u ovoj karti."], source="BPHS", debug_log=log.lines,
        )]

    yogakaraka_planets = {e["planet"] for e in find_yogakaraka(chart)}
    kendra_trikona_lords = {chart.house_lord(h) for h in KENDRA_HOUSES | {5, 9}}

    results = []
    for planet in debilitated:
        analysis = analyze_neecha_bhanga(chart, planet)
        met = analysis["met"]
        for label, ok, extra in analysis["conditions"]:
            log.check(f"{planet}: {label}", ok, extra)

        if met == 0:
            status = "Neecha planet bez poništenja"
            present = False
        elif met == 1:
            status = "djelomični Neecha Bhanga"
            present = True
        else:
            status = "snažni Neecha Bhanga"
            present = True
            is_raja_context = (
                planet in yogakaraka_planets
                or any(_relation_types(chart, planet, lord) for lord in kendra_trikona_lords if lord != planet)
            )
            if is_raja_context:
                status = "Neecha Bhanga Raja Yoga"

        house = chart.house_of(planet)
        b = compute_planet_yoga_strength(chart, planet, house_number=house)
        strength = b.total if present else 0.0
        reasons = [f"{planet} je u padu u znaku {chart.positions[planet].sign}."]
        reasons += [f"{label}." for label, ok, _ in analysis["conditions"] if ok]
        if status == "Neecha Bhanga Raja Yoga":
            reasons.append(f"{planet} dodatno sudjeluje u Raja Yogi (Yogakaraka ili odnos s vladarom kendre/trikone).")

        results.append(YogaResult(
            id="neecha_bhanga", name=f"{status}: {planet}", sanskrit_name="नीच भंग योग",
            transliteration=f"Neecha Bhanga ({planet})", present=present, category="Neecha Bhanga",
            planets=[planet], houses=[house], reference=ReferencePoint.LAGNA.value, strength=round(strength, 1),
            status=status, reasons=reasons,
            cancellation_factors=[f"{label}" for label, ok, _ in analysis["conditions"] if ok],
            source="BPHS", debug_log=list(log.lines), instance_label=planet,
        ))

    log.result(any(r.present for r in results))
    return results
