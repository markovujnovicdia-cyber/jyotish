"""
Karyesha-bazirane Tajika yoge - zahtijevaju odabir konkretnog životnog
područja (Karyesha = vladar kuće o kojoj se pita), za razliku od opće
Ithasala/Isarapha mreže (core/tajika.py) koja se primjenjuje na SVE
parove planeta bez konteksta pitanja.

Implementirano, Lagnesha/Karyesha par (jasno definirano, potvrđeno kroz
više neovisnih izvora - jyotishforgood.com "A comprehensive guide to
Tajika Yogas", Varahamihira blogspot "Tajika Yogas", B.V. Raman
"Varshaphala"):
- Ithasala / Isarapha (izravno, između Lagnesha i Karyeshe)
- Nakta (treća, BRŽA planeta premošćuje - Ithasala s obje)
- Yamaya (isto, ali treća planeta SPORIJA)
- Manau (Ithasala postoji, ali Mars i Saturn su unutar orba brže planete)
- Kambula (Mjesec sudjeluje u Ithasala odnosu Lagnesha-Karyeshe)
- Radda (Ithasala + jedan od dvoje retrogradan ILI kombust)
- Duparikutha (sporija planeta jaka, brža slaba - ipak povoljan ishod)
- Durupha (oboje u 6./8./12. kući, oslabljeni, formiraju Ithasalu)
- Duttota (oboje slabi, ALI jedan ima Ithasalu s trećom JAKOM planetom)
- Tambira (brža planeta jaka I na kraju znaka - Ithasala se potvrđuje)

Implementirano, GLOBALNO (cijela karta, ne par) - vidi funkcije
compute_ishkavala/compute_induvara/compute_khallasara niže:
- Ishkavala (=Ikkavala): SVIH 7 planeta u kendri/panaphari
- Induvara: SVIH 7 planeta u apoklimi
- Khallasara (Hartova definicija): Mjesec nema Ithasalu niti s kim

NIJE implementirano (nejasna/proturječna definicija između izvora):
Gairikambula, Kuttha (izvori se ne slažu je li to isto što i Duparikutha
ili nešto treće).
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from core.tajika import analyze_pair, TAJIKA_PLANETS, DEEPTAMSHA
from core.planet_strength import compute_dignity


@dataclass
class KaryeshaYogaResult:
    name: str
    found: bool
    detail: str


def _house_of(sign_index: int, asc_sign_index: int) -> int:
    return (sign_index - asc_sign_index) % 12 + 1


def analyze_karyesha_yogas(
    lagnesha: str,
    karyesha: str,
    positions: Dict[str, Tuple[float, bool]],
    sign_index_by_planet: Dict[str, int],
    asc_sign_index: int,
) -> List[KaryeshaYogaResult]:
    """
    lagnesha: vladar Varsha Lagne
    karyesha: vladar kuće o kojoj se pita (odabrano od korisnika)
    positions: {planet: (longitude, is_retrograde)} - pozicije 7 klasičnih
    planeta u Varsha karti
    """
    results: List[KaryeshaYogaResult] = []

    if lagnesha == karyesha:
        note = (
            f"Lagnesha i Karyesha su OBOJE {lagnesha} (isti planet vlada Varsha Lagnom i "
            f"odabranom kućom) - aspekt planeta prema samom sebi nema smisla, pa se ove "
            f"yoge ne mogu primijeniti na ovaj par."
        )
        for name in ("Ithasala", "Isarapha", "Nakta", "Yamaya", "Manau", "Kambula", "Radda", "Duparikutha", "Durupha"):
            results.append(KaryeshaYogaResult(name, False, note))
        return results

    lon_l, retro_l = positions[lagnesha]
    lon_k, retro_k = positions[karyesha]
    direct = analyze_pair(lagnesha, lon_l, retro_l, karyesha, lon_k, retro_k)

    has_ithasala = bool(direct.aspect and direct.within_orb and direct.is_applying)
    has_isarapha = bool(direct.aspect and direct.within_orb and not direct.is_applying)

    results.append(KaryeshaYogaResult(
        "Ithasala",
        has_ithasala,
        f"{lagnesha} (Lagnesha) i {karyesha} (Karyesha) izravno u primjenjujućem aspektu ({direct.aspect})."
        if has_ithasala else "Nema izravnog primjenjujućeg aspekta između Lagnesha i Karyeshe.",
    ))
    results.append(KaryeshaYogaResult(
        "Isarapha",
        has_isarapha,
        f"{lagnesha} i {karyesha} izravno u razdvajajućem aspektu ({direct.aspect})."
        if has_isarapha else "Nema izravnog razdvajajućeg aspekta između Lagnesha i Karyeshe.",
    ))

    nakta_bridge = None
    yamaya_bridge = None
    if not has_ithasala and not has_isarapha:
        l_rank = TAJIKA_PLANETS.index(lagnesha)
        k_rank = TAJIKA_PLANETS.index(karyesha)
        for p in TAJIKA_PLANETS:
            if p in (lagnesha, karyesha):
                continue
            lon_p, retro_p = positions[p]
            rel_l = analyze_pair(p, lon_p, retro_p, lagnesha, lon_l, retro_l)
            rel_k = analyze_pair(p, lon_p, retro_p, karyesha, lon_k, retro_k)
            if rel_l.aspect and rel_l.within_orb and rel_k.aspect and rel_k.within_orb:
                p_rank = TAJIKA_PLANETS.index(p)
                if p_rank < l_rank and p_rank < k_rank and nakta_bridge is None:
                    nakta_bridge = p
                elif p_rank > l_rank and p_rank > k_rank and yamaya_bridge is None:
                    yamaya_bridge = p

    results.append(KaryeshaYogaResult(
        "Nakta",
        nakta_bridge is not None,
        f"{nakta_bridge} (brži od oboje) premošćuje Lagnesha i Karyeshu - uspjeh uz pomoć treće strane."
        if nakta_bridge else "Nema brže planete koja premošćuje Lagnesha i Karyeshu.",
    ))
    results.append(KaryeshaYogaResult(
        "Yamaya",
        yamaya_bridge is not None,
        f"{yamaya_bridge} (sporiji od oboje) premošćuje Lagnesha i Karyeshu - uspjeh uz kašnjenje."
        if yamaya_bridge else "Nema sporije planete koja premošćuje Lagnesha i Karyeshu.",
    ))

    manau = False
    manau_detail = "Nema izravne Ithasale, Manau se ne primjenjuje."
    if has_ithasala:
        faster_lon, _ = positions[direct.faster]
        blockers = []
        for blocker in ("Mars", "Saturn"):
            if blocker in (lagnesha, karyesha):
                continue
            b_lon, _ = positions[blocker]
            dist = abs((b_lon - faster_lon + 180) % 360 - 180)
            if dist <= DEEPTAMSHA[blocker]:
                blockers.append(blocker)
        manau = len(blockers) > 0
        manau_detail = (
            f"Ithasala postoji, ali {', '.join(blockers)} unutar orba brže planete ({direct.faster}) - ometa ishod."
            if manau else "Ithasala postoji i nije ometena Marsom/Saturnom."
        )
    results.append(KaryeshaYogaResult("Manau", manau, manau_detail))

    # Kamboola: (1) Lagnesha-Karyesha Ithasala i (2) treći planet Mjesec
    # u vlastitoj Ithasali s jednim ili oba signifikatora. Sam par koji
    # uključuje Mjesec nije dovoljan da se potvrdi trostruka yoga.
    kambula = False
    if has_ithasala and "Mjesec" not in (lagnesha, karyesha):
        moon_lon, moon_retro = positions["Mjesec"][:2]
        moon_with_l = analyze_pair("Mjesec", moon_lon, moon_retro, lagnesha, lon_l, retro_l)
        moon_with_k = analyze_pair("Mjesec", moon_lon, moon_retro, karyesha, lon_k, retro_k)
        kambula = any(r.aspect and r.within_orb and r.is_applying
                      for r in (moon_with_l, moon_with_k))
    results.append(KaryeshaYogaResult(
        "Kambula",
        kambula,
        "Ithasala Lagnesha-Karyesha i dodatna Ithasala Mjeseca s jednim od njih."
        if kambula else "Nije potvrđena trostruka Ithasala s Mjesecom.",
    ))

    sun_lon = positions["Sunce"][0]
    from core.combustion import check_combustion
    combust_l = check_combustion(lagnesha, lon_l, sun_lon, retro_l) if lagnesha != "Sunce" else None
    combust_k = check_combustion(karyesha, lon_k, sun_lon, retro_k) if karyesha != "Sunce" else None
    is_combust_l = combust_l is not None and combust_l.is_combust
    is_combust_k = combust_k is not None and combust_k.is_combust
    radda = has_ithasala and (retro_l or retro_k or is_combust_l or is_combust_k)
    radda_reasons = []
    if retro_l or is_combust_l:
        radda_reasons.append(f"{lagnesha} ({'retrogradan' if retro_l else ''}{' i ' if retro_l and is_combust_l else ''}{'kombust' if is_combust_l else ''})")
    if retro_k or is_combust_k:
        radda_reasons.append(f"{karyesha} ({'retrogradan' if retro_k else ''}{' i ' if retro_k and is_combust_k else ''}{'kombust' if is_combust_k else ''})")
    results.append(KaryeshaYogaResult(
        "Radda",
        radda,
        f"Ithasala postoji, ali {', '.join(radda_reasons)} - uspjeh nakon poteškoća."
        if radda else "Nema retrogradnosti/kombustije unutar ove Ithasale.",
    ))

    dignity_l, _ = compute_dignity(lagnesha, sign_index_by_planet[lagnesha])
    dignity_k, _ = compute_dignity(karyesha, sign_index_by_planet[karyesha])
    slower_dignity = dignity_l if direct.slower == lagnesha else dignity_k
    faster_dignity = dignity_l if direct.faster == lagnesha else dignity_k
    duparikutha = (
        has_ithasala
        and slower_dignity in ("uzvišen", "vlastiti")
        and faster_dignity not in ("uzvišen", "vlastiti")
    )
    results.append(KaryeshaYogaResult(
        "Duparikutha",
        duparikutha,
        f"Sporija planeta ({direct.slower}) je {slower_dignity}, brža ({direct.faster}) nije - ipak povoljan ishod."
        if duparikutha else "Uvjeti za Duparikutha nisu zadovoljeni.",
    ))

    house_l = _house_of(sign_index_by_planet[lagnesha], asc_sign_index)
    house_k = _house_of(sign_index_by_planet[karyesha], asc_sign_index)
    trik_houses = {6, 8, 12}
    weak_dignities = ("pad", "neprijateljski")
    durupha = (
        has_ithasala
        and house_l in trik_houses and house_k in trik_houses
        and (dignity_l in weak_dignities or retro_l)
        and (dignity_k in weak_dignities or retro_k)
    )
    results.append(KaryeshaYogaResult(
        "Durupha",
        durupha,
        "Lagnesha i Karyesha su oboje u 6./8./12. kući i oslabljeni - nepovoljan ishod unatoč Ithasali."
        if durupha else "Uvjeti za Durupha nisu zadovoljeni.",
    ))

    # --- Duttota (Dutthotha Davira): oboje Lagnesha/Karyesha slabi, ALI jedan
    # od njih ima Ithasalu s TREĆOM, jakom planetom - uspjeh uz pomoć treće strane
    both_weak = (
        (dignity_l in weak_dignities or retro_l or is_combust_l)
        and (dignity_k in weak_dignities or retro_k or is_combust_k)
    )
    duttota_helper = None
    if both_weak:
        for helper_name in TAJIKA_PLANETS:
            if helper_name in (lagnesha, karyesha):
                continue
            helper_lon, helper_retro = positions[helper_name]
            for weak_planet, weak_lon, weak_retro in [(lagnesha, lon_l, retro_l), (karyesha, lon_k, retro_k)]:
                rel = analyze_pair(helper_name, helper_lon, helper_retro, weak_planet, weak_lon, weak_retro)
                if rel.aspect and rel.within_orb and rel.is_applying:
                    helper_dignity, _ = compute_dignity(helper_name, sign_index_by_planet[helper_name])
                    if helper_dignity in ("uzvišen", "vlastiti"):
                        duttota_helper = helper_name
                        break
            if duttota_helper:
                break
    duttota = duttota_helper is not None
    results.append(KaryeshaYogaResult(
        "Duttota",
        duttota,
        f"Lagnesha i Karyesha su oboje slabi, ali {duttota_helper} (jak) formira Ithasalu s jednim od njih - "
        f"uspjeh uz pomoć treće strane."
        if duttota else "Uvjeti za Duttota nisu zadovoljeni (potrebno da su oba slaba, uz jaku treću planetu).",
    ))

    # --- Tambira: brža planeta (u Lagnesha-Karyesha Ithasali) je jaka I na
    # kraju znaka (zadnja 3°) - Ithasala se tek formira/potvrđuje
    tambira = False
    tambira_detail = "Nema izravne Ithasale, Tambira se ne primjenjuje."
    if has_ithasala:
        faster_planet = direct.faster
        faster_lon_val = lon_l if faster_planet == lagnesha else lon_k
        faster_dignity_val = dignity_l if faster_planet == lagnesha else dignity_k
        faster_degree_in_sign = faster_lon_val % 30
        tambira = faster_dignity_val in ("uzvišen", "vlastiti") and faster_degree_in_sign >= 27.0
        tambira_detail = (
            f"Brža planeta ({faster_planet}) je jaka ({faster_dignity_val}) i na kraju znaka "
            f"({faster_degree_in_sign:.1f}°) - Ithasala se upravo potvrđuje."
            if tambira else "Uvjeti za Tambira nisu zadovoljeni (brža planeta nije i jaka i pri kraju znaka)."
        )
    results.append(KaryeshaYogaResult("Tambira", tambira, tambira_detail))

    return results


# ---------------------------------------------------------------------------
# Globalne yoge (cijela karta, ne Lagnesha/Karyesha par) - PROVJERENO kroz
# 5+ neovisnih izvora (varahamihira blogspot, jyotishforgood.com, više
# scribd/pdfcoffee prijepisa K.S. Charaka).
# ---------------------------------------------------------------------------

def compute_ishkavala(sign_index_by_planet: Dict[str, int], asc_sign_index: int) -> bool:
    """Ishkavala (=Ikkavala): SVIH 7 klasičnih planeta u kendri (1,4,7,10) ili panaphari (2,5,8,11)."""
    apoklima = {3, 6, 9, 12}
    for planet in TAJIKA_PLANETS:
        house = _house_of(sign_index_by_planet[planet], asc_sign_index)
        if house in apoklima:
            return False
    return True


def compute_induvara(sign_index_by_planet: Dict[str, int], asc_sign_index: int) -> bool:
    """Induvara: SVIH 7 klasičnih planeta u apoklimi (3,6,9,12)."""
    apoklima = {3, 6, 9, 12}
    for planet in TAJIKA_PLANETS:
        house = _house_of(sign_index_by_planet[planet], asc_sign_index)
        if house not in apoklima:
            return False
    return True


def compute_khallasara(positions: Dict[str, Tuple[float, bool]]) -> bool:
    """
    Khallasara (Hartova definicija - jasnija i provjerljivija od klasične
    "Lagnesha između Mjeseca i druge planete" verzije koju su izvori manje
    dosljedno opisivali): Mjesec ne formira Ithasalu niti s jednom drugom
    planetom.
    """
    moon_lon, moon_retro = positions["Mjesec"]
    for planet in TAJIKA_PLANETS:
        if planet == "Mjesec":
            continue
        p_lon, p_retro = positions[planet]
        rel = analyze_pair("Mjesec", moon_lon, moon_retro, planet, p_lon, p_retro)
        if rel.aspect and rel.within_orb and rel.is_applying:
            return False
    return True
