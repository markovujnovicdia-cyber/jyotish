"""
Viparita Raja Yoge (zahtjev #14) - BPHS. Zajedničko klasično načelo: vladar
dusthane (6./8./12.) SMJEŠTEN u (bilo koju od) dusthana kuća stvara
paradoksalno povoljan ishod (loše kuće "zarobe" jedna drugu, umjesto da
štete povoljnim kućama).

  - Harsha Yoga: vladar 6. kuće je u 6./8./12. kući.
  - Sarala Yoga: vladar 8. kuće je u 6./8./12. kući.
  - Vimala Yoga: vladar 12. kuće je u 6./8./12. kući.

"Čistoća" yoge (zahtjev #14 - "koliko je čista ili miješana") ovisi o tome
ima li dusthana-vladar DODATNO vlasništvo nad povoljnom kućom (kendra/
trikona) - ako da, yoga je miješana (dvojaka priroda), ako ne, čista.
"""

from typing import List

from core.houses import houses_ruled_by_planet
from core.yoga_engine.context import ChartContext, DUSTHANA_HOUSES, KENDRA_HOUSES, TRIKONA_HOUSES
from core.yoga_engine.models import DebugLog, YogaDefinition, YogaResult, ReferencePoint
from core.yoga_engine.registry import register
from core.yoga_engine.strength import compute_planet_yoga_strength, classify_status

_VIPARITA = [
    ("harsha_yoga", "Harsha Yoga", "हर्ष योग", 6),
    ("sarala_yoga", "Sarala Yoga", "सरल योग", 8),
    ("vimala_yoga", "Vimala Yoga", "विमल योग", 12),
]


def _make_rule(yoga_id: str, dusthana_house: int):
    def rule(chart: ChartContext) -> List[YogaResult]:
        log = DebugLog()
        lord = chart.house_lord(dusthana_house)
        house_now = chart.house_of(lord)
        present = log.check(f"Vladar {dusthana_house}. ({lord}) je u dusthani (6/8/12)", house_now in DUSTHANA_HOUSES,
                             f"trenutno u {house_now}. kući")
        log.result(present)

        reasons: List[str] = []
        mixed_note = ""
        strength = 0.0
        favorable_houses: List[int] = []
        if present:
            reasons.append(f"Vladar {dusthana_house}. kuće ({lord}) je smješten u {house_now}. kući (dusthana).")
            ruled = set(houses_ruled_by_planet(lord, chart.ascendant_sign_index))
            favorable_houses = sorted(ruled & (KENDRA_HOUSES | TRIKONA_HOUSES))
            if favorable_houses:
                mixed_note = (
                    f"{lord} DODATNO vlada povoljnom kućom ({', '.join(f'{h}.' for h in favorable_houses)}) - "
                    f"yoga je MIJEŠANE (dvojake) prirode, ne čista."
                )
            else:
                mixed_note = f"{lord} ne vlada nijednom kendra/trikona kućom - yoga je ČISTA."
            reasons.append(mixed_note)
            b = compute_planet_yoga_strength(chart, lord, house_number=house_now)
            strength = b.total

        return [YogaResult(
            id=yoga_id, name=_VIPARITA_META[yoga_id][0], sanskrit_name=_VIPARITA_META[yoga_id][1],
            transliteration=_VIPARITA_META[yoga_id][0], present=present, category="Viparita Raja Yoga",
            planets=[lord] if present else [], houses=[dusthana_house, house_now] if present else [],
            reference=ReferencePoint.LAGNA.value, strength=round(strength, 1), status=classify_status(present, strength),
            reasons=reasons, source="BPHS", debug_log=log.lines,
            variant="miješana (dvojaka)" if favorable_houses else ("čista" if present else ""),
        )]
    return rule


_VIPARITA_META = {yid: (name, sanskrit) for yid, name, sanskrit, _ in _VIPARITA}

for _id, _name, _sanskrit, _house in _VIPARITA:
    register(YogaDefinition(
        id=_id, sanskrit_name=_sanskrit, transliteration=_name, hr_name=_name,
        hr_description=f"Vladar {_house}. kuće smješten u 6./8./12. kući (Viparita Raja Yoga).",
        category="Viparita Raja Yoga", source="BPHS", reference_point=ReferencePoint.LAGNA.value,
    ))(_make_rule(_id, _house))
