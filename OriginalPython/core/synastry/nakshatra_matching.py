"""
Nakšatra sinastrija (2.4 u specifikaciji) - usporedba nakšatre, pade,
vladara nakšatre, devate, Gane, Yonija, Nadija i D9 znaka/elementa pade za
ključne točke: Mjesec, Ascendent, Venera, Mars, Sunce, vladar 7. kuće,
Darakaraka.

Koristi ISKLJUČIVO postojeće izračune (core.nakshatra, core.varga) i nove
tablice u core/constants.py (NAKSHATRA_DEVATA/GANA/YONI/NADI, RASHI_ELEMENT)
- nema duplicirane geometrije.

Vizualni graf odnosa vladara nakšatri (spec traži "Prikaži i graf odnosa
vladara nakšatri") je OVDJE dostupan kao struktura podataka (lord_graph_edges)
- stvarni CRTANI dijagram (SVG čvorovi/bridovi) je dio grafičkog sloja koji
dolazi u Fazi 3 ("grafički prikaz"), ovdje se prikazuje kao tablica u UI-u.

ISPRAVAK (bivša greška - "lažne nakšatra unakrsne veze"): ranije je SVAKA
podudarnost "vladar nakšatre točke A = neki od 7 promatranih planeta/točaka
osobe B" prijavljena kao "veza", iako to samo po sebi ništa ne znači - SVAKA
natalna karta ima Mars, Veneru itd., pa "vladar nakšatre Venere osobe A je
Mars, a osoba B ima Mars" NIJE stvarna astrološka poveznica bez DODATNE
potvrde. `find_dispositor_links` niže sada razdvaja to u 5 kategorija (od
najjače do najslabije potvrđene):
  1. ista nakšatra (`find_same_nakshatra_links` - nepromijenjeno)
  2. isti vladar nakšatre dviju točaka (`same_nakshatra_lord` - novo)
  3. uzajamna (zatvorena) dispozicija (`mutual_dispositor`, bivši "closed_chain")
  4. vladar-nakšatre veza POTVRĐENA stvarnim kontaktom (aspekt ili
     konjunkcija između točke i planeta koji joj vlada nakšatrom) -
     `dispositor_confirmed`
  5. NEPOTVRĐENA vladar-nakšatre veza - `dispositor_symbolic`, `scored=False`
     (samo slaba napomena u izvještaju, core/synastry/scoring.py je NE broji)
"""

from typing import Dict, List, Optional

from core.constants import (
    RASHI, NAKSHATRA_DEVATA, NAKSHATRA_GANA, NAKSHATRA_YONI,
    NAKSHATRA_NADI, RASHI_ELEMENT,
)
from core.nakshatra import get_nakshatra
from core.varga import d9_navamsha_sign_index
from core.natal import NatalContext
from core.synastry.deduplication import find_cross_contact, find_cross_conjunction
from core.synastry.models import (
    NakshatraProfile, NakshatraCrossLink, NakshatraRepeatedTheme, NakshatraSynastryResult,
    GrahaDrishtiContact, ConjunctionContact,
)

# Redoslijed i oznake ključnih točaka koje se uspoređuju (spec 2.4)
KEY_POINT_LABELS = ["Mjesec", "Ascendent", "Venera", "Mars", "Sunce", "Vladar 7.", "Darakaraka"]


def build_nakshatra_profile(person_label: str, point_label: str, planet_or_point: str, longitude: float) -> NakshatraProfile:
    nak = get_nakshatra(longitude)
    d9_sign_idx = d9_navamsha_sign_index(longitude)
    d9_sign = RASHI[d9_sign_idx]
    yoni_animal, yoni_gender = NAKSHATRA_YONI[nak.index]

    return NakshatraProfile(
        person_label=person_label,
        point_label=point_label,
        planet_or_point=planet_or_point,
        longitude=longitude,
        nakshatra=nak.name,
        pada=nak.pada,
        nakshatra_lord=nak.lord,
        devata=NAKSHATRA_DEVATA[nak.index],
        gana=NAKSHATRA_GANA[nak.index],
        yoni=yoni_animal,
        yoni_gender=yoni_gender,
        nadi=NAKSHATRA_NADI[nak.index],
        navamsha_sign=d9_sign,
        pada_element=RASHI_ELEMENT[d9_sign],
    )


def build_all_profiles(
    person_label: str, ctx: NatalContext, seventh_lord_planet: str, darakaraka_planet: str,
) -> Dict[str, NakshatraProfile]:
    """
    ctx: core.natal.NatalContext. seventh_lord_planet/darakaraka_planet:
    nazivi planeta (npr. "Mars") koji igraju te uloge u OVOJ karti.
    """
    profiles: Dict[str, NakshatraProfile] = {}
    profiles["Mjesec"] = build_nakshatra_profile(person_label, "Mjesec", "Mjesec", ctx.positions["Mjesec"].longitude)
    profiles["Ascendent"] = build_nakshatra_profile(person_label, "Ascendent", "Lagna", ctx.ascendant_longitude)
    profiles["Venera"] = build_nakshatra_profile(person_label, "Venera", "Venera", ctx.positions["Venera"].longitude)
    profiles["Mars"] = build_nakshatra_profile(person_label, "Mars", "Mars", ctx.positions["Mars"].longitude)
    profiles["Sunce"] = build_nakshatra_profile(person_label, "Sunce", "Sunce", ctx.positions["Sunce"].longitude)
    profiles["Vladar 7."] = build_nakshatra_profile(
        person_label, "Vladar 7.", seventh_lord_planet, ctx.positions[seventh_lord_planet].longitude
    )
    profiles["Darakaraka"] = build_nakshatra_profile(
        person_label, "Darakaraka", darakaraka_planet, ctx.positions[darakaraka_planet].longitude
    )
    return profiles


def _label(profile: NakshatraProfile) -> str:
    return f"{profile.point_label} ({profile.person_label})"


def find_same_nakshatra_links(
    profiles_a: Dict[str, NakshatraProfile], profiles_b: Dict[str, NakshatraProfile],
) -> List[NakshatraCrossLink]:
    """Isti nakshatra (ista ili različita pada) između bilo koje dvije ključne točke A i B."""
    links = []
    for label_a, prof_a in profiles_a.items():
        for label_b, prof_b in profiles_b.items():
            if prof_a.nakshatra == prof_b.nakshatra:
                if prof_a.pada == prof_b.pada:
                    links.append(NakshatraCrossLink(
                        relation_type="same_pada",
                        source_label=_label(prof_a), target_label=_label(prof_b),
                        detail=f"Obje u {prof_a.nakshatra}, pada {prof_a.pada} - vrlo uska, specifična veza.",
                    ))
                else:
                    links.append(NakshatraCrossLink(
                        relation_type="same_nakshatra",
                        source_label=_label(prof_a), target_label=_label(prof_b),
                        detail=(
                            f"Obje u {prof_a.nakshatra}, različite pade ({prof_a.pada} i {prof_b.pada}) - "
                            f"dijele širu simboličku temu (devata: {prof_a.devata})."
                        ),
                    ))
    return links


def find_same_nakshatra_lord_links(
    profiles_a: Dict[str, NakshatraProfile], profiles_b: Dict[str, NakshatraProfile],
) -> List[NakshatraCrossLink]:
    """Kategorija 2: dvije ključne točke (A i B) DIJELE istog vladara nakšatre."""
    links = []
    for prof_a in profiles_a.values():
        for prof_b in profiles_b.values():
            if prof_a.nakshatra_lord == prof_b.nakshatra_lord:
                links.append(NakshatraCrossLink(
                    relation_type="same_nakshatra_lord",
                    source_label=_label(prof_a), target_label=_label(prof_b),
                    detail=(
                        f"{prof_a.point_label} (A) i {prof_b.point_label} (B) dijele istog vladara "
                        f"nakšatre ({prof_a.nakshatra_lord}) - stvarna, provjerljiva poveznica (ne samo "
                        f"'obje karte imaju taj planet')."
                    ),
                    scored=True,
                ))
    return links


def _dispositor_candidates(
    profiles_a: Dict[str, NakshatraProfile], profiles_b: Dict[str, NakshatraProfile],
) -> List[NakshatraCrossLink]:
    """
    Svi KANDIDATI za vladar-nakšatre vezu (prije provjere je li stvarno
    značajna) - "vladar nakšatre točke A je BAŠ onaj planet koji kod osobe
    B igra jednu od 7 promatranih ključnih uloga" (i obrnuto). Ovo SAMO PO
    SEBI nije dovoljno (svaka karta ima Mars/Veneru/...) - vidi
    find_dispositor_links koji ove kandidate klasificira dalje.
    """
    candidates = []
    for prof_a in profiles_a.values():
        for prof_b in profiles_b.values():
            if prof_a.nakshatra_lord == prof_b.planet_or_point:
                candidates.append(NakshatraCrossLink(
                    relation_type="dispositor_symbolic",
                    source_label=_label(prof_a), target_label=_label(prof_b),
                    detail=(
                        f"{prof_a.point_label} ({prof_a.person_label}) je u nakšatri kojom vlada "
                        f"{prof_a.nakshatra_lord} - a to je baš {prof_b.point_label} osobe {prof_b.person_label}."
                    ),
                    scored=False,
                ))
    for prof_b in profiles_b.values():
        for prof_a in profiles_a.values():
            if prof_b.nakshatra_lord == prof_a.planet_or_point:
                candidates.append(NakshatraCrossLink(
                    relation_type="dispositor_symbolic",
                    source_label=_label(prof_b), target_label=_label(prof_a),
                    detail=(
                        f"{prof_b.point_label} ({prof_b.person_label}) je u nakšatri kojom vlada "
                        f"{prof_b.nakshatra_lord} - a to je baš {prof_a.point_label} osobe {prof_a.person_label}."
                    ),
                    scored=False,
                ))
    return candidates


def find_dispositor_links(
    profiles_a: Dict[str, NakshatraProfile], profiles_b: Dict[str, NakshatraProfile],
    graha_drishti_contacts: List[GrahaDrishtiContact], conjunctions: List[ConjunctionContact],
) -> List[NakshatraCrossLink]:
    """
    Klasificira svakog dispozitorskog kandidata (vidi _dispositor_candidates)
    u kategoriju 3 (uzajamna/zatvorena dispozicija), 4 (potvrđena stvarnim
    kontaktom) ili 5 (samo simbolička napomena, bez boda) - vidi napomenu
    na vrhu datoteke.
    """
    candidates = _dispositor_candidates(profiles_a, profiles_b)
    by_pair = {(l.source_label, l.target_label): l for l in candidates}

    results: List[NakshatraCrossLink] = []
    seen_mutual = set()
    # NAPOMENA: profiles_a i profiles_b dijele iste ključeve (npr. "Venera")
    # pa se NE SMIJU spojiti preko {**profiles_a, **profiles_b} (to bi
    # prepisalo A-ine vrijednosti B-inima) - grade se labele iz OBJE liste
    # vrijednosti odvojeno.
    label_to_profile = {_label(p): p for p in list(profiles_a.values()) + list(profiles_b.values())}

    for link in candidates:
        reverse_key = (link.target_label, link.source_label)
        mutual_key = frozenset((link.source_label, link.target_label))

        if reverse_key in by_pair and mutual_key not in seen_mutual:
            seen_mutual.add(mutual_key)
            results.append(NakshatraCrossLink(
                relation_type="mutual_dispositor",
                source_label=link.source_label, target_label=link.target_label,
                detail=f"Uzajamna (zatvorena) dispozicija: {link.source_label} i {link.target_label} uzajamno vladaju jedno drugom nakšatrom.",
                scored=True,
            ))
            continue
        if reverse_key in by_pair:
            # Već obrađeno kao mutual_dispositor u suprotnom smjeru - preskoči duplikat.
            continue

        prof_source = label_to_profile[link.source_label]
        prof_target = label_to_profile[link.target_label]
        # find_cross_contact/find_cross_conjunction očekuju (planet OSOBE A,
        # planet OSOBE B) - source/target OVDJE mogu biti u bilo kojem
        # smjeru (kandidati su građeni i za A-vlada-B i za B-vlada-A), pa se
        # ovdje eksplicitno poravnava po stvarnom person_label-u.
        if prof_source.person_label == "A":
            planet_a, planet_b = prof_source.planet_or_point, prof_target.planet_or_point
        else:
            planet_a, planet_b = prof_target.planet_or_point, prof_source.planet_or_point
        confirmed = (
            bool(find_cross_contact(graha_drishti_contacts, planet_a, planet_b))
            or bool(find_cross_conjunction(conjunctions, planet_a, planet_b))
        )
        if confirmed:
            results.append(NakshatraCrossLink(
                relation_type="dispositor_confirmed",
                source_label=link.source_label, target_label=link.target_label,
                detail=link.detail + " POTVRĐENO stvarnim kontaktom (aspekt ili konjunkcija) između te dvije točke.",
                scored=True,
            ))
        else:
            results.append(link)  # ostaje "dispositor_symbolic", scored=False

    return results


def find_repeated_themes(
    profiles_a: Dict[str, NakshatraProfile], profiles_b: Dict[str, NakshatraProfile],
) -> List[NakshatraRepeatedTheme]:
    """Ista nakshatra se ponavlja kroz VIŠE ključnih točaka (bilo koje kombinacije A/B)."""
    by_nakshatra: Dict[str, List[str]] = {}
    for prof in list(profiles_a.values()) + list(profiles_b.values()):
        by_nakshatra.setdefault(prof.nakshatra, []).append(_label(prof))

    themes = []
    for nakshatra, labels in by_nakshatra.items():
        if len(labels) >= 2:
            themes.append(NakshatraRepeatedTheme(
                nakshatra=nakshatra,
                points_involved=labels,
                note=f"{nakshatra} se ponavlja kroz {len(labels)} ključne točke - naglašena zajednička tema.",
            ))
    return themes


def compute_nakshatra_synastry(
    ctx_a: NatalContext, ctx_b: NatalContext,
    seventh_lord_a: str, seventh_lord_b: str,
    darakaraka_a: str, darakaraka_b: str,
    graha_drishti_contacts: Optional[List[GrahaDrishtiContact]] = None,
    conjunctions: Optional[List[ConjunctionContact]] = None,
) -> NakshatraSynastryResult:
    """
    graha_drishti_contacts/conjunctions: VEĆ izračunate unakrsne liste
    (core/synastry/graha_drishti.py, conjunctions.py) - potrebne OVDJE da bi
    se vladar-nakšatre kandidati mogli klasificirati u potvrđene (kategorija
    3/4) naspram samo simboličkih (kategorija 5, bez boda) - vidi napomenu
    na vrhu datoteke. Opcionalni (zadano prazna lista) SAMO radi unatrag
    kompatibilnosti s pozivateljima koji ne trebaju nakšatra sinastriju
    samu po sebi (npr. prediktivni testovi koji trebaju samo valjan
    NakshatraSynastryResult kao ulaz za drugu funkciju) - stvarni cjevovod
    (ui/pages_synastry.py) UVIJEK prosljeđuje stvarne liste.
    """
    graha_drishti_contacts = graha_drishti_contacts or []
    conjunctions = conjunctions or []
    profiles_a = build_all_profiles("A", ctx_a, seventh_lord_a, darakaraka_a)
    profiles_b = build_all_profiles("B", ctx_b, seventh_lord_b, darakaraka_b)

    same_links = find_same_nakshatra_links(profiles_a, profiles_b)
    same_lord_links = find_same_nakshatra_lord_links(profiles_a, profiles_b)
    dispositor_links = find_dispositor_links(profiles_a, profiles_b, graha_drishti_contacts, conjunctions)
    all_links = same_links + same_lord_links + dispositor_links

    repeated = find_repeated_themes(profiles_a, profiles_b)

    graph_edges = [
        (l.source_label, l.target_label, l.relation_type) for l in dispositor_links
        if l.relation_type in ("mutual_dispositor", "dispositor_confirmed", "dispositor_symbolic")
    ]

    return NakshatraSynastryResult(
        profiles_a=profiles_a, profiles_b=profiles_b,
        cross_links=all_links, repeated_themes=repeated,
        lord_graph_edges=graph_edges,
    )
