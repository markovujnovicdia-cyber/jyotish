"""
Kuja (Mangal) Dosha - Marsova afflikcija gledano od Ascendenta, Mjeseca i
Venere. Koristi core.houses.whole_sign_house (ista Whole Sign logika kao
natalna karta) i core.planet_strength.compute_dignity (za poništenja) -
ne duplicira izračune.

Namjerno STUPNJEVANA procjena (ne binarno "ima/nema" - spec 2.6):
- 0 od 3 osnove pogođeno -> "nema"
- 1 od 3 -> "blaga"
- 2 od 3 -> "umjerena"
- 3 od 3 -> "jaka"

Kuće koje se smatraju problematičnima su KONFIGURABILNE
(core/synastry/config.py:DEFAULT_KUJA_DOSHA_HOUSES) jer se škole razlikuju
(neke koriste 4 kuće, neke 6 - vidi napomenu u config.py).

Poništenja implementirana (samo ona koja su POUZDANO, ponovljeno
potvrđena u više izvora - vidi napomenu uz svaku):
- Mars u vlastitom ili uzvišenom znaku (klasična, nesporna iznimka)
- Mars u konjunkciji ili aspektu s Jupiterom (klasična, često citirana
  iznimka - Jupiterov "guru drishti" ublažava malefične učinke)
- Uzajamno poništenje: OBOJE imaju Kuja Doshu (vrlo često citirano
  tradicionalno pravilo - "Mangal-Mangal" brak poništava dosha)

NIJE implementirano (nedovoljno pouzdano/konzistentno među izvorima):
poništenja vezana uz specifične varge (D9 Mars pozicija), Nadi Vishesha
iznimke, i "Mars u 12. kući od partnerova Marsa" napredna pravila.
"""

from dataclasses import dataclass
from typing import Dict, List

from core.houses import whole_sign_house
from core.planet_strength import compute_dignity
from core.aspects import compute_graha_drishti
from core.natal import NatalContext
from core.synastry.config import SynastryConfig
from core.synastry.models import KujaDoshaAssessment, KujaDoshaComparison

_BASE_LABELS = ["Ascendent", "Mjesec", "Venera"]


def _base_sign_index(ctx: NatalContext, base: str) -> int:
    if base == "Ascendent":
        return ctx.ascendant_sign_index
    return ctx.positions[base].sign_index


def assess_kuja_dosha(ctx: NatalContext, person_label: str, config: SynastryConfig) -> KujaDoshaAssessment:
    mars_sign_index = ctx.positions["Mars"].sign_index
    houses_involved: Dict[str, int] = {}
    afflicted_from: List[str] = []
    reasons: List[str] = []

    for base in _BASE_LABELS:
        base_sign_idx = _base_sign_index(ctx, base)
        house = whole_sign_house(mars_sign_index, base_sign_idx)
        houses_involved[base] = house
        if house in config.kuja_dosha_houses:
            afflicted_from.append(base)
            reasons.append(f"Mars je u {house}. kući gledano od {base} - unutar konfiguriranog skupa doshakuća.")

    severity_map = {0: "nema", 1: "blaga", 2: "umjerena", 3: "jaka"}
    severity = severity_map[len(afflicted_from)]
    severity_score = {0: 0.0, 1: 33.0, 2: 66.0, 3: 100.0}[len(afflicted_from)]

    cancellations: List[str] = []
    if afflicted_from:
        dignity, _ = compute_dignity("Mars", mars_sign_index)
        if dignity in ("vlastiti", "uzvišen"):
            cancellations.append(
                f"Mars je {dignity} u vlastitoj karti - klasična iznimka koja ublažava ili poništava Kuja Doshu."
            )

        asc_sign_idx = ctx.ascendant_sign_index
        sign_index_map = {name: pos.sign_index for name, pos in ctx.positions.items()}
        relations = compute_graha_drishti(sign_index_map, include_rahu_ketu=False)
        jupiter_aspects_mars = any(
            r.from_planet == "Jupiter" and r.to_planet == "Mars" for r in relations
        )
        jupiter_conjunct_mars = ctx.positions["Jupiter"].sign_index == mars_sign_index
        if jupiter_aspects_mars or jupiter_conjunct_mars:
            cancellations.append(
                "Jupiter aspektira ili je u konjunkciji s Marsom - klasična, često citirana iznimka "
                "('Guru Drishti' ublažava malefične učinke)."
            )

    return KujaDoshaAssessment(
        person_label=person_label,
        houses_involved=houses_involved,
        afflicted_from=afflicted_from,
        severity=severity,
        severity_score=severity_score,
        reasons=reasons,
        possible_cancellations=cancellations,
    )


def compare_kuja_dosha(
    ctx_a: NatalContext, ctx_b: NatalContext, config: SynastryConfig,
) -> KujaDoshaComparison:
    """
    ISPRAVAK (bivša greška): "oboje imaju Kuja Doshu" se ranije tretiralo
    kao POTPUNO uzajamno uravnoteženje bez obzira na razliku u
    intenzitetu (npr. "blaga" kod A, "jaka" kod B) - to je pogrešno
    poništavalo (u core/synastry/scoring.py) cijelu marriage-potential
    kaznu čak i kad je afflikcija kod jedne osobe bila mnogo jača.

    Sada se računa `balancing_fraction = min(severity)/max(severity)`
    (0.0 = nema uravnoteženja, 1.0 = jednak intenzitet kod oboje) -
    scoring.py primjenjuje DJELOMIČNU, ne potpunu kaznu, razmjerno tome
    koliko su intenziteti zapravo asimetrični.
    """
    assessment_a = assess_kuja_dosha(ctx_a, "A", config)
    assessment_b = assess_kuja_dosha(ctx_b, "B", config)

    sev_a, sev_b = assessment_a.severity_score, assessment_b.severity_score
    both_afflicted = sev_a > 0 and sev_b > 0
    balancing_fraction = (min(sev_a, sev_b) / max(sev_a, sev_b)) if both_afflicted else 0.0

    if not both_afflicted:
        note = "Nema uzajamnog uravnoteženja - Kuja Dosha (ako postoji) prisutna je samo kod jedne osobe."
    elif balancing_fraction >= 0.9:
        note = (
            f"Oboje imaju PRIBLIŽNO JEDNAK stupanj Kuja Doshe (A: {assessment_a.severity}, "
            f"B: {assessment_b.severity}) - klasično citirano pravilo ('Mangal-Mangal' brak) "
            "ovdje vrijedi gotovo u potpunosti, afflikcije se uvelike međusobno uravnotežuju."
        )
    else:
        note = (
            f"Oboje imaju određeni stupanj Kuja Doshe, ALI intenzitet NIJE jednak (A: "
            f"{assessment_a.severity}, B: {assessment_b.severity}) - uravnoteženje je SAMO "
            f"DJELOMIČNO (procjena {balancing_fraction * 100:.0f}%), ne potpuno poništenje. "
            "Asimetriju treba zadržati u tumačenju, ne tretirati kao da je dosha kod obje "
            "osobe jednako izražena."
        )

    return KujaDoshaComparison(
        person_a=assessment_a, person_b=assessment_b,
        mutual_balancing=both_afflicted, balancing_note=note,
        balancing_fraction=balancing_fraction,
    )
