"""
Vrsta odnosa (spec 1) - ljubavni/partnerski, bračni, prijateljski,
poslovni, obiteljski, opći.

VAŽNO (spec 1: "vrsta odnosa ne smije mijenjati astronomske položaje,
nego samo izbor i težinu interpretacijskih tema"): ništa u ovoj datoteci
ne dira core.natal/core.houses/core.aspects niti bilo koji od
GrahaDrishtiContact/ConjunctionContact/HouseOverlayRow izračuna. Profili
niže utječu ISKLJUČIVO na:
  1. koje teme/signifikatore core/synastry/report.py istakne PRVE u
     izvještaju (emphasized_houses/planets/significators), i
  2. BLAGU (najviše ±15%) prilagodbu kategorijskih težina u
     core/synastry/scoring.py (category_weight_multipliers, primijenjeno
     na `raw_deviation` PRIJE tanh/gate koraka, tako da gate-ovi i dalje
     ispravno rade na PRILAGOĐENOJ, ne sirovoj vrijednosti).

ISPRAVAK (bivša greška - spec 1): `relationship_type` je ranije bio ČISTO
kozmetički label u izvještaju (report.py ga je samo ispisivao) - bez
ikakvog stvarnog učinka na naglasak ili bodovanje, i UI selectbox
(ui/pages_synastry.py) nije imao eksplicitni zadani indeks niti je bio
scope-an po paru osoba, pa je stara vrijednost (npr. "Prijateljstvo" iz
prijašnjeg para) tiho preživljavala prebacivanje na drugi par. Oboje je
ispravljeno - vidi ui/pages_synastry.py.
"""

from dataclasses import dataclass, field
from typing import Dict, List

RELATIONSHIP_TYPE_KEYS = [
    "ljubavni_partnerski", "bracni", "prijateljski", "poslovni", "obiteljski", "opci",
]

RELATIONSHIP_TYPE_LABELS: Dict[str, str] = {
    "ljubavni_partnerski": "Ljubavni/partnerski odnos",
    "bracni": "Bračni odnos",
    "prijateljski": "Prijateljski odnos",
    "poslovni": "Poslovni odnos",
    "obiteljski": "Obiteljski odnos",
    "opci": "Opći odnos",
}
_LABEL_TO_KEY = {v: k for k, v in RELATIONSHIP_TYPE_LABELS.items()}

DEFAULT_RELATIONSHIP_TYPE = "ljubavni_partnerski"

# Gornja ograda multiplikatora - "blaga" prilagodba, nikad drastična promjena rezultata.
MAX_CATEGORY_EMPHASIS_MULTIPLIER = 1.15
MIN_CATEGORY_EMPHASIS_MULTIPLIER = 0.85


@dataclass
class RelationshipProfile:
    key: str
    label: str
    emphasized_houses: List[int]
    emphasized_planets: List[str]
    emphasized_significators: List[str]   # npr. "darakaraka", "7th_lord", "UL_lord"
    category_weight_multipliers: Dict[str, float] = field(default_factory=dict)
    framing_note: str = ""


RELATIONSHIP_PROFILES: Dict[str, RelationshipProfile] = {
    "ljubavni_partnerski": RelationshipProfile(
        key="ljubavni_partnerski", label=RELATIONSHIP_TYPE_LABELS["ljubavni_partnerski"],
        emphasized_houses=[5, 7, 8, 12],
        emphasized_planets=["Venera", "Mars", "Mjesec"],
        emphasized_significators=["darakaraka", "5th_lord", "7th_lord", "UL_lord"],
        category_weight_multipliers={
            "Privlačnost i kemija": 1.15, "Emocionalna povezanost": 1.10,
            "Bračni potencijal": 1.10, "Karmička/intenzivna povezanost": 1.05,
        },
        framing_note=(
            "Ljubavni/partnerski odnos - naglasak je na romantičnoj i seksualnoj privlačnosti, "
            "emocionalnoj bliskosti i partnerskoj projekciji: 5., 7., 8. i 12. kuća, Venera, Mars, "
            "Mjesec, vladari 5. i 7. kuće, Darakaraka, Upapada Lagna i D9 (Navamsha)."
        ),
    ),
    "bracni": RelationshipProfile(
        key="bracni", label=RELATIONSHIP_TYPE_LABELS["bracni"],
        emphasized_houses=[2, 4, 7, 8],
        emphasized_planets=["Venera", "Mjesec", "Saturn"],
        emphasized_significators=["darakaraka", "7th_lord", "UL_lord", "A7_lord"],
        category_weight_multipliers={
            "Bračni potencijal": 1.15, "Stabilnost": 1.15, "Praktična kompatibilnost": 1.10,
        },
        framing_note=(
            "Bračni odnos - naglasak je na trajnosti, obvezi i praktičnoj/materijalnoj strani "
            "zajedništva: 2., 4., 7. i 8. kuća, vladar 7. kuće, Upapada Lagna, Darapada (A7), Saturn "
            "kao signifikator trajnosti."
        ),
    ),
    "prijateljski": RelationshipProfile(
        key="prijateljski", label=RELATIONSHIP_TYPE_LABELS["prijateljski"],
        emphasized_houses=[3, 7, 11],
        emphasized_planets=["Merkur", "Jupiter"],
        emphasized_significators=["11th_lord", "7th_lord"],
        category_weight_multipliers={
            "Podrška i prijateljstvo": 1.15, "Komunikacija": 1.10,
        },
        framing_note=(
            "Prijateljski odnos - naglasak je na 11. kući (prijateljstvo, zajedničke želje), 3. kući "
            "(razmjena, druženje) i Jupiteru/Merkuru kao signifikatorima podrške i komunikacije."
        ),
    ),
    "poslovni": RelationshipProfile(
        key="poslovni", label=RELATIONSHIP_TYPE_LABELS["poslovni"],
        emphasized_houses=[2, 6, 10, 11],
        emphasized_planets=["Merkur", "Saturn", "Sunce"],
        emphasized_significators=["10th_lord", "11th_lord"],
        category_weight_multipliers={
            "Praktična kompatibilnost": 1.15, "Komunikacija": 1.10, "Stabilnost": 1.05,
        },
        framing_note=(
            "Poslovni odnos - naglasak je na praktičnoj suradnji, statusu i zajedničkim ciljevima: "
            "2., 6., 10. i 11. kuća, Merkur (komunikacija/pregovori), Saturn (disciplina/obveza), "
            "Sunce (autoritet/vodstvo)."
        ),
    ),
    "obiteljski": RelationshipProfile(
        key="obiteljski", label=RELATIONSHIP_TYPE_LABELS["obiteljski"],
        emphasized_houses=[2, 4, 9],
        emphasized_planets=["Mjesec", "Sunce", "Jupiter"],
        emphasized_significators=[],  # 4./9. vladar nije dio core.synastry.deduplication.RoleMap uloga u ovoj fazi
        category_weight_multipliers={
            "Emocionalna povezanost": 1.10, "Podrška i prijateljstvo": 1.10, "Stabilnost": 1.05,
        },
        framing_note=(
            "Obiteljski odnos - naglasak je na emocionalnoj sigurnosti, korijenima i zajedničkim "
            "vrijednostima: 2. i 4. kuća (dom, obitelj), 9. kuća (zajednička vjerovanja), Mjesec i "
            "Sunce kao signifikatori roditeljske/obiteljske dinamike."
        ),
    ),
    "opci": RelationshipProfile(
        key="opci", label=RELATIONSHIP_TYPE_LABELS["opci"],
        emphasized_houses=[1, 7],
        emphasized_planets=[],
        emphasized_significators=["7th_lord"],
        category_weight_multipliers={},
        framing_note=(
            "Opći odnos - bez posebnog naglaska; prikazuje se ravnomjerno cijeli sinastrijski profil "
            "(svih 9 kategorija, bez blage prilagodbe težina)."
        ),
    ),
}


def resolve_relationship_key(key_or_label: str) -> str:
    """Prihvaća i interni ključ (npr. 'bracni') i prikazni label (npr. 'Bračni odnos')."""
    if key_or_label in RELATIONSHIP_PROFILES:
        return key_or_label
    if key_or_label in _LABEL_TO_KEY:
        return _LABEL_TO_KEY[key_or_label]
    return DEFAULT_RELATIONSHIP_TYPE


def get_relationship_profile(key_or_label: str) -> RelationshipProfile:
    return RELATIONSHIP_PROFILES[resolve_relationship_key(key_or_label)]
