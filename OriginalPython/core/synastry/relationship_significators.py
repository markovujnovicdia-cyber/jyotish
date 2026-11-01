"""
Ključni signifikatori odnosa (2.7 u specifikaciji) - 7. kuća, Venera, Mars,
Jupiter, Mjesec, Atmakaraka, Darakaraka, Arudha Lagna, Upapada Lagna (UL),
Darapada (A7), i posebne unakrsne veze između dviju karata.

Koristi ISKLJUČIVO postojeće izračune: core.houses, core.chara_karaka
(NOVO u Fazi 2), core.natal.special_points (AL/UL/A7 već izračunati u
Fazi 1). Za unakrsne aspekte/konjunkcije PONOVNO KORISTI već izgrađene
liste iz core/synastry/graha_drishti.py i conjunctions.py (ne računa ih
iznova) - te se liste prosljeđuju kao argumenti.

ISPRAVAK (bivša greška): traženje unakrsnog kontakta (npr. Darakaraka
osobe A naspram Atmakarake osobe B) je ranije filtriralo Graha Drishti/
konjunkcije SAMO po nazivu planeta, bez provjere KOJOJ osobi taj planet u
kontaktu pripada - to je dopuštalo da se npr. "Merkur osobe A aspektira
Saturn osobe B" pogrešno prizna kao potvrda veze "Darakaraka osobe A
(Saturn) - Atmakaraka osobe B (Merkur)". Svi unakrsni parovi niže sada
prolaze isključivo kroz core.synastry.deduplication.find_cross_contact/
find_cross_conjunction, koji EKSPLICITNO provjeravaju source_person/
target_person (odn. da person_a_object dolazi iz karte A, person_b_object
iz karte B) - vidi tests/test_relationship_significators.py za regresijski
test točno ovog slučaja.
"""

from typing import Dict, List

from core.constants import RASHI, RASHI_LORD, PLANET_ORDER
from core.houses import whole_sign_house
from core.chara_karaka import get_atmakaraka, get_darakaraka
from core.natal import NatalContext
from core.synastry.config import SynastryConfig
from core.synastry.deduplication import find_cross_contact, find_cross_conjunction
from core.synastry.models import (
    PersonSignificatorProfile, RelationshipSignificatorsResult,
    GrahaDrishtiContact, ConjunctionContact, SynastryPoint,
)

# Unakrsni parovi ključnih signifikatora koje specifikacija izričito traži
# (2.7/2.8) - (uloga u karti A, uloga u karti B). Redoslijed je važan: prvi
# element je UVIJEK uloga/planet OSOBE A, drugi UVIJEK OSOBE B (vidi
# build_synastry_points niže) - to je ono što find_cross_contact/
# find_cross_conjunction očekuju.
CROSS_SIGNIFICATOR_PAIRS = [
    ("atmakaraka", "darakaraka", "Atmakaraka (A) - Darakaraka (B)"),
    ("darakaraka", "atmakaraka", "Darakaraka (A) - Atmakaraka (B)"),
    ("1st_lord", "1st_lord", "Vladar 1. kuće (A) - Vladar 1. kuće (B)"),
    ("5th_lord", "5th_lord", "Vladar 5. kuće (A) - Vladar 5. kuće (B)"),
    ("7th_lord", "7th_lord", "Vladar 7. kuće (A) - Vladar 7. kuće (B)"),
    ("8th_lord", "8th_lord", "Vladar 8. kuće (A) - Vladar 8. kuće (B)"),
    ("11th_lord", "11th_lord", "Vladar 11. kuće (A) - Vladar 11. kuće (B)"),
    ("venus", "mars", "Venera (A) - Mars (B)"),
    ("mars", "venus", "Mars (A) - Venera (B)"),
    ("moon", "sun", "Mjesec (A) - Sunce (B)"),
    ("sun", "moon", "Sunce (A) - Mjesec (B)"),
    ("UL_lord", "UL_lord", "Vladar Upapada Lagne (A) - Vladar Upapada Lagne (B)"),
    ("A7_lord", "A7_lord", "Vladar Darapade/A7 (A) - Vladar Darapade/A7 (B)"),
]


def _planets_in_sign(ctx: NatalContext, sign_index: int) -> List[str]:
    return [p for p in PLANET_ORDER if ctx.positions[p].sign_index == sign_index]


def build_significator_profile(ctx: NatalContext, person_label: str, config: SynastryConfig) -> PersonSignificatorProfile:
    asc_idx = ctx.ascendant_sign_index
    seventh_sign_idx = (asc_idx + 6) % 12
    seventh_lord = RASHI_LORD[RASHI[seventh_sign_idx]]
    seventh_lord_sign_idx = ctx.positions[seventh_lord].sign_index

    venus, mars, jupiter, moon = ctx.positions["Venera"], ctx.positions["Mars"], ctx.positions["Jupiter"], ctx.positions["Mjesec"]

    karaka_positions = {p: ctx.positions[p] for p in PLANET_ORDER if p != "Ketu"}
    atmakaraka = get_atmakaraka(karaka_positions, config.chara_karaka_scheme)
    darakaraka = get_darakaraka(karaka_positions, config.chara_karaka_scheme)

    al_sign_idx = ctx.special_points["AL_sign_index"]
    ul_sign_idx = ctx.special_points["UL_sign_index"]
    a7_sign_idx = ctx.special_points["A7_sign_index"]

    second_from_ul_idx = (ul_sign_idx + 1) % 12
    eighth_from_ul_idx = (ul_sign_idx + 7) % 12

    return PersonSignificatorProfile(
        person_label=person_label,
        seventh_house_sign=RASHI[seventh_sign_idx],
        seventh_house_planets=_planets_in_sign(ctx, seventh_sign_idx),
        seventh_lord=seventh_lord,
        seventh_lord_house=whole_sign_house(seventh_lord_sign_idx, asc_idx),
        seventh_lord_sign=RASHI[seventh_lord_sign_idx],
        venus_house=whole_sign_house(venus.sign_index, asc_idx), venus_sign=venus.sign,
        mars_house=whole_sign_house(mars.sign_index, asc_idx), mars_sign=mars.sign,
        jupiter_house=whole_sign_house(jupiter.sign_index, asc_idx), jupiter_sign=jupiter.sign,
        moon_house=whole_sign_house(moon.sign_index, asc_idx), moon_sign=moon.sign,
        atmakaraka_planet=atmakaraka.planet,
        darakaraka_planet=darakaraka.planet,
        arudha_lagna_sign=RASHI[al_sign_idx],
        upapada_lagna_sign=RASHI[ul_sign_idx],
        upapada_house=whole_sign_house(ul_sign_idx, asc_idx),
        upapada_lord=RASHI_LORD[RASHI[ul_sign_idx]],
        upapada_planets=_planets_in_sign(ctx, ul_sign_idx),
        second_from_upapada_sign=RASHI[second_from_ul_idx],
        eighth_from_upapada_sign=RASHI[eighth_from_ul_idx],
        darapada_sign=RASHI[a7_sign_idx],
        darapada_house=whole_sign_house(a7_sign_idx, asc_idx),
    )


def build_synastry_points(ctx: NatalContext, person_label: str, profile: PersonSignificatorProfile) -> Dict[str, SynastryPoint]:
    """
    Gradi rječnik "uloga -> SynastryPoint" (planet, dužina, znak, kuća) za
    SVE ključne signifikatore koje CROSS_SIGNIFICATOR_PAIRS koristi.
    person_label je UGRAĐEN u svaki SynastryPoint - ovo je ono što
    generičkim unakrsnim provjerama niže jamči da se osoba A i osoba B
    nikad ne mogu zamijeniti (svaki SynastryPoint zna kojoj osobi pripada).
    """
    asc_idx = ctx.ascendant_sign_index
    a7_lord = RASHI_LORD[profile.darapada_sign]
    first_lord = RASHI_LORD[RASHI[asc_idx]]
    fifth_lord = RASHI_LORD[RASHI[(asc_idx + 4) % 12]]
    eighth_lord = RASHI_LORD[RASHI[(asc_idx + 7) % 12]]
    eleventh_lord = RASHI_LORD[RASHI[(asc_idx + 10) % 12]]

    roles = {
        "atmakaraka": profile.atmakaraka_planet,
        "darakaraka": profile.darakaraka_planet,
        "1st_lord": first_lord,
        "5th_lord": fifth_lord,
        "7th_lord": profile.seventh_lord,
        "8th_lord": eighth_lord,
        "11th_lord": eleventh_lord,
        "UL_lord": profile.upapada_lord,
        "A7_lord": a7_lord,
        "venus": "Venera",
        "mars": "Mars",
        "moon": "Mjesec",
        "sun": "Sunce",
    }

    points: Dict[str, SynastryPoint] = {}
    for role, planet in roles.items():
        pos = ctx.positions[planet]
        points[role] = SynastryPoint(
            person_id=person_label, role=role, planet=planet,
            longitude=pos.longitude, sign=pos.sign,
            house=whole_sign_house(pos.sign_index, asc_idx),
        )
    return points


def _planets_of_other_on_point(ctx_other: NatalContext, sign_index: int) -> List[str]:
    return _planets_in_sign(ctx_other, sign_index)


def _cross_pair_notes(
    point_a: SynastryPoint, point_b: SynastryPoint, label: str,
    graha_drishti_contacts: List[GrahaDrishtiContact], conjunctions: List[ConjunctionContact],
) -> List[str]:
    """
    Generička provjera JEDNOG unakrsnog para - point_a MORA biti osobe A,
    point_b MORA biti osobe B (provjereno assertom, ne samo dokumentacijom).
    Provjerava: isti planet, isti znak, konjunkciju, Graha Drishti - sve
    preko core.synastry.deduplication (person-svjesno, bez mogućnosti
    zamjene A/B).
    """
    assert point_a.person_id == "A" and point_b.person_id == "B", (
        "_cross_pair_notes očekuje point_a iz karte A i point_b iz karte B - "
        "vidi napomenu o A/B identitetu na vrhu datoteke."
    )
    notes: List[str] = []

    if point_a.planet == point_b.planet:
        notes.append(f"{label}: ISTI planet ({point_a.planet}) igra obje uloge u obje karte.")

    if point_a.sign == point_b.sign and point_a.planet != point_b.planet:
        notes.append(f"{label}: {point_a.planet} (A) i {point_b.planet} (B) su u istom znaku ({point_a.sign}).")

    for c in find_cross_conjunction(conjunctions, point_a.planet, point_b.planet):
        notes.append(f"{label}: konjunkcija ({c.degree_distance:.1f}°) - {c.short_interpretation}")

    for c in find_cross_contact(graha_drishti_contacts, point_a.planet, point_b.planet):
        notes.append(f"{label}: Graha Drishti - {c.short_interpretation}")

    return notes


def compute_cross_notes(
    ctx_a: NatalContext, ctx_b: NatalContext,
    profile_a: PersonSignificatorProfile, profile_b: PersonSignificatorProfile,
    graha_drishti_contacts: List[GrahaDrishtiContact],
    conjunctions: List[ConjunctionContact],
) -> List[str]:
    notes: List[str] = []

    ul_sign_a = profile_a.upapada_lagna_sign
    ul_sign_b = profile_b.upapada_lagna_sign
    a7_sign_a = profile_a.darapada_sign
    a7_sign_b = profile_b.darapada_sign

    b_on_ul_a = _planets_of_other_on_point(ctx_b, RASHI.index(ul_sign_a))
    if b_on_ul_a:
        notes.append(f"Planeti osobe B na UL osobe A ({ul_sign_a}): {', '.join(b_on_ul_a)}.")
    a_on_ul_b = _planets_of_other_on_point(ctx_a, RASHI.index(ul_sign_b))
    if a_on_ul_b:
        notes.append(f"Planeti osobe A na UL osobe B ({ul_sign_b}): {', '.join(a_on_ul_b)}.")

    b_on_a7_a = _planets_of_other_on_point(ctx_b, RASHI.index(a7_sign_a))
    if b_on_a7_a:
        notes.append(f"Planeti osobe B na A7 (Darapadi) osobe A ({a7_sign_a}): {', '.join(b_on_a7_a)}.")
    a_on_a7_b = _planets_of_other_on_point(ctx_a, RASHI.index(a7_sign_b))
    if a_on_a7_b:
        notes.append(f"Planeti osobe A na A7 (Darapadi) osobe B ({a7_sign_b}): {', '.join(a_on_a7_b)}.")

    if ul_sign_a == a7_sign_b:
        notes.append(f"UL osobe A i A7 osobe B su u istom znaku ({ul_sign_a}) - naglašena bračna/partnerska tema.")
    if ul_sign_b == a7_sign_a:
        notes.append(f"UL osobe B i A7 osobe A su u istom znaku ({ul_sign_b}) - naglašena bračna/partnerska tema.")
    if ul_sign_a == ul_sign_b:
        notes.append(f"UL obje osobe je u istom znaku ({ul_sign_a}) - ponavljajuća bračna tema.")
    if a7_sign_a == a7_sign_b:
        notes.append(f"A7 (Darapada) obje osobe je u istom znaku ({a7_sign_a}) - ponavljajuća bračna tema.")

    ul_lord_a = profile_a.upapada_lord
    if ul_lord_a == profile_b.seventh_lord:
        notes.append(f"Vladar UL osobe A ({ul_lord_a}) je isti planet kao vladar 7. kuće osobe B.")
    if ul_lord_a == profile_b.darakaraka_planet:
        notes.append(f"Vladar UL osobe A ({ul_lord_a}) je isti planet kao Darakaraka osobe B.")
    if ul_lord_a == "Mjesec":
        notes.append("Vladar UL osobe A je Mjesec - izravna povezanost s Mjesecom kao signifikatorom.")

    ul_lord_b = profile_b.upapada_lord
    if ul_lord_b == profile_a.seventh_lord:
        notes.append(f"Vladar UL osobe B ({ul_lord_b}) je isti planet kao vladar 7. kuće osobe A.")
    if ul_lord_b == profile_a.darakaraka_planet:
        notes.append(f"Vladar UL osobe B ({ul_lord_b}) je isti planet kao Darakaraka osobe A.")

    # Svi unakrsni parovi ključnih signifikatora (2.7/2.8) - JEDNO mjesto,
    # person-svjesno (vidi _cross_pair_notes/find_cross_contact) umjesto
    # ranijih ad hoc provjera po nazivu planeta bez oznake osobe.
    points_a = build_synastry_points(ctx_a, "A", profile_a)
    points_b = build_synastry_points(ctx_b, "B", profile_b)
    for role_a, role_b, label in CROSS_SIGNIFICATOR_PAIRS:
        notes.extend(_cross_pair_notes(points_a[role_a], points_b[role_b], label, graha_drishti_contacts, conjunctions))

    return notes


def compute_relationship_significators(
    ctx_a: NatalContext, ctx_b: NatalContext, config: SynastryConfig,
    graha_drishti_contacts: List[GrahaDrishtiContact],
    conjunctions: List[ConjunctionContact],
) -> RelationshipSignificatorsResult:
    profile_a = build_significator_profile(ctx_a, "A", config)
    profile_b = build_significator_profile(ctx_b, "B", config)
    cross_notes = compute_cross_notes(ctx_a, ctx_b, profile_a, profile_b, graha_drishti_contacts, conjunctions)
    return RelationshipSignificatorsResult(profile_a=profile_a, profile_b=profile_b, cross_notes=cross_notes)
