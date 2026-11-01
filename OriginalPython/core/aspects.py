"""
Graha Drishti (planetarni aspekti) - klasična Parashari metoda (BPHS).

Svaki planet baca aspekt na kuće brojane OD SEBE (ne od Lagne), inkluzivnim
brojanjem (isti znak = 1., sljedeći = 2., itd.). Snaga aspekta (Drishti
Amsha), prema BPHS:

  - 7. kuća od sebe: PUNI aspekt (100%) - baca ga SVAKI od 7 klasičnih grahe
  - 4. i 8. kuća od sebe: 3/4 aspekt (75%) za sve; Mars ima PUNI (100%)
  - 5. i 9. kuća od sebe: 1/2 aspekt (50%) za sve; Jupiter ima PUNI (100%)
  - 3. i 10. kuća od sebe: 1/4 aspekt (25%) za sve; Saturn ima PUNI (100%)
  - 1., 2., 6., 11., 12. kuća od sebe: NEMA aspekta

Rahu/Ketu su PO ZADANOM isključeni iz izračuna (compute_graha_drishti bez
include_rahu_ketu=True). Izvorno BPHS Drishti poglavlje definira aspekte
samo za 7 klasičnih grahe (Sunce-Saturn); konvencije za Rahu/Ketu (neki
izvori/softveri ih tretiraju kao Saturn, drugi drugačije) međusobno se
razlikuju i nisu jedinstveno potvrđene BPHS-om.

Ako se izričito zatraži (include_rahu_ketu=True), Rahu/Ketu se tretiraju
KAO SATURN (puni aspekt na 3., 7., 10. kuću od sebe) - ovo je NAJČEŠĆA
konvencija u modernom softveru (npr. Jagannatha Hora), ali je NAKNADNA/
sporna konvencija, ne izvorni BPHS - korisnik je to eksplicitno zatražio
uz tu napomenu.
"""

from typing import Dict, List, NamedTuple, Optional

# Redoslijed i skup planeta koji BACAJU i PRIMAJU Graha Drishti PO ZADANOM
# (isključivo 7 klasičnih grahe - vidi napomenu gore). Rahu/Ketu se dodaju
# samo ako se izričito zatraže preko include_rahu_ketu=True.
ASPECTING_PLANETS = ["Sunce", "Mjesec", "Mars", "Merkur", "Jupiter", "Venera", "Saturn"]
_RAHU_KETU = ["Rahu", "Ketu"]

# Bazna snaga aspekta po udaljenosti kuće (1-12, brojano OD planeta koji baca)
_BASE_DRISHTI = {3: 0.25, 4: 0.75, 5: 0.5, 7: 1.0, 8: 0.75, 9: 0.5, 10: 0.25}

# Čitljiva oznaka za prikaz snage aspekta (0.25/0.5/0.75/1.0) - dijele je
# natalni i sinastrijski prikaz Graha Drishti da se ne duplicira u UI kodu.
ASPECT_STRENGTH_LABEL = {1.0: "puni (100%)", 0.75: "3/4 (75%)", 0.5: "1/2 (50%)", 0.25: "1/4 (25%)"}

# Posebni planeti koji na SVOJIM dodatnim kućama bacaju PUNI (100%) aspekt
# umjesto bazne (djelomične) snage
_SPECIAL_FULL_HOUSES = {
    "Mars": {4, 8},
    "Jupiter": {5, 9},
    "Saturn": {3, 10},
}
# Rahu/Ketu "kao Saturn" konvencija (vidi napomenu na vrhu) - koristi se
# SAMO kad je include_rahu_ketu=True
_SPECIAL_FULL_HOUSES_RAHU_KETU = {
    "Rahu": {3, 10},
    "Ketu": {3, 10},
}


class AspectRelation(NamedTuple):
    from_planet: str
    to_planet: str
    house_distance: int  # 1-12, kuća "to_planet" gledano OD "from_planet"
    strength: float       # 0.25 / 0.5 / 0.75 / 1.0


def _strength_for_distance(from_planet: str, distance: int, include_rahu_ketu: bool) -> Optional[float]:
    if distance in _SPECIAL_FULL_HOUSES.get(from_planet, ()):
        return 1.0
    if include_rahu_ketu and distance in _SPECIAL_FULL_HOUSES_RAHU_KETU.get(from_planet, ()):
        return 1.0
    return _BASE_DRISHTI.get(distance)


def is_special_full_aspect(from_planet: str, house_distance: int, include_rahu_ketu: bool = False) -> bool:
    """
    Je li ovaj aspekt planetov POSEBAN puni aspekt (Mars 4./8., Jupiter
    5./9., Saturn 3./10., a s include_rahu_ketu=True i Rahu/Ketu 3./10.) -
    umjesto bazne (djelomične) snage koju bi ta udaljenost inače imala.
    Javna funkcija da core/synastry/scoring.py ne duplicira
    _SPECIAL_FULL_HOUSES tablicu (vidi napomenu na vrhu ove datoteke).
    """
    if house_distance in _SPECIAL_FULL_HOUSES.get(from_planet, ()):
        return True
    if include_rahu_ketu and house_distance in _SPECIAL_FULL_HOUSES_RAHU_KETU.get(from_planet, ()):
        return True
    return False


def compute_graha_drishti(
    from_sign_index: Dict[str, int],
    to_sign_index: Optional[Dict[str, int]] = None,
    include_rahu_ketu: bool = False,
) -> List[AspectRelation]:
    """
    Računa sve aktivne Graha Drishti odnose.

    from_sign_index: {naziv_planeta: sign_index} planeta koji BACAJU aspekt
        (npr. natalni planeti, ili tranzitni planeti za Gochara)
    to_sign_index: {naziv_ili_oznaka: sign_index} META aspekta (npr. natalni
        planeti + Lagna, za Gochara). Ako je None, aspekti se računaju
        UNUTAR from_sign_index (planeti iste karte međusobno - natalna ili
        Varsha karta same sa sobom), i planet ne aspektira sam sebe.
    include_rahu_ketu: ako je True, Rahu/Ketu (ako su prisutni u ulaznim
        mapama) se tretiraju KAO SATURN (puni aspekt 3./7./10.) - vidi
        napomenu na vrhu datoteke o spornosti ove konvencije. PO ZADANOM
        (False) Rahu/Ketu ni bacaju ni primaju aspekt.
    """
    self_mode = to_sign_index is None
    if self_mode:
        to_sign_index = from_sign_index

    aspecting = ASPECTING_PLANETS + _RAHU_KETU if include_rahu_ketu else ASPECTING_PLANETS
    from_planets = [p for p in aspecting if p in from_sign_index]
    to_items = [(label, idx) for label, idx in to_sign_index.items() if self_mode is False or label in aspecting]
    if self_mode:
        to_items = [(label, idx) for label, idx in to_items if label in aspecting]

    relations: List[AspectRelation] = []
    for from_planet in from_planets:
        from_idx = from_sign_index[from_planet]
        for to_label, to_idx in to_items:
            if self_mode and to_label == from_planet:
                continue
            distance = (to_idx - from_idx) % 12 + 1
            strength = _strength_for_distance(from_planet, distance, include_rahu_ketu)
            if strength is not None:
                relations.append(AspectRelation(from_planet, to_label, distance, strength))
    return relations
