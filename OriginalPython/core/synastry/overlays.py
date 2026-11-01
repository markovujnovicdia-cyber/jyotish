"""
Kućni overlay (D1 sinastrija) - gdje padaju planeti jedne osobe u kućama
druge osobe, i obrnuto.

Koristi ISTI Whole Sign (core.houses.whole_sign_house) i Bhava Chalit
(core.houses.bhava_chalit_house) izračun kao natalna karta - BEZ ikakve
promjene metode. Dostojanstvo (core.planet_strength.compute_dignity) i
prirodno prijateljstvo/neprijateljstvo (NATURAL_FRIENDS/NATURAL_ENEMIES) su
također ponovno iskorišteni, ne duplicirani.

NAPOMENA o dosegu (Faza 1): "funkcionalna priroda planeta za ascendent
osobe A" (functional_nature - je li planet funkcionalni dobrotvor/zlotvor
za DANI ascendent) i puna analiza "kako A djeluje / kako B doživljava"
ostavljene su kao tekstualna interpretacija u core/synastry/interpretation.py
i ui/pages_synastry.py (dvije odvojene tablice + presjek), a ne kao dodatno
polje ovdje - polje functional_nature je rezervirano (None) za kasniju fazu.
"""

from typing import List

from core.constants import RASHI, RASHI_LORD, PLANET_ORDER, NAKSHATRA_LORDS
from core.houses import whole_sign_house, bhava_chalit_house
from core.nakshatra import get_nakshatra
from core.planet_strength import compute_dignity, NATURAL_FRIENDS, NATURAL_ENEMIES
from core.natal import NatalContext
from core.synastry.models import HouseOverlayRow

# Kuće koje specifikacija izričito traži da se posebno označe (sve OSIM 3. i 6.)
SIGNIFICANT_HOUSES = {1, 2, 4, 5, 7, 8, 9, 10, 11, 12}


def _lord_relation(planet: str, house_lord: str) -> str:
    if planet == house_lord:
        return "planet je i posjetitelj i vladar te kuće (najizravnija veza)"
    if house_lord in NATURAL_FRIENDS.get(planet, set()):
        return "prirodno prijateljski odnos s vladarom kuće"
    if house_lord in NATURAL_ENEMIES.get(planet, set()):
        return "prirodno neprijateljski odnos s vladarom kuće"
    return "neutralan (ni prijateljski ni neprijateljski) odnos s vladarom kuće"


def compute_house_overlay(
    source_ctx: NatalContext, target_ctx: NatalContext,
    source_label: str, target_label: str,
) -> List[HouseOverlayRow]:
    """
    Planeti iz source_ctx (Faza 1: sve klasične 9 grahe) preslikani u kuće
    target_ctx karte. Zove se dvaput (A->B i B->A) da se dobiju oba smjera.
    """
    rows: List[HouseOverlayRow] = []
    for planet in PLANET_ORDER:
        pos = source_ctx.positions[planet]
        ws_house = whole_sign_house(pos.sign_index, target_ctx.ascendant_sign_index)
        bc_house = bhava_chalit_house(pos.longitude, target_ctx.ascendant_longitude)
        nak = get_nakshatra(pos.longitude)
        sign_lord = RASHI_LORD[pos.sign]
        dignity, _ = compute_dignity(planet, pos.sign_index)

        target_house_sign_index = (target_ctx.ascendant_sign_index + ws_house - 1) % 12
        target_house_lord = RASHI_LORD[RASHI[target_house_sign_index]]

        rows.append(HouseOverlayRow(
            source_person=source_label,
            target_person=target_label,
            planet=planet,
            sign=pos.sign,
            whole_sign_house=ws_house,
            bhava_chalit_house=bc_house if bc_house != ws_house else None,
            nakshatra=nak.name,
            pada=nak.pada,
            sign_lord=sign_lord,
            nakshatra_lord=NAKSHATRA_LORDS[nak.index],
            dignity=dignity,
            is_significant_house=ws_house in SIGNIFICANT_HOUSES,
            target_house_lord=target_house_lord,
            target_house_lord_relation=_lord_relation(planet, target_house_lord),
            label=f"{planet} ({source_label}) → {ws_house}. kuća ({target_label})",
        ))
    return rows


def find_mutual_emphasis(
    overlay_source_to_target: List[HouseOverlayRow],
    overlay_target_to_source: List[HouseOverlayRow],
) -> List[str]:
    """
    Prepoznaje kad se ISTI planet pojavljuje u relevantnoj kući u OBA
    smjera (npr. Venera osobe A u 7. kući osobe B, I Venera osobe B u
    relevantnoj kući osobe A) - naznaka uzajamnog, ponavljajućeg obrasca,
    a ne samo jednosmjernog utjecaja.
    """
    target_significant_planets = {
        r.planet for r in overlay_target_to_source if r.is_significant_house
    }
    notes = []
    for r in overlay_source_to_target:
        if r.is_significant_house and r.planet in target_significant_planets:
            notes.append(
                f"{r.planet} pada u relevantnu kuću u OBA smjera ({r.source_person}→{r.target_person} "
                f"i {r.target_person}→{r.source_person}) - obrazac se ponavlja uzajamno, ne samo jednosmjerno."
            )
    return notes
