"""
Pancha Mahapurusha Yoge (BPHS, poglavlje o Panchamahapurusha Yogama).

Zajedničko klasično pravilo za svih pet (Ruchaka/Bhadra/Hamsa/Malavya/Sasa):
  1. Planet je u kendri (1./4./7./10.) OD LAGNE.
  2. Planet je u vlastitom znaku, Moolatrikoni ili uzvišenju.

Oba uvjeta su OBAVEZNA (zahtjev #9) - ako nisu ispunjena, yoga NIJE
prisutna (nema "djelomične" Mahapurusha yoge). Kombustija/aspekt malefika/
retrogradnost/Navamsha dignitet NE brišu yogu nego mijenjaju njezinu
snagu/status (izračunato preko core/yoga_engine/strength.py).
"""

from typing import List

from core.yoga_engine.context import ChartContext, is_kendra
from core.yoga_engine.models import DebugLog, YogaDefinition, YogaResult, ReferencePoint
from core.yoga_engine.registry import register
from core.yoga_engine.strength import compute_planet_yoga_strength, classify_status

_MAHAPURUSHA = [
    ("ruchaka", "रुचक योग", "Ruchaka Yoga", "Mars"),
    ("bhadra", "भद्र योग", "Bhadra Yoga", "Merkur"),
    ("hamsa", "हंस योग", "Hamsa Yoga", "Jupiter"),
    ("malavya", "मालव्य योग", "Malavya Yoga", "Venera"),
    ("sasa", "शश योग", "Sasa Yoga", "Saturn"),
]


def _make_rule(yoga_id: str, planet: str):
    def rule(chart: ChartContext) -> List[YogaResult]:
        log = DebugLog()
        house = chart.house_of(planet)
        in_kendra = log.check(f"{planet} u kendri (1/4/7/10) od Lagne", is_kendra(house), f"kuća {house}")

        own = chart.is_own_sign(planet)
        exalted = chart.is_exalted(planet)
        moolatrikona = chart.is_moolatrikona(planet)
        good_dignity = log.check(
            f"{planet} u vlastitom/Moolatrikona/uzvišenom znaku", own or exalted or moolatrikona,
            "uzvišen" if exalted else ("Moolatrikona" if moolatrikona else ("vlastiti" if own else chart.dignity(planet))),
        )

        present = in_kendra and good_dignity
        log.result(present)

        reasons: List[str] = []
        strength_val = 0.0
        weakening: List[str] = []
        if present:
            reasons.append(f"{planet} je u {house}. kući (kendra) od Lagne.")
            dignity_label = "uzvišenju" if exalted else ("Moolatrikoni" if moolatrikona else "vlastitom znaku")
            reasons.append(f"{planet} je u {dignity_label} ({chart.positions[planet].sign}).")
            b = compute_planet_yoga_strength(chart, planet, house_number=house)
            strength_val = b.total
            log.lines.extend(b.as_reasons())
            if chart.is_combust(planet):
                weakening.append(f"{planet} je kombust - slabi yogu.")
            malefics_touch = [
                p for p in ["Sunce", "Mars", "Saturn", "Rahu", "Ketu"]
                if p != planet and (chart.same_sign(p, planet) or chart.planet_aspects(p, planet, include_rahu_ketu=True))
            ]
            if malefics_touch:
                weakening.append(f"Zlotvori u konjunkciji/aspektu: {', '.join(malefics_touch)}.")

        return [YogaResult(
            id=yoga_id,
            name=YOGA_REGISTRY_DEFS[yoga_id].hr_name,
            sanskrit_name=YOGA_REGISTRY_DEFS[yoga_id].sanskrit_name,
            transliteration=YOGA_REGISTRY_DEFS[yoga_id].transliteration,
            present=present,
            category="Pancha Mahapurusha Yoga",
            planets=[planet],
            houses=[house],
            reference=ReferencePoint.LAGNA.value,
            strength=round(strength_val, 1),
            status=classify_status(present, strength_val),
            reasons=reasons,
            weakening_factors=weakening,
            source="BPHS",
            debug_log=log.lines,
        )]
    return rule


YOGA_REGISTRY_DEFS = {}
for _id, _sanskrit, _translit, _planet in _MAHAPURUSHA:
    _definition = YogaDefinition(
        id=_id,
        sanskrit_name=_sanskrit,
        transliteration=_translit,
        hr_name=_translit,
        hr_description=(
            f"{_planet} u kendri od Lagne, u vlastitom znaku/Moolatrikoni/uzvišenju - "
            f"jedna od 5 klasičnih Mahapurusha yoga."
        ),
        category="Pancha Mahapurusha Yoga",
        source="BPHS",
        reference_point=ReferencePoint.LAGNA.value,
        planets_involved=[_planet],
    )
    YOGA_REGISTRY_DEFS[_id] = _definition
    register(_definition)(_make_rule(_id, _planet))
