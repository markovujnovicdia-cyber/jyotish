"""
Centralna konfiguracija za sinastrijski modul.

Sve školski sporne ili proizvoljno definirane vrijednosti (orbisi,
tretman Rahu/Ketu, itd.) su OVDJE, s jasno navedenom zadanom postavkom i
obrazloženjem - ne raspršene ili "skrivene" po pojedinim datotekama.
Korisničko sučelje (ui/pages_synastry.py, tab "Postavke") čita i mijenja
ove vrijednosti; izvještaj (core/synastry/report.py) uvijek navodi koje
su postavke bile aktivne za dani izračun.
"""

from dataclasses import dataclass, field
from typing import Dict

# ---------------------------------------------------------------------------
# Rahu/Ketu Graha Drishti IZMEĐU dviju karata (core/synastry/graha_drishti.py)
#
# core/aspects.py (natalna karta, nedirano) podržava samo binarni izbor
# (uključi/isključi "kao Saturn"). Sinastrija nudi 3 opcije jer je pitanje
# aspekata čvorova posebno sporno kad se primjenjuje unakrsno, na TUĐU
# kartu (ne samo unutar iste karte):
#
#   "seventh_only" - čvorovi bacaju SAMO 7. aspekt (kao svih 7 klasičnih
#       grahe - to je univerzalni, nesporni Drishti). Konzervativna opcija,
#       najbliža izvornom BPHS-u koji Rahu/Ketu uopće ne spominje u
#       poglavlju o Drishtiju.
#   "5_7_9" - čvorovi bacaju 5./7./9., analogno Jupiteru. Rjeđa, novija
#       konvencija (neki suvremeni izvori tretiraju čvorove kao "duhovne"
#       aspektatore analogne Jupiteru, posebno u sinastriji).
#   "none" - čvorovi ne bacaju nikakav Graha Drishti (samo se promatraju
#       kroz konjunkcije i kućni overlay).
# ---------------------------------------------------------------------------
NODE_ASPECT_MODES = ("seventh_only", "5_7_9", "none")
DEFAULT_NODE_ASPECT_MODE = "seventh_only"

# ---------------------------------------------------------------------------
# Orbisi za međukartne (sinastrijske) konjunkcije, u stupnjevima.
# "_sensitive" pokriva posebne točke bez vlastite "prirodne" veličine tijela
# (AL/UL/A7/BP/Lagna).
# ---------------------------------------------------------------------------
DEFAULT_CONJUNCTION_ORBS: Dict[str, float] = {
    "Sunce": 8.0, "Mjesec": 8.0,
    "Mars": 6.0, "Merkur": 6.0, "Venera": 6.0,
    "Jupiter": 5.0, "Saturn": 5.0,
    "Rahu": 4.0, "Ketu": 4.0,
    "_sensitive": 3.0,
}

EXACT_CONJUNCTION_ORB = 1.0  # unutar 1° = "egzaktna" konjunkcija

# ---------------------------------------------------------------------------
# Chara Karaka shema (core/chara_karaka.py) - vidi tu datoteku za puno
# obrazloženje. "7_karaka" (zadano) je izvorna, najraširenija shema (7
# klasičnih grahe, bez čvorova). "8_karaka" dodaje Rahu.
# ---------------------------------------------------------------------------
CHARA_KARAKA_SCHEMES = ("7_karaka", "8_karaka")
DEFAULT_CHARA_KARAKA_SCHEME = "7_karaka"

# ---------------------------------------------------------------------------
# Kuja Dosha (core/synastry/kuja_dosha.py) - kuće u kojima Mars klasično
# uzrokuje Kuja (Mangal) Doshu, gledano od Lagne/Mjeseca/Venere. Škole se
# RAZLIKUJU: neke koriste 6 kuća (1,2,4,7,8,12), neke tradicionalnije samo
# 4 (2,4,7,8), a neke isključuju 1. i 2. kad se gleda od Lagne. Zadano:
# najšira, najčešće citirana verzija (6 kuća) - korisnik može suziti.
# ---------------------------------------------------------------------------
DEFAULT_KUJA_DOSHA_HOUSES = frozenset({1, 2, 4, 7, 8, 12})

# ---------------------------------------------------------------------------
# Prediktivna sinastrija (core/synastry/transit_activations.py, predictive.py)
# - kuće koje se prate za aktivaciju tranzitom i za dvostruki tranzit
#   Jupitera/Saturna (spec 3.3: "1,5,7,8,9,11")
# - relativna težina tranzita po brzini planeta (spori tranziti ne smiju
#   imati istu težinu kao brzi - spec 3.1). Mjesec je namjerno najniže
#   ponderiran ("kratkotrajni okidač, ne samostalan dokaz" - spec 3.6).
# ---------------------------------------------------------------------------
PREDICTIVE_ACTIVATION_HOUSES = frozenset({1, 5, 7, 8, 9, 11})
TRANSIT_SPEED_WEIGHT = {
    "Saturn": 1.0, "Jupiter": 1.0, "Rahu": 1.0, "Ketu": 1.0,
    "Mars": 0.6,
    "Sunce": 0.35, "Merkur": 0.35, "Venera": 0.35,
    "Mjesec": 0.15,
}
SLOW_TRANSIT_PLANETS = frozenset({"Saturn", "Jupiter", "Rahu", "Ketu"})


@dataclass
class SynastryConfig:
    node_aspect_mode: str = DEFAULT_NODE_ASPECT_MODE
    conjunction_orbs: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_CONJUNCTION_ORBS))
    use_bhava_chalit: bool = True
    # Rezervirano za kasniji, IZRIČITO opcionalni sloj stupanjskih
    # zapadnjačkih aspekata (sekstil/kvadrat/trigon/opozicija) uz klasični
    # Graha Drishti - NIJE implementirano u Fazi 1, vidi core/synastry/README
    # napomenu u __init__.py. Zadano isključeno.
    include_western_aspects: bool = False
    chara_karaka_scheme: str = DEFAULT_CHARA_KARAKA_SCHEME
    kuja_dosha_houses: frozenset = field(default_factory=lambda: set(DEFAULT_KUJA_DOSHA_HOUSES))

    def orb_for(self, planet_or_point: str) -> float:
        return self.conjunction_orbs.get(planet_or_point, self.conjunction_orbs["_sensitive"])

    def settings_summary(self) -> Dict[str, str]:
        """Kratak, čitljiv sažetak aktivnih postavki - za izvještaj (transparentnost)."""
        node_label = {
            "seventh_only": "samo 7. aspekt (puna snaga)",
            "5_7_9": "5./7./9. aspekt (analogno Jupiteru)",
            "none": "bez aspekata",
        }[self.node_aspect_mode]
        return {
            "Rahu/Ketu Graha Drishti": node_label,
            "Bhava Chalit prikaz": "uključen" if self.use_bhava_chalit else "isključen",
            "Zapadnjački aspekti (dodatni sloj)": "uključeni" if self.include_western_aspects else "isključeni (nije implementirano u ovoj fazi)",
            "Orb Sunce/Mjesec": f"{self.orb_for('Sunce'):.1f}°",
            "Orb ostali osobni planeti": f"{self.orb_for('Mars'):.1f}°",
            "Orb Jupiter/Saturn": f"{self.orb_for('Jupiter'):.1f}°",
            "Orb Rahu/Ketu": f"{self.orb_for('Rahu'):.1f}°",
            "Orb osjetljivih točaka": f"{self.orb_for('_sensitive'):.1f}°",
            "Chara Karaka shema": self.chara_karaka_scheme,
            "Kuja Dosha kuće": ", ".join(str(h) for h in sorted(self.kuja_dosha_houses)),
        }


DEFAULT_CONFIG = SynastryConfig()
