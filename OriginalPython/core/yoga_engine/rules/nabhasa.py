"""
Svih 32 Nabhasa Yoga (BPHS, poglavlje o Nabhasa Yogama).

Pravila su unakrsno provjerena kroz VIŠE neovisnih prijepisa/komentara BPHS-a
(astro121.com "Chapter 14 - Nabhasa Yogas", sanatanveda.com, vedicmystics.com,
astrojyoti.com) jer mi točan raspored za sve podskupine (naročito Akriti
"lučna"/"oblik" skupina - Hala/Vapi/Yupa/Shara/Shakti/Danda/Nauka/Kuta/
Chatra/Chapa/Ardhachandra) nije bio dovoljno siguran iz sjećanja da bih ga
proglasio provjerenim bez unakrsne provjere (zahtjev #2). Svi izvori se
slažu oko sljedeće strukture:

Koristi se ISKLJUČIVO 7 klasičnih graha (Sunce...Saturn) - NIKAD Rahu/Ketu
(zahtjev #7).

A) Ashraya (3): SVIH 7 planeta u istom TIPU znaka
   - Rajju: svi u pokretnim (Chara) znakovima (Ovan/Rak/Vaga/Jarac)
   - Musala: svi u nepokretnim (Sthira) znakovima (Bik/Lav/Škorpion/Vodenjak)
   - Nala: svi u dvostrukim (Dwiswabhava) znakovima (Blizanci/Djevica/Strijelac/Ribe)

B) Dala (2): sve 4 kendre (1/4/7/10) zauzete, ISKLJUČIVO jednom vrstom planeta
   - Mala: sve kendre zauzete ISKLJUČIVO dobrotvorima
   - Sarpa: sve kendre zauzete ISKLJUČIVO zlotvorima

C) Akriti (20) - PRIORITET: specifičnija formacija uvijek ima prednost pred
   generičkom (zahtjev #8) - vidi komentare kod Kamala/Ardhachandra:
   - Gada: sve 7 planeta ISKLJUČIVO u 2 SUSJEDNE kendre (1&4, 4&7, 7&10, 10&1)
   - Sakata: ISKLJUČIVO u 1. i 7. (obje zauzete)
   - Vihaga: ISKLJUČIVO u 4. i 10. (obje zauzete)
   - Vajra: dobrotvori ISKLJUČIVO u 1.+7., zlotvori ISKLJUČIVO u 4.+10.
   - Yava: zlotvori ISKLJUČIVO u 1.+7., dobrotvori ISKLJUČIVO u 4.+10.
   - Kamala: sve 4 kendre zauzete, MIJEŠANO (generički slučaj - SAMO ako
     Mala/Sarpa/Vajra/Yava ne odgovaraju)
   - Vapi: ISKLJUČIVO u 2.+5.+8.+11. (sve 4 zauzete) ILI ISKLJUČIVO u
     3.+6.+9.+12. (sve 4 zauzete)
   - Sringataka: ISKLJUČIVO u 1.+5.+9. (trikona, sve 3 zauzete)
   - Hala: ISKLJUČIVO u 2.+6.+10. ILI 3.+7.+11. ILI 4.+8.+12. (preostale 3
     "trine" skupine osim 1-5-9, sve 3 zauzete)
   - Yupa: ISKLJUČIVO u 1.-4. (4 uzastopne kuće od Lagne)
   - Sara (Ishu): ISKLJUČIVO u 4.-7.
   - Sakti: ISKLJUČIVO u 7.-10.
   - Danda: ISKLJUČIVO u 10.-1.
   - Nauka: TOČNO po jedan planet u SVAKOJ od 7 uzastopnih kuća 1.-7.
   - Kuta: TOČNO po jedan planet u SVAKOJ od 7 uzastopnih kuća 4.-10.
   - Chatra: TOČNO po jedan planet u SVAKOJ od 7 uzastopnih kuća 7.-1.
   - Chapa (Dhanus): TOČNO po jedan planet u SVAKOJ od 7 uzastopnih kuća 10.-4.
   - Ardhachandra: TOČNO po jedan planet u 7 uzastopnih kuća koje NE počinju
     kendrom (generički slučaj - SAMO ako Nauka/Kuta/Chatra/Chapa ne odgovaraju)
   - Chakra: sve 6 NEPARNIH kuća (1,3,5,7,9,11) zauzete (bar 1 planet svaka,
     preostali 7. planet dijeli jednu od njih)
   - Samudra: sve 6 PARNIH kuća (2,4,6,8,10,12) zauzete (isto)

D) Sankhya (7) - INFORMATIVNA/bazna klasifikacija (zahtjev #8: ne prikazuje
   se kao "iznenadni dodatni nalaz" pored specifičnije Akriti/Ashraya/Dala
   yoge, jer TOČNO JEDNA od ovih 7 je UVIJEK aktivna u svakoj karti - broji
   se broj RAZLIČITIH znakova koje zauzima 7 klasičnih graha):
   1 znak=Gola, 2=Yuga, 3=Sula, 4=Kedara, 5=Pasha, 6=Dama, 7=Vina (Vallaki)
"""

from typing import Dict, List

from core.yoga_engine.context import ChartContext, CLASSICAL_SEVEN, house_from
from core.yoga_engine.models import DebugLog, YogaDefinition, YogaResult, ReferencePoint
from core.yoga_engine.registry import register
from core.yoga_engine.strength import compute_planet_yoga_strength, classify_status

_SIGN_TYPE = {0: "Chara (pokretan)", 1: "Sthira (nepokretan)", 2: "Dwiswabhava (dvostruk)"}


def _sign_type_of(sign_index: int) -> str:
    return _SIGN_TYPE[sign_index % 3]


def _houses_occupied(chart: ChartContext) -> Dict[int, List[str]]:
    occ: Dict[int, List[str]] = {h: [] for h in range(1, 13)}
    for p in CLASSICAL_SEVEN:
        occ[chart.house_of(p)].append(p)
    return occ


def _confined_to(occ: Dict[int, List[str]], houses: List[int]) -> bool:
    """Svih 7 planeta ISKLJUČIVO u zadanim kućama (nema planeta van skupa)."""
    outside = sum(len(occ[h]) for h in occ if h not in houses)
    return outside == 0


def _all_occupied(occ: Dict[int, List[str]], houses: List[int]) -> bool:
    """Svaka od zadanih kuća ima BAR jedan planet."""
    return all(len(occ[h]) >= 1 for h in houses)


def _select(group_fn, yoga_id: str):
    """
    Omotač oko funkcije koja računa VIŠE povezanih yoga odjednom (dijele
    istu skupu occupancy provjeru) - registry.run_all_yogas poziva SVAKI
    registrirani id zasebno, pa svaki registrirani id smije vratiti SAMO
    svoj vlastiti rezultat (inače bi se cijela grupa dodala u finalnu
    listu jednom PO SVAKOM registriranom id-u iz te grupe = duplikati).
    """
    def wrapper(chart: ChartContext) -> List[YogaResult]:
        return [r for r in group_fn(chart) if r.id == yoga_id]
    return wrapper


def _result(yid, name, sanskrit, present, planets, houses, category, reference, log, reasons,
            strength=None, favorable=True, variant=""):
    if strength is None:
        strength = 60.0 if present else 0.0
    return YogaResult(
        id=yid, name=name, sanskrit_name=sanskrit, transliteration=name, present=present,
        category=category, planets=planets, houses=houses, reference=reference,
        strength=round(strength, 1), status=classify_status(present, strength), reasons=reasons,
        source="BPHS", debug_log=log.lines, favorable=favorable, variant=variant,
    )


# ---------------------------------------------------------------------------
# A) Ashraya (3)
# ---------------------------------------------------------------------------

def _make_ashraya_rule(yoga_id: str, name: str, sanskrit: str, type_index: int):
    def rule(chart: ChartContext) -> List[YogaResult]:
        log = DebugLog()
        types = {p: _sign_type_of(chart.sign_index(p)) for p in CLASSICAL_SEVEN}
        target = _SIGN_TYPE[type_index]
        all_match = all(t == target for t in types.values())
        for p, t in types.items():
            log.check(f"{p} u {target}nom znaku", t == target, chart.positions[p].sign)
        log.result(all_match)
        reasons = [f"Svih 7 klasičnih graha je u {target}nim znakovima."] if all_match else []
        return [_result(
            yoga_id, name, sanskrit, all_match, list(CLASSICAL_SEVEN) if all_match else [], [],
            "Nabhasa - Ashraya", ReferencePoint.LAGNA.value, log, reasons,
            strength=65.0 if all_match else 0.0,
        )]
    return rule


for _id, _name, _sanskrit, _tidx in [
    ("rajju", "Rajju Yoga", "रज्जु योग", 0),
    ("musala", "Musala Yoga", "मुसल योग", 1),
    ("nala", "Nala Yoga", "नल योग", 2),
]:
    register(YogaDefinition(
        id=_id, sanskrit_name=_sanskrit, transliteration=_name, hr_name=_name,
        hr_description="Svih 7 klasičnih graha u istom tipu znaka (pokretan/nepokretan/dvostruk).",
        category="Nabhasa - Ashraya", source="BPHS", reference_point=ReferencePoint.LAGNA.value,
    ))(_make_ashraya_rule(_id, _name, _sanskrit, _tidx))


# ---------------------------------------------------------------------------
# B) Dala (2) + Akriti kendra-podskupina (Gada/Sakata/Vihaga/Vajra/Yava/Kamala)
#    - implementirano ZAJEDNO jer dijele istu provjeru "sve 4 kendre pune"
#    i moraju poštovati prioritet specifičnije formacije (zahtjev #8).
# ---------------------------------------------------------------------------

_KENDRA = [1, 4, 7, 10]
_ADJACENT_KENDRA_PAIRS = [(1, 4), (4, 7), (7, 10), (10, 1)]


def _dala_group(chart: ChartContext) -> List[YogaResult]:
    """
    Mala/Sarpa (Dala skupina) - NAMJERNO drugačiji uvjet od Akriti Kamala/
    Vajra/Yava: traži se SAMO da su sve 4 kendre zauzete i "čiste" (svaki
    zauzetnik iste vrste), BEZ zahtjeva da su preostala 3 planeta (koja su,
    ako je "čistoća" ispunjena, nužno druge vrste) izbačena izvan kendri -
    to bi za Mala bilo LOGIČKI NEMOGUĆE (samo 4 od 7 klasičnih graha su
    prirodni dobrotvori, pa "svih 7 unutar kendri, sve dobrotvor" nikad ne
    bi moglo biti zadovoljeno). Ovo je RAZLOG zašto su Mala/Sarpa vlastita,
    manja "Dala" kategorija (2 yoge), odvojena od "Akriti" (20) - vidi
    napomenu na vrhu datoteke.
    """
    log = DebugLog()
    occ = _houses_occupied(chart)
    all_four_full = _all_occupied(occ, _KENDRA)
    log.check("Sve 4 kendre (1/4/7/10) zauzete", all_four_full)

    mala = sarpa = False
    if all_four_full:
        mala = all(chart.is_natural_benefic(p) for h in _KENDRA for p in occ[h])
        sarpa = all(chart.is_natural_malefic(p) for h in _KENDRA for p in occ[h])
    log.check("Sve kendre isključivo dobrotvori (Mala)", mala)
    log.check("Sve kendre isključivo zlotvori (Sarpa)", sarpa)

    kendra_planets = [p for h in _KENDRA for p in occ[h]]

    def _dala_result(yid, name, sanskrit, present, reasons, strength, favorable):
        return _result(yid, name, sanskrit, present, kendra_planets if present else [],
                        sorted(_KENDRA) if present else [], "Nabhasa - Dala",
                        ReferencePoint.LAGNA.value, log, reasons, strength, favorable)

    return [
        _dala_result("mala_yoga", "Mala Yoga", "माला योग", mala,
                     ["Sve 4 kendre zauzete isključivo prirodnim dobrotvorima."], 70.0, True),
        _dala_result("sarpa_yoga", "Sarpa Yoga", "सर्प योग", sarpa,
                     ["Sve 4 kendre zauzete isključivo prirodnim zlotvorima."], 55.0, False),
    ]


def _kendra_group(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    occ = _houses_occupied(chart)
    all_four_full = _all_occupied(occ, _KENDRA)
    kendra_only = _confined_to(occ, _KENDRA)
    log.check("Sve 4 kendre (1/4/7/10) zauzete", all_four_full)
    log.check("SVI planeti unutar kendri (nitko izvan)", kendra_only)

    results: List[YogaResult] = []

    def _kendra_result(yid, name, sanskrit, present, planets, reasons, strength, favorable=True):
        return _result(yid, name, sanskrit, present, planets, sorted(set(chart.house_of(p) for p in planets)) if present else [],
                        "Nabhasa - Akriti (Kendra)", ReferencePoint.LAGNA.value, log, reasons, strength, favorable)

    vajra = yava = False
    if all_four_full and kendra_only:
        h1_benefic = all(chart.is_natural_benefic(p) for p in occ[1])
        h7_benefic = all(chart.is_natural_benefic(p) for p in occ[7])
        h4_malefic = all(chart.is_natural_malefic(p) for p in occ[4])
        h10_malefic = all(chart.is_natural_malefic(p) for p in occ[10])
        h1_malefic = all(chart.is_natural_malefic(p) for p in occ[1])
        h7_malefic = all(chart.is_natural_malefic(p) for p in occ[7])
        h4_benefic = all(chart.is_natural_benefic(p) for p in occ[4])
        h10_benefic = all(chart.is_natural_benefic(p) for p in occ[10])

        vajra = h1_benefic and h7_benefic and h4_malefic and h10_malefic
        yava = (not vajra) and h1_malefic and h7_malefic and h4_benefic and h10_benefic

    all_kendra_planets = [p for h in _KENDRA for p in occ[h]] if all_four_full and kendra_only else []
    results.append(_kendra_result("vajra_yoga", "Vajra Yoga", "वज्र योग", vajra, all_kendra_planets,
                                   ["Dobrotvori u 1./7., zlotvori u 4./10. - SVIH 7 planeta unutar sve 4 kendre."], 65.0))
    results.append(_kendra_result("yava_yoga", "Yava Yoga", "यव योग", yava, all_kendra_planets,
                                   ["Zlotvori u 1./7., dobrotvori u 4./10. - SVIH 7 planeta unutar sve 4 kendre."], 55.0))

    kamala = all_four_full and kendra_only and not (vajra or yava)
    log.note(f"Kamala (generička) provjerava se SAMO ako Vajra/Yava ne odgovaraju - ovdje: {kamala}")
    results.append(_kendra_result(
        "kamala_yoga", "Kamala Yoga", "कमल योग", kamala, all_kendra_planets,
        ["SVIH 7 planeta unutar sve 4 kendre, miješano - ne odgovara specifičnijoj Vajra/Yava formaciji."] if kamala else [],
        60.0,
    ))

    # Gada (2 susjedne kendre) / Sakata (1&7) / Vihaga (4&10) - SAMO ako
    # TOČNO 2 kendre imaju planete, preostale 2 su prazne (jasno odvojeno od
    # gornje "sve 4 pune" skupine pa nema preklapanja).
    filled_kendra = [h for h in _KENDRA if occ[h]]
    exactly_two = len(filled_kendra) == 2 and kendra_only and _confined_to(occ, filled_kendra)
    pair = tuple(sorted(filled_kendra)) if exactly_two else None
    log.check("Točno 2 kendre pune, ostale 2 kendre i sve ne-kendre prazne", exactly_two, str(pair) if pair else "-")

    gada = exactly_two and pair in [(1, 4), (4, 7), (7, 10), (1, 10)]
    sakata = exactly_two and pair == (1, 7)
    vihaga = exactly_two and pair == (4, 10)
    two_kendra_planets = [p for h in (pair or ()) for p in occ[h]]

    results.append(_kendra_result("gada_yoga", "Gada Yoga", "गद योग", gada, two_kendra_planets,
                                   [f"Svih 7 planeta isključivo u {pair[0]}. i {pair[1]}. kući (susjedne kendre)."] if gada else [], 60.0))
    results.append(_kendra_result("sakata_yoga", "Sakata Yoga", "शकट योग", sakata, two_kendra_planets,
                                   ["Svih 7 planeta isključivo u 1. i 7. kući."] if sakata else [], 30.0, favorable=False))
    results.append(_kendra_result("vihaga_yoga", "Vihaga Yoga", "विहग योग", vihaga, two_kendra_planets,
                                   ["Svih 7 planeta isključivo u 4. i 10. kući."] if vihaga else [], 35.0, favorable=False))

    return results


def _register_kendra_group_defs():
    defs = [
        ("mala_yoga", "Mala Yoga", "माला योग", "Nabhasa - Dala", True, "Sve 4 kendre isključivo dobrotvori."),
        ("sarpa_yoga", "Sarpa Yoga", "सर्प योग", "Nabhasa - Dala", False, "Sve 4 kendre isključivo zlotvori."),
        ("vajra_yoga", "Vajra Yoga", "वज्र योग", "Nabhasa - Akriti", True, "Dobrotvori 1./7., zlotvori 4./10."),
        ("yava_yoga", "Yava Yoga", "यव योग", "Nabhasa - Akriti", True, "Zlotvori 1./7., dobrotvori 4./10."),
        ("kamala_yoga", "Kamala Yoga", "कमल योग", "Nabhasa - Akriti", True, "Sve 4 kendre zauzete, miješano (generički slučaj)."),
        ("gada_yoga", "Gada Yoga", "गद योग", "Nabhasa - Akriti", True, "Svih 7 planeta u 2 susjedne kendre."),
        ("sakata_yoga", "Sakata Yoga", "शकट योग", "Nabhasa - Akriti", False, "Svih 7 planeta isključivo u 1. i 7. kući."),
        ("vihaga_yoga", "Vihaga Yoga", "विहग योग", "Nabhasa - Akriti", False, "Svih 7 planeta isključivo u 4. i 10. kući."),
    ]
    for _id, _name, _sanskrit, _cat, _fav, _desc in defs:
        source_fn = _dala_group if _id in ("mala_yoga", "sarpa_yoga") else _kendra_group
        register(YogaDefinition(
            id=_id, sanskrit_name=_sanskrit, transliteration=_name, hr_name=_name, hr_description=_desc,
            category=_cat, source="BPHS", reference_point=ReferencePoint.LAGNA.value, favorable=_fav,
        ))(_select(source_fn, _id))


_register_kendra_group_defs()


# ---------------------------------------------------------------------------
# C) Vapi / Sringataka / Hala - "trine"/"kendra-medusobno" skupine
# ---------------------------------------------------------------------------

def _confinement_rule(yoga_id, name, sanskrit, house_options: List[List[int]], desc, favorable=True):
    def rule(chart: ChartContext) -> List[YogaResult]:
        log = DebugLog()
        occ = _houses_occupied(chart)
        matched = None
        for houses in house_options:
            ok = _confined_to(occ, houses) and _all_occupied(occ, houses)
            log.check(f"Svih 7 isključivo u {houses} (sve zauzete)", ok)
            if ok:
                matched = houses
                break
        present = matched is not None
        log.result(present)
        planets = [p for h in (matched or []) for p in occ[h]]
        reasons = [f"Svih 7 klasičnih graha isključivo u kućama {matched}."] if present else []
        return [_result(yoga_id, name, sanskrit, present, planets, matched or [], "Nabhasa - Akriti",
                         ReferencePoint.LAGNA.value, log, reasons, strength=55.0 if present else 0.0, favorable=favorable)]
    register(YogaDefinition(
        id=yoga_id, sanskrit_name=sanskrit, transliteration=name, hr_name=name, hr_description=desc,
        category="Nabhasa - Akriti", source="BPHS", reference_point=ReferencePoint.LAGNA.value, favorable=favorable,
    ))(rule)


_confinement_rule("sringataka_yoga", "Sringataka Yoga", "शृंगाटक योग", [[1, 5, 9]],
                   "Svih 7 planeta isključivo u trikona kućama (1./5./9.).")
_confinement_rule("hala_yoga", "Hala Yoga", "हल योग", [[2, 6, 10], [3, 7, 11], [4, 8, 12]],
                   "Svih 7 planeta isključivo u jednoj od preostale 3 'trine' skupine kuća.", favorable=False)
_confinement_rule("vapi_yoga", "Vapi Yoga", "वापी योग", [[2, 5, 8, 11], [3, 6, 9, 12]],
                   "Svih 7 planeta isključivo u panaphara (2/5/8/11) ILI apoklima (3/6/9/12) kućama.")


# ---------------------------------------------------------------------------
# C) 4-uzastopne-kuće skupina: Yupa/Sara/Sakti/Danda
# ---------------------------------------------------------------------------

def _four_consecutive(start_house: int) -> List[int]:
    return [((start_house - 1 + i) % 12) + 1 for i in range(4)]


for _id, _name, _sanskrit, _start, _desc in [
    ("yupa_yoga", "Yupa Yoga", "यूप योग", 1, "Svih 7 planeta isključivo u 4 uzastopne kuće počevši od Lagne (1.-4.)."),
    ("sara_yoga", "Sara Yoga", "शर योग", 4, "Svih 7 planeta isključivo u 4 uzastopne kuće počevši od 4. (4.-7.)."),
    ("sakti_yoga", "Sakti Yoga", "शक्ति योग", 7, "Svih 7 planeta isključivo u 4 uzastopne kuće počevši od 7. (7.-10.)."),
    ("danda_yoga", "Danda Yoga", "दण्ड योग", 10, "Svih 7 planeta isključivo u 4 uzastopne kuće počevši od 10. (10.-1.).", ),
]:
    _confinement_rule(_id, _name, _sanskrit, [_four_consecutive(_start)], _desc,
                       favorable=(_id not in ("sakti_yoga", "danda_yoga")))


# ---------------------------------------------------------------------------
# C) 7-uzastopnih-kuća skupina, "jedan-po-jedan" oblik: Nauka/Kuta/Chatra/
#    Chapa (počinju TOČNO na kendri) + Ardhachandra (generički - počinje
#    izvan kendre, zahtjev #8 prioriteta).
# ---------------------------------------------------------------------------

def _seven_consecutive(start_house: int) -> List[int]:
    return [((start_house - 1 + i) % 12) + 1 for i in range(7)]


def _one_each_rule(chart: ChartContext, houses: List[int], occ: Dict[int, List[str]]) -> bool:
    if not _confined_to(occ, houses):
        return False
    if not _all_occupied(occ, houses):
        return False
    return True  # 7 planeta, 7 kuća sve pune, nitko izvan -> nužno "jedan po jedan" (uz najviše jedno mjesto s 2)


_NAMED_SEVEN_STARTS = {1: "nauka_yoga", 4: "kuta_yoga", 7: "chatra_yoga", 10: "chapa_yoga"}
_NAMED_SEVEN_META = {
    "nauka_yoga": ("Nauka Yoga", "नौका योग", "1.-7."),
    "kuta_yoga": ("Kuta Yoga", "कूट योग", "4.-10."),
    "chatra_yoga": ("Chatra Yoga", "छत्र योग", "7.-1."),
    "chapa_yoga": ("Chapa Yoga (Dhanus)", "चाप योग", "10.-4."),
}


def _seven_house_group(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    occ = _houses_occupied(chart)
    results = []
    matched_named = None
    for start, yid in _NAMED_SEVEN_STARTS.items():
        houses = _seven_consecutive(start)
        ok = _one_each_rule(chart, houses, occ)
        log.check(f"{_NAMED_SEVEN_META[yid][0]} ({_NAMED_SEVEN_META[yid][2]})", ok)
        name, sanskrit, _ = _NAMED_SEVEN_META[yid]
        planets = [p for h in houses for p in occ[h]] if ok else []
        reasons = [f"Svih 7 planeta pokriva uzastopne kuće {houses[0]}.-{houses[-1]}. (redom od kendre), po jedan svaka."] if ok else []
        results.append(_result(yid, name, sanskrit, ok, planets, houses if ok else [], "Nabhasa - Akriti",
                                ReferencePoint.LAGNA.value, log, reasons, strength=60.0 if ok else 0.0))
        if ok:
            matched_named = yid

    # Ardhachandra - generički, SAMO ako nijedan od gornja 4 (koji počinju na kendri) ne odgovara,
    # a POSTOJI 7-uzastopni prozor koji počinje na NE-kendri i pokriva sve.
    ardhachandra_present = False
    ach_houses: List[int] = []
    if matched_named is None:
        for start in (2, 3, 5, 6, 8, 9, 11, 12):
            houses = _seven_consecutive(start)
            if _one_each_rule(chart, houses, occ):
                ardhachandra_present = True
                ach_houses = houses
                break
    log.check("Ardhachandra (7 uzastopnih od NE-kendre, samo ako Nauka/Kuta/Chatra/Chapa ne odgovaraju)", ardhachandra_present)
    ach_planets = [p for h in ach_houses for p in occ[h]] if ardhachandra_present else []
    results.append(_result(
        "ardhachandra_yoga", "Ardhachandra Yoga", "अर्धचन्द्र योग", ardhachandra_present, ach_planets,
        ach_houses, "Nabhasa - Akriti", ReferencePoint.LAGNA.value, log,
        [f"Svih 7 planeta pokriva uzastopne kuće {ach_houses[0]}.-{ach_houses[-1]}. (počevši izvan kendre)."] if ardhachandra_present else [],
        strength=55.0 if ardhachandra_present else 0.0,
    ))
    return results


for _yid in list(_NAMED_SEVEN_STARTS.values()) + ["ardhachandra_yoga"]:
    if _yid == "ardhachandra_yoga":
        _name, _sanskrit, _span = "Ardhachandra Yoga", "अर्धचन्द्र योग", "7 uzastopnih kuća počevši izvan kendre"
    else:
        _name, _sanskrit, _span = _NAMED_SEVEN_META[_yid]
    register(YogaDefinition(
        id=_yid, sanskrit_name=_sanskrit, transliteration=_name, hr_name=_name,
        hr_description=f"Svih 7 klasičnih graha pokriva (po jedan) 7 uzastopnih kuća: {_span}.",
        category="Nabhasa - Akriti", source="BPHS", reference_point=ReferencePoint.LAGNA.value,
    ))(_select(_seven_house_group, _yid))


# ---------------------------------------------------------------------------
# C) Chakra / Samudra - naizmjenične (neparne/parne) kuće
# ---------------------------------------------------------------------------

def _make_odd_even_rule(yoga_id, name, sanskrit, houses):
    def rule(chart: ChartContext) -> List[YogaResult]:
        log = DebugLog()
        occ = _houses_occupied(chart)
        confined = _confined_to(occ, houses)
        covered = _all_occupied(occ, houses)
        present = confined and covered
        log.check(f"Svih 7 isključivo u {houses}, svih 6 kuća zauzeto", present)
        log.result(present)
        planets = [p for h in houses for p in occ[h]] if present else []
        reasons = [f"Svih 7 planeta pokriva svih 6 kuća {houses} (barem po jedan svaka)."] if present else []
        return [_result(yoga_id, name, sanskrit, present, planets, houses if present else [], "Nabhasa - Akriti",
                         ReferencePoint.LAGNA.value, log, reasons, strength=65.0 if present else 0.0)]
    return rule


register(YogaDefinition(
    id="chakra_yoga", sanskrit_name="चक्र योग", transliteration="Chakra Yoga", hr_name="Chakra Yoga",
    hr_description="Svih 7 klasičnih graha pokriva svih 6 neparnih kuća (1,3,5,7,9,11).",
    category="Nabhasa - Akriti", source="BPHS", reference_point=ReferencePoint.LAGNA.value,
))(_make_odd_even_rule("chakra_yoga", "Chakra Yoga", "चक्र योग", [1, 3, 5, 7, 9, 11]))

register(YogaDefinition(
    id="samudra_yoga", sanskrit_name="समुद्र योग", transliteration="Samudra Yoga", hr_name="Samudra Yoga",
    hr_description="Svih 7 klasičnih graha pokriva svih 6 parnih kuća (2,4,6,8,10,12).",
    category="Nabhasa - Akriti", source="BPHS", reference_point=ReferencePoint.LAGNA.value,
))(_make_odd_even_rule("samudra_yoga", "Samudra Yoga", "समुद्र योग", [2, 4, 6, 8, 10, 12]))


# ---------------------------------------------------------------------------
# D) Sankhya (7) - bazna klasifikacija po broju RAZLIČITIH znakova
# ---------------------------------------------------------------------------

_SANKHYA_BY_COUNT = {
    1: ("gola_yoga", "Gola Yoga", "गोल योग"),
    2: ("yuga_yoga", "Yuga Yoga", "युग योग"),
    3: ("sula_yoga", "Sula Yoga", "शूल योग"),
    4: ("kedara_yoga", "Kedara Yoga", "केदार योग"),
    5: ("pasha_yoga", "Pasha Yoga", "पाश योग"),
    6: ("dama_yoga", "Dama Yoga", "दाम योग"),
    7: ("vina_yoga", "Vina Yoga (Vallaki)", "वीणा योग"),
}


def _sankhya_group(chart: ChartContext) -> List[YogaResult]:
    log = DebugLog()
    distinct_signs = sorted(set(chart.sign_index(p) for p in CLASSICAL_SEVEN))
    n = len(distinct_signs)
    log.note(f"Broj RAZLIČITIH znakova koje zauzima 7 klasičnih graha: {n}")
    results = []
    for count, (yid, name, sanskrit) in _SANKHYA_BY_COUNT.items():
        present = (count == n)
        planets = list(CLASSICAL_SEVEN) if present else []
        reasons = ([f"7 klasičnih graha zauzima točno {n} različit(ih) znak(ova)."]
                   if present else [])
        results.append(YogaResult(
            id=yid, name=name, sanskrit_name=sanskrit, transliteration=name, present=present,
            category="Nabhasa - Sankhya (bazna klasifikacija)", planets=planets, houses=[],
            reference=ReferencePoint.LAGNA.value, strength=50.0 if present else 0.0,
            status=classify_status(present, 50.0 if present else 0.0), reasons=reasons,
            source="BPHS", debug_log=log.lines,
            review_note=(
                "Sankhya klasifikacija je UVIJEK aktivna za točno jednu od 7 varijanti u svakoj "
                "karti (nije rijedak 'nalaz' kao Akriti/Ashraya/Dala yoge) - prikazuje se kao "
                "bazna informacija, ne kao dodatna postignuta yoga (zahtjev #8)."
            ),
        ))
    return results


for _count, (_yid, _name, _sanskrit) in _SANKHYA_BY_COUNT.items():
    register(YogaDefinition(
        id=_yid, sanskrit_name=_sanskrit, transliteration=_name, hr_name=_name,
        hr_description=f"7 klasičnih graha zauzima točno {_count} različit(ih) znak(ova) - bazna Sankhya klasifikacija.",
        category="Nabhasa - Sankhya (bazna klasifikacija)", source="BPHS", reference_point=ReferencePoint.LAGNA.value,
    ))(_select(_sankhya_group, _yid))
