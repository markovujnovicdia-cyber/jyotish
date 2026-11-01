"""
Graha Drishti IZMEĐU dviju natalnih karata (sinastrija).

Za 7 klasičnih grahe ovo je izravan poziv na core.aspects.compute_graha_drishti
(ISTA geometrija/snaga kao natalna karta - 7./4.+8./5.+9./3.+10., vidi
core/aspects.py) - GEOMETRIJA SE NE DUPLICIRA, samo se primjenjuje
unakrsno (from_sign_index = planeti jedne osobe, to_sign_index = planeti/
Lagna druge osobe).

Rahu/Ketu su OVDJE obrađeni odvojeno od core.aspects (koji za natalnu
kartu podržava samo binarni izbor "kao Saturn") - vidi
core/synastry/config.py za 3 konfigurabilne opcije i obrazloženje. Ovo NE
mijenja postojeće natalne rezultate (core/aspects.py ostaje netaknut).
"""

from typing import Dict, List

from core.aspects import compute_graha_drishti, AspectRelation, ASPECTING_PLANETS, ASPECT_STRENGTH_LABEL
from core.houses import houses_ruled_by_planet
from core.synastry.config import SynastryConfig
from core.synastry.models import GrahaDrishtiContact

# Snaga koju čvorovi (Rahu/Ketu) bacaju na danu kućnu udaljenost (1-12,
# brojano OD čvora), po odabranom konfiguracijskom modu - vidi
# core/synastry/config.py:NODE_ASPECT_MODES za puno obrazloženje.
_NODE_DISTANCE_STRENGTH = {
    "seventh_only": {7: 1.0},
    "5_7_9": {5: 1.0, 7: 1.0, 9: 1.0},
    "none": {},
}


def compute_cross_chart_drishti(
    from_sign_index: Dict[str, int],
    to_sign_index: Dict[str, int],
    config: SynastryConfig,
) -> List[AspectRelation]:
    """
    from_sign_index / to_sign_index: {naziv: sign_index} - SVI planeti
    (uklj. Rahu/Ketu) jedne, odnosno druge natalne karte (to_sign_index
    može uključivati i "Lagna" ili druge posebne točke kao metu).
    """
    classical_from = {p: idx for p, idx in from_sign_index.items() if p in ASPECTING_PLANETS}
    relations = list(compute_graha_drishti(classical_from, to_sign_index, include_rahu_ketu=False))

    node_rule = _NODE_DISTANCE_STRENGTH.get(config.node_aspect_mode, {})
    if node_rule:
        for node in ("Rahu", "Ketu"):
            if node not in from_sign_index:
                continue
            from_idx = from_sign_index[node]
            for to_label, to_idx in to_sign_index.items():
                distance = (to_idx - from_idx) % 12 + 1
                strength = node_rule.get(distance)
                if strength is not None:
                    relations.append(AspectRelation(node, to_label, distance, strength))
    return relations


def build_graha_drishti_contacts(
    source_ctx, target_ctx, source_label: str, target_label: str, config: SynastryConfig,
) -> List[GrahaDrishtiContact]:
    """
    source_ctx/target_ctx: core.natal.NatalContext. Vraća listu kontakata
    gdje planeti IZ source_ctx aspektiraju planete/Lagnu U target_ctx.
    Zove se dvaput (A->B i B->A) za pun uzajamni prikaz.
    """
    from_sign_index = {name: pos.sign_index for name, pos in source_ctx.positions.items()}
    to_sign_index = {name: pos.sign_index for name, pos in target_ctx.positions.items()}
    to_sign_index["Lagna"] = target_ctx.ascendant_sign_index

    relations = compute_cross_chart_drishti(from_sign_index, to_sign_index, config)

    contacts = []
    for rel in relations:
        from_houses = houses_ruled_by_planet(rel.from_planet, source_ctx.ascendant_sign_index)
        to_houses = houses_ruled_by_planet(rel.to_planet, target_ctx.ascendant_sign_index) if rel.to_planet != "Lagna" else []
        contacts.append(GrahaDrishtiContact(
            source_person=source_label,
            target_person=target_label,
            from_planet=rel.from_planet,
            to_planet=rel.to_planet,
            house_distance=rel.house_distance,
            strength=rel.strength,
            strength_label=ASPECT_STRENGTH_LABEL[rel.strength],
            from_planet_houses_own_chart=from_houses,
            to_planet_houses_own_chart=to_houses,
        ))
    return contacts
