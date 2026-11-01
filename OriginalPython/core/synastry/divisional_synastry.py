"""
Generička divizijska (varga) sinastrija (2.8/2.9 u specifikaciji).

Potpuno implementirano za D9 (Navamsha) - compute_navamsha_synastry(). Sve
funkcije osim tog ulaza su NAMJERNO generičke (primaju varga_func iz
core.varga) - ista arhitektura vrijedi za D7/D10/D12 ili bilo koju drugu
vargu, samo se proslijedi odgovarajuća core.varga funkcija (npr.
core.varga.d7_saptamsha_sign_index). Sučelje (UI/izvještaj) trenutno poziva
samo D9 verziju - D7/D10/D12 sinastrija nije još izložena u UI-u, ali
izračun je spreman.

NE duplicira geometriju: kućni overlay ponovno koristi core.houses.
whole_sign_house, Graha Drishti ponovno koristi core.synastry.graha_drishti.
compute_cross_chart_drishti (već generički - radi na BILO KOJIM sign_index
mapama, D1 ili varga).

"Konjunkcija" u varga karti NIJE stupanjski koncept ovdje (varga stupnjevi
su "sažeti"/nelinearni prema D1 stupnju, orb-bazirana konjunkcija bi bila
zavaravajuća) - umjesto toga koristi se ISTI ZNAK (same-sign) kao
varga-ekvivalent konjunkcije, jasno tako i nazvano.

Prema specifikaciji ("Nemoj D9 tumačiti kao potpuno neovisnu natalnu
kartu"): find_repeated_patterns_vs_d1() POVEZUJE D9 rezultate s već
izračunatim D1 kontaktima (Graha Drishti + konjunkcije), ne promatra D9
izolirano.
"""

from typing import Callable, Dict, List

from core.constants import RASHI, RASHI_LORD, PLANET_ORDER
from core.houses import whole_sign_house
from core.aspects import ASPECT_STRENGTH_LABEL
from core.natal import NatalContext
from core.synastry.config import SynastryConfig
from core.synastry.deduplication import (
    contact_key, key_from_drishti_contact, key_from_conjunction,
    drishti_confirmation_strength, conjunction_confirmation_strength, parse_contact_key,
)
from core.synastry.graha_drishti import compute_cross_chart_drishti
from core.synastry.overlays import SIGNIFICANT_HOUSES
from core.synastry.scoring_config import D1_D9_REPEAT_MIN_SCORE
from core.synastry.models import (
    GrahaDrishtiContact, ConjunctionContact,
    VargaHouseOverlayRow, VargaSameSignContact, VargaSynastryResult,
)

KEY_POINT_PLANETS = ["Venera", "Mars", "Jupiter", "Mjesec"]


def compute_varga_house_overlay(
    source_ctx: NatalContext, target_ctx: NatalContext,
    source_label: str, target_label: str,
    varga_func: Callable[[float], int],
) -> List[VargaHouseOverlayRow]:
    target_asc_varga_idx = varga_func(target_ctx.ascendant_longitude)
    rows = []
    for planet in PLANET_ORDER:
        pos = source_ctx.positions[planet]
        varga_idx = varga_func(pos.longitude)
        house = whole_sign_house(varga_idx, target_asc_varga_idx)
        rows.append(VargaHouseOverlayRow(
            source_person=source_label, target_person=target_label,
            planet=planet, varga_sign=RASHI[varga_idx], house=house,
            is_significant_house=house in SIGNIFICANT_HOUSES,
            label=f"{planet} ({source_label}) → {house}. kuća ({target_label})",
        ))
    return rows


def compute_varga_drishti(
    source_ctx: NatalContext, target_ctx: NatalContext,
    source_label: str, target_label: str,
    varga_func: Callable[[float], int],
    config: SynastryConfig,
) -> List[GrahaDrishtiContact]:
    from_sign_index = {p: varga_func(pos.longitude) for p, pos in source_ctx.positions.items()}
    to_sign_index = {p: varga_func(pos.longitude) for p, pos in target_ctx.positions.items()}
    to_sign_index["Lagna"] = varga_func(target_ctx.ascendant_longitude)

    relations = compute_cross_chart_drishti(from_sign_index, to_sign_index, config)
    contacts = []
    for rel in relations:
        contacts.append(GrahaDrishtiContact(
            source_person=source_label, target_person=target_label,
            from_planet=rel.from_planet, to_planet=rel.to_planet,
            house_distance=rel.house_distance, strength=rel.strength,
            strength_label=ASPECT_STRENGTH_LABEL[rel.strength],
            from_planet_houses_own_chart=[], to_planet_houses_own_chart=[],
        ))
    return contacts


def compute_varga_same_sign_contacts(
    points_a: Dict[str, float], points_b: Dict[str, float], varga_func: Callable[[float], int],
) -> List[VargaSameSignContact]:
    results = []
    for name_a, lon_a in points_a.items():
        idx_a = varga_func(lon_a)
        for name_b, lon_b in points_b.items():
            idx_b = varga_func(lon_b)
            if idx_a == idx_b:
                results.append(VargaSameSignContact(name_a, name_b, RASHI[idx_a]))
    return results


def find_repeated_patterns_vs_d1(
    varga_drishti: List[GrahaDrishtiContact],
    varga_same_sign: List[VargaSameSignContact],
    d1_drishti: List[GrahaDrishtiContact],
    d1_conjunctions: List[ConjunctionContact],
    varga_name: str,
) -> List[tuple]:
    """
    Vraća listu (pair_key, napomena) - pair_key (core.synastry.deduplication.
    contact_key) omogućuje core/synastry/scoring.py da D1/D9 potvrdu
    primijeni kao ograničen bonus na POSTOJEĆI D1 par, umjesto novog,
    neovisnog boda (spec 9).

    Pronalazi parove planeta koji su povezani i u D1 (Graha Drishti ili
    konjunkcija) I u varga karti (Graha Drishti ili isti znak) - "ponovljena
    tema" (spec 2.8/9) koja jača indikaciju umjesto da se broji kao odvojen,
    neovisan nalaz.

    ISPRAVAK (bivša greška): ranije se par bilježio kao "ponovljen" čim je
    postojao BILO KAKAV D1 kontakt i BILO KAKAV D9 kontakt za par planeta
    identificiran preko `frozenset({ime_a, ime_b})` - bez oznake osobe (ista
    person-swap ranjivost kao u core/synastry/scoring.py) i bez praga
    jačine, što je proizvodilo desetke lažno pojačanih nalaza čak i za
    slabe (1/4) aspekte. Sada:
      - ključ para je person-svjestan (core.synastry.deduplication.contact_key)
      - par se broji kao "ponovljen" SAMO ako kombinirana jačina D1 i D9
        strane (core.synastry.deduplication.drishti_confirmation_strength/
        conjunction_confirmation_strength, ista ljestvica kao scoring.py)
        prijeđe D1_D9_REPEAT_MIN_SCORE.
    """
    d1_strength: Dict[str, float] = {}
    for c in d1_drishti:
        key = key_from_drishti_contact(c)
        d1_strength[key] = max(d1_strength.get(key, 0.0), drishti_confirmation_strength(c))
    for c in d1_conjunctions:
        key = key_from_conjunction(c)
        d1_strength[key] = max(d1_strength.get(key, 0.0), conjunction_confirmation_strength(c))

    notes: List[tuple] = []
    seen = set()
    for c in varga_drishti:
        key = key_from_drishti_contact(c)
        if key in d1_strength and key not in seen:
            combined = (d1_strength[key] + drishti_confirmation_strength(c)) / 2.0
            if combined >= D1_D9_REPEAT_MIN_SCORE:
                seen.add(key)
                a, b = parse_contact_key(key)
                notes.append((key,
                    f"{a} (A) - {b} (B): veza postoji i u D1 (Graha Drishti/konjunkcija) I u {varga_name} "
                    f"(Graha Drishti) - ponovljena tema (kombinirana jačina {combined:.2f}), jača indikacija "
                    f"nego izolirani nalaz."
                ))
    for c in varga_same_sign:
        key = contact_key(c.person_a_object, c.person_b_object)
        if key in d1_strength and key not in seen:
            # Isti znak u vargi tretira se kao jaka (1.0), egzaktnoj konjunkciji
            # analogna potvrda - vidi core.synastry.deduplication.conjunction_confirmation_strength.
            combined = (d1_strength[key] + 1.0) / 2.0
            if combined >= D1_D9_REPEAT_MIN_SCORE:
                seen.add(key)
                a, b = parse_contact_key(key)
                notes.append((key,
                    f"{a} (A) - {b} (B): isti par povezan i u D1 I u {varga_name} (isti znak: {c.varga_sign}) - "
                    f"ponovljena tema (kombinirana jačina {combined:.2f})."
                ))
    return notes


def compute_varga_synastry(
    ctx_a: NatalContext, ctx_b: NatalContext, config: SynastryConfig,
    varga_func: Callable[[float], int], varga_code: str, varga_name: str,
    seventh_lord_a: str, seventh_lord_b: str,
    darakaraka_a: str, darakaraka_b: str, atmakaraka_a: str, atmakaraka_b: str,
    d1_drishti: List[GrahaDrishtiContact],
    d1_conjunctions: List[ConjunctionContact],
) -> VargaSynastryResult:
    asc_a_idx, asc_b_idx = varga_func(ctx_a.ascendant_longitude), varga_func(ctx_b.ascendant_longitude)
    seventh_a_idx, seventh_b_idx = (asc_a_idx + 6) % 12, (asc_b_idx + 6) % 12

    def _key_points(ctx: NatalContext, darakaraka: str, atmakaraka: str) -> Dict[str, str]:
        points = {p: RASHI[varga_func(ctx.positions[p].longitude)] for p in KEY_POINT_PLANETS}
        points["Darakaraka"] = RASHI[varga_func(ctx.positions[darakaraka].longitude)]
        points["Atmakaraka"] = RASHI[varga_func(ctx.positions[atmakaraka].longitude)]
        return points

    key_points_a = _key_points(ctx_a, darakaraka_a, atmakaraka_a)
    key_points_b = _key_points(ctx_b, darakaraka_b, atmakaraka_b)

    overlay_a_to_b = compute_varga_house_overlay(ctx_a, ctx_b, "A", "B", varga_func)
    overlay_b_to_a = compute_varga_house_overlay(ctx_b, ctx_a, "B", "A", varga_func)

    drishti_a_to_b = compute_varga_drishti(ctx_a, ctx_b, "A", "B", varga_func, config)
    drishti_b_to_a = compute_varga_drishti(ctx_b, ctx_a, "B", "A", varga_func, config)

    points_a = {name: pos.longitude for name, pos in ctx_a.positions.items()}
    points_a["Lagna"] = ctx_a.ascendant_longitude
    points_b = {name: pos.longitude for name, pos in ctx_b.positions.items()}
    points_b["Lagna"] = ctx_b.ascendant_longitude
    same_sign = compute_varga_same_sign_contacts(points_a, points_b, varga_func)

    repeated = find_repeated_patterns_vs_d1(
        drishti_a_to_b + drishti_b_to_a, same_sign, d1_drishti, d1_conjunctions, varga_name,
    )
    repeated_keys = [key for key, _ in repeated]
    repeated_notes = [note for _, note in repeated]

    return VargaSynastryResult(
        varga_code=varga_code, varga_name=varga_name,
        ascendant_sign_a=RASHI[asc_a_idx], ascendant_sign_b=RASHI[asc_b_idx],
        seventh_sign_a=RASHI[seventh_a_idx], seventh_sign_b=RASHI[seventh_b_idx],
        seventh_lord_a=RASHI_LORD[RASHI[seventh_a_idx]], seventh_lord_b=RASHI_LORD[RASHI[seventh_b_idx]],
        key_points_a=key_points_a, key_points_b=key_points_b,
        overlay_a_to_b=overlay_a_to_b, overlay_b_to_a=overlay_b_to_a,
        drishti_a_to_b=drishti_a_to_b, drishti_b_to_a=drishti_b_to_a,
        same_sign_contacts=same_sign,
        repeated_pattern_notes=repeated_notes,
        repeated_pattern_pair_keys=repeated_keys,
    )


def compute_navamsha_synastry(
    ctx_a: NatalContext, ctx_b: NatalContext, config: SynastryConfig,
    seventh_lord_a: str, seventh_lord_b: str,
    darakaraka_a: str, darakaraka_b: str, atmakaraka_a: str, atmakaraka_b: str,
    d1_drishti: List[GrahaDrishtiContact],
    d1_conjunctions: List[ConjunctionContact],
) -> VargaSynastryResult:
    from core.varga import d9_navamsha_sign_index
    return compute_varga_synastry(
        ctx_a, ctx_b, config, d9_navamsha_sign_index, "D9", "Navamsha",
        seventh_lord_a, seventh_lord_b, darakaraka_a, darakaraka_b, atmakaraka_a, atmakaraka_b,
        d1_drishti, d1_conjunctions,
    )
