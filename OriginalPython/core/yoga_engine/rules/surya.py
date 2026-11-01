"""
Surya (Sunčeve) Yoge - BPHS.

Vesi/Vosi/Ubhayachari: ISKLJUČUJU Mjesec (klasično pravilo - "grah" ovdje
znači bilo koji od preostalih 6 klasičnih planeta osim Mjeseca, analogno
tome kako Sunapha/Anapha isključuju Sunce, vidi core/yoga_engine/rules/chandra.py).

Budha-Aditya: Sunce+Merkur konjunkcija. Zahtjev #11 - NE proglašavati
automatski "jaku" yogu samo zbog konjunkcije: prikazuje se udaljenost
Merkura od Sunca, combustion status, dignitet oba planeta, a snaga se
IZVODI iz toga (formation ostaje True čim su u istom znaku - to je i
doslovna klasična definicija - ali "koliko je jaka" ovisi o gornjem).
"""

from typing import List

from core.yoga_engine.context import ChartContext, house_from, CLASSICAL_SEVEN
from core.yoga_engine.models import DebugLog, YogaDefinition, YogaResult, ReferencePoint
from core.yoga_engine.registry import register, select_from_group
from core.yoga_engine.strength import compute_planet_yoga_strength, classify_status

_OTHER_SIX_FROM_SUN = ["Mars", "Merkur", "Jupiter", "Venera", "Saturn", "Mjesec"]


def _planets_in_house_from_sun_excluding_moon(chart: ChartContext, house: int) -> List[str]:
    sun_sign = chart.sign_index("Sunce")
    pool = ["Mars", "Merkur", "Jupiter", "Venera", "Saturn"]
    return [p for p in pool if house_from(sun_sign, chart.sign_index(p)) == house]


def _vesi_vosi_ubhayachari(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    second = _planets_in_house_from_sun_excluding_moon(chart, 2)
    twelfth = _planets_in_house_from_sun_excluding_moon(chart, 12)
    log.check("Planet(i) osim Mjeseca u 2. od Sunca", bool(second), ", ".join(second) or "-")
    log.check("Planet(i) osim Mjeseca u 12. od Sunca", bool(twelfth), ", ".join(twelfth) or "-")

    has_vesi = bool(second)
    has_vosi = bool(twelfth)
    has_ubhayachari = has_vesi and has_vosi

    def _avg_strength(planets: List[str]) -> float:
        if not planets:
            return 0.0
        return sum(compute_planet_yoga_strength(chart, p).total for p in planets) / len(planets)

    results = [
        YogaResult(
            id="vesi", name="Vesi Yoga", sanskrit_name="वेसि योग", transliteration="Vesi Yoga",
            present=has_vesi, category="Surya Yoga", planets=second, houses=[2] if has_vesi else [],
            reference=ReferencePoint.SURYA.value, strength=round(_avg_strength(second), 1),
            status=classify_status(has_vesi, _avg_strength(second)),
            reasons=[f"{p} je u 2. od Sunca (bez Mjeseca)." for p in second],
            source="BPHS", debug_log=log.lines,
        ),
        YogaResult(
            id="vosi", name="Vosi Yoga", sanskrit_name="वोसि योग", transliteration="Vosi Yoga",
            present=has_vosi, category="Surya Yoga", planets=twelfth, houses=[12] if has_vosi else [],
            reference=ReferencePoint.SURYA.value, strength=round(_avg_strength(twelfth), 1),
            status=classify_status(has_vosi, _avg_strength(twelfth)),
            reasons=[f"{p} je u 12. od Sunca (bez Mjeseca)." for p in twelfth],
            source="BPHS", debug_log=log.lines,
        ),
        YogaResult(
            id="ubhayachari", name="Ubhayachari Yoga", sanskrit_name="उभयचरी योग", transliteration="Ubhayachari Yoga",
            present=has_ubhayachari, category="Surya Yoga", planets=second + twelfth if has_ubhayachari else [],
            houses=[2, 12] if has_ubhayachari else [], reference=ReferencePoint.SURYA.value,
            strength=round(_avg_strength(second + twelfth), 1) if has_ubhayachari else 0.0,
            status=classify_status(has_ubhayachari, _avg_strength(second + twelfth) if has_ubhayachari else 0.0),
            reasons=(
                [f"{p} je u 2. od Sunca." for p in second] + [f"{p} je u 12. od Sunca." for p in twelfth]
            ) if has_ubhayachari else [],
            source="BPHS", debug_log=log.lines,
        ),
    ]
    return results


for _id, _name, _sanskrit in [
    ("vesi", "Vesi Yoga", "वेसि योग"),
    ("vosi", "Vosi Yoga", "वोसि योग"),
    ("ubhayachari", "Ubhayachari Yoga", "उभयचरी योग"),
]:
    register(YogaDefinition(
        id=_id, sanskrit_name=_sanskrit, transliteration=_name, hr_name=_name,
        hr_description="Planet(i) osim Mjeseca u 2. i/ili 12. kući od Sunca (BPHS).",
        category="Surya Yoga", source="BPHS", reference_point=ReferencePoint.SURYA.value,
    ))(select_from_group(_vesi_vosi_ubhayachari, _id))


@register(YogaDefinition(
    id="budha_aditya", sanskrit_name="बुध आदित्य योग", transliteration="Budha-Aditya Yoga",
    hr_name="Budha-Aditya Yoga",
    hr_description=(
        "Sunce i Merkur u istom znaku (konjunkcija) - donosi intelekt i analitičke "
        "sposobnosti. Snaga OVISI o kombustiji Merkura i dignitetu oba planeta - "
        "obična konjunkcija (Merkur gotovo uvijek kombust uz Sunce) NIJE automatski jaka yoga."
    ),
    category="Surya Yoga", source="BPHS", reference_point=ReferencePoint.LAGNA.value,
    planets_involved=["Sunce", "Merkur"],
))
def _budha_aditya(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    present = log.check("Sunce i Merkur u istom znaku", chart.same_sign("Sunce", "Merkur"))
    log.result(present)

    reasons: List[str] = []
    weakening: List[str] = []
    strength = 0.0
    house = 0
    if present:
        house = chart.house_of("Sunce")
        distance = abs((chart.longitude("Merkur") - chart.longitude("Sunce") + 180) % 360 - 180)
        combust = chart.is_combust("Merkur")
        reasons.append(f"Sunce i Merkur su oboje u znaku {chart.positions['Sunce'].sign} ({house}. kuća).")
        reasons.append(f"Udaljenost Merkura od Sunca: {distance:.2f}°.")
        reasons.append(f"Dignitet Sunca: {chart.dignity('Sunce')}, Merkura: {chart.dignity('Merkur')}.")
        if combust:
            weakening.append(f"Merkur je kombust (udaljenost {distance:.2f}° od Sunca) - slabi analitičku jasnoću yoge.")
        else:
            reasons.append("Merkur NIJE kombust unatoč konjunkciji (rijetka, jača varijanta).")
        b = compute_planet_yoga_strength(chart, "Merkur", house_number=house)
        strength = b.total

    return [YogaResult(
        id="budha_aditya", name="Budha-Aditya Yoga", sanskrit_name="बुध आदित्य योग",
        transliteration="Budha-Aditya Yoga", present=present, category="Surya Yoga",
        planets=["Sunce", "Merkur"] if present else [], houses=[house] if present else [],
        reference=ReferencePoint.LAGNA.value, strength=round(strength, 1),
        status=classify_status(present, strength), reasons=reasons, weakening_factors=weakening,
        source="BPHS", debug_log=log.lines,
    )]
