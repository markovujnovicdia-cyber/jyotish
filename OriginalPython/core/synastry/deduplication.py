"""
Kanonski identitet unakrsnog (sinastrijskog) kontakta - JEDINO mjesto koje
zna kako izgraditi ključ para dva planeta iz DVIJE RAZLIČITE karte.

RAZLOG POSTOJANJA (ispravak stvarne greške): više modula je do sada gradilo
ključ para preko `frozenset({ime_planeta_a, ime_planeta_b})` - BEZ oznake
KOJOJ osobi koji planet pripada. Kako su nazivi planeta (Mars, Venera...)
identični u obje karte, takav ključ:
  1) NE sprječava zamjenu osoba kod traženja "baš tog" unakrsnog para
     (npr. "Saturn osobe A - Merkur osobe B" nasuprot "Merkur osobe A -
     Saturn osobe B" su DVA različita fizička kontakta, ne isti par), i
  2) MOŽE spojiti dva potpuno različita fizička kontakta u jedan "par"
     (npr. "A-Mars -> B-Venera" i "B-Mars -> A-Venera" dijele isti
     frozenset {"Mars","Venera"}, ali to su različiti kontakti).

`contact_key()` niže je person-aware zamjena - svaki modul koji je gradio
frozenset bez oznake osobe (core/synastry/scoring.py,
relationship_significators.py, divisional_synastry.py) prelazi na ovu
funkciju/`find_cross_contact()`.

Ovo je i jedino mjesto koje implementira "role_multiplier" (spec: jedan
fizički planetarni kontakt broji se JEDNOM čak i kad taj planet istodobno
igra više uloga - npr. Darakaraka I vladar 7. kuće) - dodatne uloge SMIJU
povećati važnost već izbrojanog kontakta kroz ograničeni multiplikator, ne
dodati novi neovisan bod.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

MAX_ROLE_MULTIPLIER = 1.25
ONE_ROLE_BONUS = 0.10
TWO_OR_MORE_ROLES_BONUS = 0.15


def contact_key(person_a_planet: str, person_b_planet: str) -> str:
    """
    Jedinstveni, smjer/osoba-svjestan ključ fizičkog kontakta između
    planeta osobe A i planeta osobe B. NIKAD ne koristiti frozenset bez
    oznake osobe za ovu svrhu - vidi napomenu na vrhu datoteke.
    """
    return f"A:{person_a_planet}|B:{person_b_planet}"


def parse_contact_key(key: str) -> Sequence[str]:
    """Obrnuto od contact_key() - vraća (planet_osobe_A, planet_osobe_B), za tekstualne napomene."""
    a_part, b_part = key.split("|")
    return a_part[2:], b_part[2:]


def planet_role_key(person_label: str, planet: str) -> str:
    """Ključ za RoleMap - "A:Saturn", "B:Merkur" itd."""
    return f"{person_label}:{planet}"


@dataclass
class RoleMap:
    """roles_by_key: "A:Saturn" -> ["darakaraka", "7th_lord"]"""
    roles_by_key: Dict[str, List[str]] = field(default_factory=dict)

    def roles_for(self, person_label: str, planet: str) -> List[str]:
        return self.roles_by_key.get(planet_role_key(person_label, planet), [])

    def add_role(self, person_label: str, planet: str, role: str) -> None:
        key = planet_role_key(person_label, planet)
        roles = self.roles_by_key.setdefault(key, [])
        if role not in roles:
            roles.append(role)


def build_role_map(
    darakaraka_a: str, atmakaraka_a: str, seventh_lord_a: str,
    darakaraka_b: str, atmakaraka_b: str, seventh_lord_b: str,
    upapada_lord_a: Optional[str] = None, upapada_lord_b: Optional[str] = None,
    first_lord_a: Optional[str] = None, first_lord_b: Optional[str] = None,
    fifth_lord_a: Optional[str] = None, fifth_lord_b: Optional[str] = None,
    eighth_lord_a: Optional[str] = None, eighth_lord_b: Optional[str] = None,
    eleventh_lord_a: Optional[str] = None, eleventh_lord_b: Optional[str] = None,
    darapada_lord_a: Optional[str] = None, darapada_lord_b: Optional[str] = None,
) -> RoleMap:
    """
    Gradi mapu "koje sve ključne uloge igra svaki planet" po osobi - koristi
    se za role_multiplier (spec 4: dvostruko brojanje istog fizičkog
    planeta kroz više uloga) i za izvještajnu napomenu ("Saturn osobe A je
    istodobno Darakaraka i vladar 7. kuće...").
    """
    role_map = RoleMap()
    assignments = [
        ("A", darakaraka_a, "darakaraka"), ("A", atmakaraka_a, "atmakaraka"),
        ("A", seventh_lord_a, "7th_lord"), ("A", upapada_lord_a, "UL_lord"),
        ("A", first_lord_a, "1st_lord"), ("A", fifth_lord_a, "5th_lord"),
        ("A", eighth_lord_a, "8th_lord"), ("A", eleventh_lord_a, "11th_lord"),
        ("A", darapada_lord_a, "A7_lord"),
        ("B", darakaraka_b, "darakaraka"), ("B", atmakaraka_b, "atmakaraka"),
        ("B", seventh_lord_b, "7th_lord"), ("B", upapada_lord_b, "UL_lord"),
        ("B", first_lord_b, "1st_lord"), ("B", fifth_lord_b, "5th_lord"),
        ("B", eighth_lord_b, "8th_lord"), ("B", eleventh_lord_b, "11th_lord"),
        ("B", darapada_lord_b, "A7_lord"),
    ]
    for person_label, planet, role in assignments:
        if planet:
            role_map.add_role(person_label, planet, role)
    return role_map


def role_multiplier(roles: Sequence[str]) -> float:
    """
    Ograničen multiplikator za kontakt čiji planet(i) nosi(e) više ključnih
    uloga - NE dodaje novi neovisan bod, samo pojačava VEĆ izbrojani
    kontakt (spec 4). Formula iz specifikacije, s gornjim ogradom 1.25.
    """
    distinct_roles = set(roles)
    multiplier = 1.0
    if len(distinct_roles) == 1:
        multiplier += ONE_ROLE_BONUS
    elif len(distinct_roles) >= 2:
        multiplier += TWO_OR_MORE_ROLES_BONUS
    return min(multiplier, MAX_ROLE_MULTIPLIER)


def combined_role_multiplier(role_map: RoleMap, person_a_label: str, planet_a: str, person_b_label: str, planet_b: str) -> float:
    """
    Ukupni role_multiplier za kontakt IZMEĐU dva planeta - uzima planet s
    VIŠE uloga (jači slučaj za "dvostruku funkciju") umjesto zbrajanja
    multiplikatora obiju strana (što bi opet bilo dvostruko brojanje istog
    efekta).
    """
    roles_a = role_map.roles_for(person_a_label, planet_a)
    roles_b = role_map.roles_for(person_b_label, planet_b)
    return max(role_multiplier(roles_a), role_multiplier(roles_b))


def key_from_drishti_contact(c) -> str:
    """
    Person-aware contact_key IZRAVNO iz GrahaDrishtiContact (koristi
    source_person/target_person da odredi koja je strana "A" a koja "B" -
    kontakt može biti zabilježen u bilo kojem smjeru poziva). Zamjenjuje
    stari `frozenset({c.from_planet, c.to_planet})` uzorak koji je brkao
    "A-X aspektira B-Y" s "B-X aspektira A-Y" (dva različita kontakta).
    """
    if c.source_person == "A":
        return contact_key(c.from_planet, c.to_planet)
    return contact_key(c.to_planet, c.from_planet)


def key_from_conjunction(c) -> str:
    """Person-aware contact_key iz ConjunctionContact (person_a_object je UVIJEK osoba A po konstrukciji)."""
    return contact_key(c.person_a_object, c.person_b_object)


def find_cross_contact(contacts, person_a_planet: str, person_b_planet: str):
    """
    Traži TOČNO kontakt gdje je from_planet/source planet OSOBE A jednak
    `person_a_planet` I to_planet/target planet OSOBE B jednak
    `person_b_planet` (ili obrnuto, ako je kontakt zabilježen u B->A
    smjeru) - PROVJERAVAJUĆI source_person/target_person, ne samo naziv
    planeta. Radi na GrahaDrishtiContact listama (source_person/
    target_person/from_planet/to_planet polja).

    Vraća listu pogodaka (obično 0 ili 1 element po smjeru).
    """
    matches = []
    for c in contacts:
        if (
            c.source_person == "A" and c.target_person == "B"
            and c.from_planet == person_a_planet and c.to_planet == person_b_planet
        ):
            matches.append(c)
        elif (
            c.source_person == "B" and c.target_person == "A"
            and c.from_planet == person_b_planet and c.to_planet == person_a_planet
        ):
            matches.append(c)
    return matches


_STRENGTH_TO_TIER = {1.0: "full", 0.75: "three_quarter", 0.5: "half", 0.25: "quarter"}


def drishti_confirmation_strength(contact) -> float:
    """
    "Koliko snažno POTVRĐUJE ovaj Graha Drishti kontakt neku drugu tvrdnju"
    (0-1) - dijeli core.synastry.scoring_config.DRISHTI_WEIGHT (puni aspekt
    = 1.0, djelomični mnogo manje) tako da core/synastry/divisional_synastry.py
    (D1↔D9 prag potvrde) i core/synastry/scoring.py koriste ISTU ljestvicu
    umjesto dvije neovisne, potencijalno nekonzistentne.
    """
    from core.synastry.scoring_config import DRISHTI_WEIGHT
    tier = _STRENGTH_TO_TIER.get(contact.strength, "quarter")
    return DRISHTI_WEIGHT.get(tier, contact.strength)


def conjunction_confirmation_strength(contact) -> float:
    """Isto, za ConjunctionContact - egzaktna konjunkcija broji se kao jaka potvrda, ostale umjereno."""
    return 1.0 if contact.is_exact else 0.6


def find_cross_conjunction(conjunctions, person_a_planet: str, person_b_planet: str):
    """
    Isto kao find_cross_contact, ali za ConjunctionContact - person_a_object
    je PO KONSTRUKCIJI (core/synastry/conjunctions.py) uvijek iz karte
    osobe A, person_b_object uvijek iz karte osobe B, pa nema potrebe za
    dodatnom osoba-provjerom - ali se i dalje NE smije koristiti set
    usporedba {a,b}=={x,y} jer to dopušta zamjenu A/B strane.
    """
    return [
        c for c in conjunctions
        if c.person_a_object == person_a_planet and c.person_b_object == person_b_planet
    ]
