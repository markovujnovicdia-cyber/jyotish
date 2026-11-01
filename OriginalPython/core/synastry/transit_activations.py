"""
Tranzitna aktivacija natalne sinastrije (3.1/3.2 u specifikaciji) - "koja
je najvažnija" komponenta prediktivne sinastrije: prepoznavanje kad
tranzit aktivira VEĆ POSTOJEĆU natalnu vezu između dviju osoba.

Model (spec 3.2):
1. pronađi natalne sinastrijske veze (build_natal_synastry_links - koristi
   VEĆ izračunate Graha Drishti kontakte, konjunkcije i nakšatra veze iz
   core/synastry/graha_drishti.py, conjunctions.py, nakshatra_matching.py -
   ne duplicira geometriju)
2. spremi ih kao strukturirane objekte (NatalSynastryLink)
3. za odabrani datum provjeri aktivira li ih neki tranzit
   (compute_link_activations)
4. izračunaj jačinu aktivacije (core.synastry.config.TRANSIT_SPEED_WEIGHT)
5. tekstualno tumačenje (core/synastry/interpretation.py stil, ovdje kratko)

Vrste aktivacije (svih 7 iz specifikacije): konjunkcija, Graha Drishti,
isti znak, ista nakšatra, tranzit PREKO vladara nakšatre (transitirajući
planet JEST vladar nakšatre veze), tranzit preko dispozitora (transitirajući
planet JEST vladar znaka veze), D9 aktivacija (D9 znak transita = D9 znak
veze). Graha Drishti provjera PONOVNO KORISTI core.synastry.graha_drishti.
compute_cross_chart_drishti (već generička - radi s bilo kojim sign_index
mapama, ovdje: tranzitni planeti -> "sidrišta" veza).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from core.constants import RASHI, RASHI_LORD
from core.nakshatra import get_nakshatra
from core.varga import d9_navamsha_sign_index
from core.natal import NatalContext
from core.ephemeris import PlanetPosition
from core.synastry.config import SynastryConfig, TRANSIT_SPEED_WEIGHT
from core.synastry.graha_drishti import compute_cross_chart_drishti
from core.synastry.models import (
    NatalSynastryLink, TransitActivation, GrahaDrishtiContact, ConjunctionContact,
    NakshatraSynastryResult,
)

_ACTIVATION_TYPE_LABELS = {
    "konjunkcija": "tranzitna konjunkcija",
    "graha_drishti": "tranzitni Graha Drishti",
    "isti_znak": "tranzit preko znaka veze",
    "ista_nakshatra": "tranzit preko nakšatre veze",
    "vladar_nakshatre": "tranzit vladara nakšatre veze",
    "dispozitor": "tranzit dispozitora veze",
    "d9_aktivacija": "aktivacija u D9",
}


def _resolve_longitude(ctx_a: NatalContext, ctx_b: NatalContext, person_label: str, object_name: str) -> Optional[float]:
    ctx = ctx_a if person_label == "A" else ctx_b
    if object_name == "Lagna":
        return ctx.ascendant_longitude
    if object_name in ctx.positions:
        return ctx.positions[object_name].longitude
    return None


def build_natal_synastry_links(
    ctx_a: NatalContext, ctx_b: NatalContext,
    drishti_contacts: List[GrahaDrishtiContact],
    conjunctions: List[ConjunctionContact],
    nakshatra_result: NakshatraSynastryResult,
) -> List[NatalSynastryLink]:
    links: List[NatalSynastryLink] = []

    for i, c in enumerate(drishti_contacts):
        lon_a = _resolve_longitude(ctx_a, ctx_b, c.source_person, c.from_planet)
        lon_b = _resolve_longitude(ctx_a, ctx_b, c.target_person, c.to_planet)
        if lon_a is None or lon_b is None:
            continue
        links.append(NatalSynastryLink(
            link_id=f"drishti:{i}", link_type="graha_drishti",
            person_a_object=f"{c.from_planet} ({c.source_person})",
            person_b_object=f"{c.to_planet} ({c.target_person})",
            anchor_longitude_a=lon_a, anchor_longitude_b=lon_b,
            description=c.short_interpretation,
        ))

    for i, c in enumerate(conjunctions):
        links.append(NatalSynastryLink(
            link_id=f"conj:{i}", link_type="conjunction",
            person_a_object=f"{c.person_a_object} (A)", person_b_object=f"{c.person_b_object} (B)",
            anchor_longitude_a=c.longitude_a, anchor_longitude_b=c.longitude_b,
            description=c.short_interpretation,
        ))

    for i, link in enumerate(nakshatra_result.cross_links):
        if link.relation_type not in ("same_nakshatra", "same_pada"):
            continue
        point_a, person_a = link.source_label.rsplit(" (", 1)
        point_b, person_b = link.target_label.rsplit(" (", 1)
        person_a, person_b = person_a.rstrip(")"), person_b.rstrip(")")
        profiles_a = nakshatra_result.profiles_a if person_a == "A" else nakshatra_result.profiles_b
        profiles_b = nakshatra_result.profiles_a if person_b == "A" else nakshatra_result.profiles_b
        if point_a not in profiles_a or point_b not in profiles_b:
            continue
        links.append(NatalSynastryLink(
            link_id=f"nakshatra:{i}", link_type="nakshatra",
            person_a_object=link.source_label, person_b_object=link.target_label,
            anchor_longitude_a=profiles_a[point_a].longitude, anchor_longitude_b=profiles_b[point_b].longitude,
            description=link.detail,
        ))

    return links


def build_transit_sign_and_longitude_maps(transit_positions: Dict[str, PlanetPosition]):
    sign_index = {p: pos.sign_index for p, pos in transit_positions.items()}
    longitude = {p: pos.longitude for p, pos in transit_positions.items()}
    return sign_index, longitude


def _angular_distance(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def compute_link_activations(
    links: List[NatalSynastryLink],
    transit_positions: Dict[str, PlanetPosition],
    config: SynastryConfig,
) -> List[TransitActivation]:
    if not links:
        return []

    transit_sign_index, transit_longitude = build_transit_sign_and_longitude_maps(transit_positions)

    # Graha Drishti u JEDNOM prolazu preko svih veza - ponovno koristi
    # core.synastry.graha_drishti.compute_cross_chart_drishti (generička),
    # bez ponovne implementacije geometrije aspekta.
    to_sign_index: Dict[str, int] = {}
    for link in links:
        to_sign_index[f"{link.link_id}:a"] = int(link.anchor_longitude_a % 360.0 // 30)
        to_sign_index[f"{link.link_id}:b"] = int(link.anchor_longitude_b % 360.0 // 30)
    drishti_relations = compute_cross_chart_drishti(transit_sign_index, to_sign_index, config)
    drishti_hits: Dict[str, set] = {}
    for rel in drishti_relations:
        # rsplit (ne split) jer link.link_id sam po sebi može sadržavati ":"
        # (npr. "drishti:0") - samo ZADNJI ":a"/":b" sufiks treba odsjeći.
        link_id = rel.to_planet.rsplit(":", 1)[0]
        drishti_hits.setdefault(link_id, set()).add(rel.from_planet)

    activations: List[TransitActivation] = []
    for link in links:
        anchor_sign_a = int(link.anchor_longitude_a % 360.0 // 30)
        anchor_sign_b = int(link.anchor_longitude_b % 360.0 // 30)
        anchor_nak_a = get_nakshatra(link.anchor_longitude_a)
        anchor_nak_b = get_nakshatra(link.anchor_longitude_b)
        anchor_d9_a = d9_navamsha_sign_index(link.anchor_longitude_a)
        anchor_d9_b = d9_navamsha_sign_index(link.anchor_longitude_b)
        dispositor_a = RASHI_LORD[RASHI[anchor_sign_a]]
        dispositor_b = RASHI_LORD[RASHI[anchor_sign_b]]

        for transit_planet, t_lon in transit_longitude.items():
            types: List[str] = []
            orb = config.orb_for(transit_planet)
            if _angular_distance(t_lon, link.anchor_longitude_a) <= orb or _angular_distance(t_lon, link.anchor_longitude_b) <= orb:
                types.append("konjunkcija")
            if transit_planet in drishti_hits.get(link.link_id, set()):
                types.append("graha_drishti")
            if transit_sign_index[transit_planet] in (anchor_sign_a, anchor_sign_b):
                types.append("isti_znak")
            t_nak = get_nakshatra(t_lon)
            if t_nak.index in (anchor_nak_a.index, anchor_nak_b.index):
                types.append("ista_nakshatra")
            if transit_planet in (anchor_nak_a.lord, anchor_nak_b.lord):
                types.append("vladar_nakshatre")
            if transit_planet in (dispositor_a, dispositor_b):
                types.append("dispozitor")
            t_d9 = d9_navamsha_sign_index(t_lon)
            if t_d9 in (anchor_d9_a, anchor_d9_b):
                types.append("d9_aktivacija")

            if not types:
                continue

            base_weight = TRANSIT_SPEED_WEIGHT.get(transit_planet, 0.3)
            strength = round(base_weight * min(1.0, 0.5 + 0.15 * len(types)), 3)
            type_labels = ", ".join(_ACTIVATION_TYPE_LABELS[t] for t in types)
            interpretation = (
                f"Tranzitni {transit_planet} aktivira natalnu vezu {link.person_a_object} — "
                f"{link.person_b_object} ({type_labels}). Izvorna veza: {link.description}"
            )
            activations.append(TransitActivation(
                transit_planet=transit_planet, link=link, activation_types=types,
                strength=strength, is_slow_planet=transit_planet in TRANSIT_SPEED_WEIGHT and TRANSIT_SPEED_WEIGHT[transit_planet] >= 1.0,
                interpretation=interpretation,
            ))

    activations.sort(key=lambda a: -a.strength)
    return activations
