"""
Ashtakoota (Kuta) kompatibilnost - tradicionalna usporedba Mjeseca dviju
osoba kroz 8 kuta, ukupno 36 bodova. Koristi core.nakshatra (nakshatra/pada)
i core.constants tablice (NAKSHATRA_GANA/YONI/NADI, RASHI_VARNA/VASHYA_GROUP)
- ne duplicira geometriju, samo primjenjuje Kuta pravila na već izračunate
podatke.

VAŽNA NAPOMENA O POUZDANOSTI (dosljedno stilu ostatka projekta - vidi npr.
core/varga.py, core/tajika.py): neke od 8 kuta imaju JEDNOSTAVNE, nesporne
pravile (Nadi, Bhakoot, Tara), dok druge (Yoni, Vashya, dijelom Gana)
imaju u različitim izvorima/softverima RAZLIČITE detaljne bodovne tablice
(pogotovo za "srednje" - ni prijateljske ni neprijateljske - kombinacije).
Ovdje je korištena POJEDNOSTAVLJENA, ali kategorijski ISPRAVNA verzija
(iste kategorije/parovi kao referentni izvori, ali bez najsitnijih
gradacija koje se međusobno razlikuju) - jasno označeno po kuti niže.
Rezultat treba tumačiti kao orijentacijski, ne kao konačnu autoritativnu
ocjenu - vidi i opću napomenu u specifikaciji (36 bodova NIJE presuda).

VARNA KOOTA - napomena o rodnoj neutralnosti: klasično pravilo je
HIJERARHIJSKO (mladoženjina Varna >= mladenkine). Ova aplikacija namjerno
nema fiksne rodne uloge, pa se za ovu JEDNU kutu (najniže ponderirana,
1 od 36 bodova) koristi red odabira - OSOBA A je referentna "starija"
strana. Bod 0 ovdje NE znači "nekompatibilno", nego samo da B ima viši
Varna rang od A po ovoj tablici - vidi cross_notes u rezultatu.
"""

from dataclasses import dataclass
from typing import List, Tuple

from core.constants import (
    RASHI, RASHI_LORD, RASHI_VARNA, VARNA_RANK, RASHI_VASHYA_GROUP,
    NAKSHATRA_GANA, NAKSHATRA_YONI, NAKSHATRA_NADI,
)
from core.nakshatra import get_nakshatra
from core.planet_strength import NATURAL_FRIENDS, NATURAL_ENEMIES
from core.synastry.models import KutaScore, AshtakootaResult

# --- Tara (2.4/2.5) - nesporna nakshatra-brojevna klasifikacija ---
_TARA_NAMES = {
    1: "Janma", 2: "Sampat", 3: "Vipat", 4: "Kshema", 5: "Pratyak",
    6: "Sadhaka", 7: "Vadha (Naidhana)", 8: "Mitra", 9: "Parama Mitra",
}
_TARA_BAD = {3, 5, 7}

# --- Yoni enemy parovi (7 parova, 14 yonija) - standardna, nesporna lista ---
_YONI_ENEMY_PAIRS = {
    frozenset({"Konj", "Bivol"}), frozenset({"Slon", "Lav"}),
    frozenset({"Ovca", "Majmun"}), frozenset({"Zmija", "Mungos"}),
    frozenset({"Pas", "Jelen"}), frozenset({"Štakor", "Mačka"}),
    frozenset({"Krava", "Tigar"}),
}

# --- Vashya - POJEDNOSTAVLJENA tablica (vidi napomenu na vrhu datoteke) ---
_VASHYA_PARTIAL_PAIRS = {
    frozenset({"Chatushpada", "Manava"}): 1.0,
    frozenset({"Vanachara", "Manava"}): 1.0,
}


def _tara_number(from_index: int, to_index: int) -> int:
    count = (to_index - from_index) % 27 + 1
    return ((count - 1) % 9) + 1


def compute_varna_koota(moon_sign_a: str, moon_sign_b: str) -> KutaScore:
    varna_a, varna_b = RASHI_VARNA[moon_sign_a], RASHI_VARNA[moon_sign_b]
    points = 1.0 if VARNA_RANK[varna_a] >= VARNA_RANK[varna_b] else 0.0
    return KutaScore(
        name="Varna", points=points, max_points=1.0,
        rule_used=f"A={varna_a} (rang {VARNA_RANK[varna_a]}), B={varna_b} (rang {VARNA_RANK[varna_b]}) - "
                   f"bod ako A >= B (vidi napomenu o rodnoj neutralnosti u kodu).",
        table_reference="Varna po elementu znaka (Brahmin>Kshatriya>Vaishya>Shudra)",
        interpretation="Duhovna/vrijednosna usklađenost - najniže ponderirana kuta (1/36).",
        limitation="Klasično hijerarhijska (rodno uvjetovana) - ovdje neutralizirano redom A/B; 0 ne znači nekompatibilnost.",
    )


def compute_vashya_koota(moon_sign_a: str, moon_sign_b: str) -> KutaScore:
    group_a, group_b = RASHI_VASHYA_GROUP[moon_sign_a], RASHI_VASHYA_GROUP[moon_sign_b]
    if group_a == group_b:
        points = 2.0
    else:
        points = _VASHYA_PARTIAL_PAIRS.get(frozenset({group_a, group_b}), 0.0)
    return KutaScore(
        name="Vashya", points=points, max_points=2.0,
        rule_used=f"A skupina={group_a}, B skupina={group_b}.",
        table_reference="5 Vashya skupina (Chatushpada/Manava/Jalachara/Vanachara/Keeta)",
        interpretation="Uzajamni 'utjecaj'/privlačnost - tko na koga prirodno više 'djeluje'.",
        limitation="POJEDNOSTAVLJENA tablica (vidi napomenu na vrhu datoteke) - puna verzija ima više gradacija.",
    )


def compute_tara_koota(nak_index_a: int, nak_index_b: int) -> KutaScore:
    tara_ab = _tara_number(nak_index_a, nak_index_b)
    tara_ba = _tara_number(nak_index_b, nak_index_a)
    points = 0.0
    points += 0.0 if tara_ab in _TARA_BAD else 1.5
    points += 0.0 if tara_ba in _TARA_BAD else 1.5
    return KutaScore(
        name="Tara (Dina)", points=points, max_points=3.0,
        rule_used=f"A→B={_TARA_NAMES[tara_ab]} ({tara_ab}.), B→A={_TARA_NAMES[tara_ba]} ({tara_ba}.).",
        table_reference="9 Tara (brojanje nakšatri, ciklus od 9) - Vipat/Pratyak/Vadha su nepovoljne.",
        interpretation="Opća sreća/dobrobit u odnosu, računato u oba smjera.",
        limitation="Nesporna, standardna metoda.",
    )


def compute_yoni_koota(nak_index_a: int, nak_index_b: int) -> KutaScore:
    yoni_a, _ = NAKSHATRA_YONI[nak_index_a]
    yoni_b, _ = NAKSHATRA_YONI[nak_index_b]
    if yoni_a == yoni_b:
        points = 4.0
    elif frozenset({yoni_a, yoni_b}) in _YONI_ENEMY_PAIRS:
        points = 0.0
    else:
        points = 2.0
    return KutaScore(
        name="Yoni", points=points, max_points=4.0,
        rule_used=f"A yoni={yoni_a}, B yoni={yoni_b}.",
        table_reference="14 tradicionalnih yonija (životinjski simboli), 7 poznatih neprijateljskih parova.",
        interpretation="Fizička/instinktivna kompatibilnost.",
        limitation="POJEDNOSTAVLJENO na 3 razine (isti/neprijatelj/ostalo) - puna tablica ima i 'prijateljske' parove (3 boda).",
    )


def compute_graha_maitri_koota(moon_sign_a: str, moon_sign_b: str) -> KutaScore:
    lord_a, lord_b = RASHI_LORD[moon_sign_a], RASHI_LORD[moon_sign_b]
    if lord_a == lord_b:
        points, category = 5.0, "isti vladar (najbolje)"
    else:
        def _rel(x, y):
            if y in NATURAL_FRIENDS.get(x, set()):
                return "friend"
            if y in NATURAL_ENEMIES.get(x, set()):
                return "enemy"
            return "neutral"

        rel_ab, rel_ba = _rel(lord_a, lord_b), _rel(lord_b, lord_a)
        pair = {rel_ab, rel_ba}
        if pair == {"friend"}:
            points, category = 5.0, "Adhi Mitra (obostrano prijateljstvo)"
        elif "friend" in pair and "enemy" not in pair:
            points, category = 4.0, "Mitra"
        elif pair == {"enemy"}:
            points, category = 0.0, "Adhi Shatru (obostrano neprijateljstvo)"
        elif "enemy" in pair and "friend" not in pair:
            points, category = 1.0, "Shatru"
        else:
            points, category = 3.0, "Sama (neutralno)"
    return KutaScore(
        name="Graha Maitri", points=points, max_points=5.0,
        rule_used=f"Vladar A={lord_a}, vladar B={lord_b} → {category}.",
        table_reference="Kombinacija prirodnog prijateljstva u oba smjera (core.planet_strength.NATURAL_FRIENDS/ENEMIES).",
        interpretation="Mentalna/intelektualna usklađenost, prijateljstvo.",
        limitation="Nesporna kombinacijska logika (5 razina), ponovno koristi postojeću natalnu tablicu prijateljstva.",
    )


def compute_gana_koota(nak_index_a: int, nak_index_b: int) -> KutaScore:
    gana_a, gana_b = NAKSHATRA_GANA[nak_index_a], NAKSHATRA_GANA[nak_index_b]
    if gana_a == gana_b:
        points = 6.0
    elif frozenset({gana_a, gana_b}) == frozenset({"Deva", "Rakshasa"}):
        points = 0.0
    else:
        points = 5.0
    return KutaScore(
        name="Gana", points=points, max_points=6.0,
        rule_used=f"A gana={gana_a}, B gana={gana_b}.",
        table_reference="3 Gane (Deva/Manushya/Rakshasa) po nakšatri.",
        interpretation="Temperament i narav - kako se 'dvije prirode' slažu.",
        limitation="POJEDNOSTAVLJENO na simetričnu tablicu - puni (izvorno smjerni) tablice daju finije gradacije (npr. 1 umjesto 0/5 za neke parove).",
    )


def compute_bhakoot_koota(moon_sign_a: str, moon_sign_b: str) -> Tuple[KutaScore, bool]:
    idx_a, idx_b = RASHI.index(moon_sign_a), RASHI.index(moon_sign_b)
    k = (idx_b - idx_a) % 12
    bad = k in {1, 4, 5, 7, 8, 11}
    points = 0.0 if bad else 7.0
    return KutaScore(
        name="Bhakoot (Rashi)", points=points, max_points=7.0,
        rule_used=f"Udaljenost znakova A→B = {k + 1}. znak (i komplementarno B→A).",
        table_reference="6/8, 5/9 i 2/12 kombinacije su nepovoljne (Bhakoot Dosha).",
        interpretation="Opća bračna/partnerska harmonija, financije i zdravlje zajednice.",
        limitation="Nesporna, standardna metoda.",
    ), bad


def compute_nadi_koota(nak_index_a: int, nak_index_b: int) -> Tuple[KutaScore, bool]:
    nadi_a, nadi_b = NAKSHATRA_NADI[nak_index_a], NAKSHATRA_NADI[nak_index_b]
    same_nadi = nadi_a == nadi_b
    points = 0.0 if same_nadi else 8.0
    return KutaScore(
        name="Nadi", points=points, max_points=8.0,
        rule_used=f"A Nadi={nadi_a}, B Nadi={nadi_b}.",
        table_reference="3 Nadi (Vata/Pitta/Kapha) po nakšatri - najviše ponderirana kuta (8/36).",
        interpretation="Genetska/zdravstvena kompatibilnost potomstva - tradicionalno najvažnija kuta.",
        limitation="Nesporna, standardna metoda.",
    ), same_nadi


def compute_ashtakoota(moon_longitude_a: float, moon_longitude_b: float) -> AshtakootaResult:
    nak_a = get_nakshatra(moon_longitude_a)
    nak_b = get_nakshatra(moon_longitude_b)
    sign_a = RASHI[int(moon_longitude_a % 360.0 // 30)]
    sign_b = RASHI[int(moon_longitude_b % 360.0 // 30)]

    bhakoot_kuta, bhakoot_dosha = compute_bhakoot_koota(sign_a, sign_b)
    nadi_kuta, nadi_dosha = compute_nadi_koota(nak_a.index, nak_b.index)

    kutas = [
        compute_varna_koota(sign_a, sign_b),
        compute_vashya_koota(sign_a, sign_b),
        compute_tara_koota(nak_a.index, nak_b.index),
        compute_yoni_koota(nak_a.index, nak_b.index),
        compute_graha_maitri_koota(sign_a, sign_b),
        compute_gana_koota(nak_a.index, nak_b.index),
        bhakoot_kuta,
        nadi_kuta,
    ]

    cancellations: List[str] = []

    if bhakoot_dosha:
        lord_a, lord_b = RASHI_LORD[sign_a], RASHI_LORD[sign_b]
        if lord_a == lord_b:
            bhakoot_kuta.points = 7.0
            cancellations.append(
                f"Bhakoot Dosha tradicionalno poništena: vladar oba Mjesečeva znaka je isti planet ({lord_a})."
            )
        else:
            cancellations.append(
                "Bhakoot Dosha PRISUTNA (6/8, 5/9 ili 2/12 kombinacija znakova) - nema prepoznate tradicionalne iznimke "
                "(vladari znakova nisu isti planet)."
            )

    if nadi_dosha:
        if nak_a.index == nak_b.index:
            nadi_kuta.points = 8.0
            cancellations.append(
                "Nadi Dosha tradicionalno poništena: oba su u POTPUNO ISTOJ nakšatri (ne samo istoj Nadi kategoriji) - "
                "česta klasična iznimka."
            )
        else:
            cancellations.append(
                "Nadi Dosha PRISUTNA (ista Nadi kategorija, različita nakšatra) - nema prepoznate tradicionalne iznimke."
            )

    total = sum(k.points for k in kutas)
    return AshtakootaResult(
        person_a_moon_nakshatra=nak_a.name, person_b_moon_nakshatra=nak_b.name,
        kutas=kutas, total_points=total, max_points=36.0,
        cancellations=cancellations,
    )
