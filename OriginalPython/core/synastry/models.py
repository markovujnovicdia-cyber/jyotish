"""
Strukturirani modeli za sinastrijski modul. Namjerno se NE koristi jedan
"veliki" model za sve (kontakti, overlay, konjunkcije su različite stvari
s različitim poljima) - svaki dio (core/synastry/overlays.py, graha_drishti.py,
conjunctions.py) gradi svoju listu, a report.py/scoring.py (kasnija faza)
ih spajaju.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from core.natal import NatalContext


@dataclass
class SynastryPerson:
    """Omotač oko core.natal.NatalContext s podacima potrebnim za sinastriju."""
    person_id: Optional[int]
    name: str
    context: NatalContext
    birth_time_accuracy: Optional[str] = None  # napomena o pouzdanosti vremena rođenja (iz Person.time_confirmed)


@dataclass
class HouseOverlayRow:
    source_person: str   # "A" ili "B" - čiji planet PADA u tuđu kartu
    target_person: str   # "A" ili "B" - u čiju kartu pada
    planet: str
    sign: str
    whole_sign_house: int
    bhava_chalit_house: Optional[int]   # None ako je isto kao whole_sign_house
    nakshatra: str
    pada: int
    sign_lord: str        # dispozitor (vladar znaka)
    nakshatra_lord: str    # vladar nakshatre (za Vimshottari dashu)
    dignity: str           # core.planet_strength.compute_dignity
    is_significant_house: bool   # kuća 1,2,4,5,7,8,9,10,11,12
    target_house_lord: str
    target_house_lord_relation: str  # kratki opis odnosa planeta s vladarom kuće u koju pada
    label: str              # kratka oznaka za tablicu, npr. "Venera (A) -> 7. kuća (B)"


@dataclass
class GrahaDrishtiContact:
    source_person: str
    target_person: str
    from_planet: str
    to_planet: str          # naziv planeta ili "Lagna"/"UL"/"A7" itd.
    house_distance: int      # 1-12, kuća mete gledano OD from_planet
    strength: float
    strength_label: str
    from_planet_houses_own_chart: List[int]   # koje kuće from_planet vlada u SVOJOJ (izvornoj) karti
    to_planet_houses_own_chart: List[int]      # koje kuće to_planet vlada u SVOJOJ karti (ako je planet)
    short_interpretation: str = ""
    detailed_interpretation: str = ""


@dataclass
class ConjunctionContact:
    person_a_object: str
    person_b_object: str
    longitude_a: float
    longitude_b: float
    sign: str
    degree_distance: float
    orb_used: float
    is_exact: bool
    same_nakshatra: bool
    same_pada: bool
    special_flags: List[str] = field(default_factory=list)
    short_interpretation: str = ""
    detailed_interpretation: str = ""


@dataclass
class SynastryContactTable:
    person_a_name: str
    person_b_name: str
    house_overlay_a_to_b: List[HouseOverlayRow]
    house_overlay_b_to_a: List[HouseOverlayRow]
    mutual_emphasis_notes: List[str]
    graha_drishti: List[GrahaDrishtiContact]
    conjunctions: List[ConjunctionContact]


# ---------------------------------------------------------------------------
# Faza 2: nakšatra sinastrija, Ashtakoota, Kuja Dosha, ključni signifikatori
# ---------------------------------------------------------------------------

@dataclass
class NakshatraProfile:
    person_label: str        # "A" ili "B"
    point_label: str          # "Mjesec", "Ascendent", "Venera", "Mars", "Sunce", "Vladar 7.", "Darakaraka"
    planet_or_point: str      # stvarni planet (npr. "Mars") koji zauzima tu ulogu
    longitude: float
    nakshatra: str
    pada: int
    nakshatra_lord: str
    devata: str
    gana: str
    yoni: str
    yoni_gender: str
    nadi: str
    navamsha_sign: str        # D9 znak TE TOČNE pade
    pada_element: str          # element (Vatra/Zemlja/Zrak/Voda) tog D9 znaka


@dataclass
class NakshatraCrossLink:
    # "same_nakshatra" | "same_pada" | "same_nakshatra_lord" | "mutual_dispositor" |
    # "dispositor_confirmed" | "dispositor_symbolic" (potonje = kategorija 5,
    # slaba simbolička napomena BEZ bodovanja - vidi core/synastry/nakshatra_matching.py)
    relation_type: str
    source_label: str          # npr. "Mjesec (A)"
    target_label: str          # npr. "Venera (B)"
    detail: str
    scored: bool = True         # False SAMO za "dispositor_symbolic" (kategorija 5)


@dataclass
class NakshatraRepeatedTheme:
    nakshatra: str
    points_involved: List[str]
    note: str


@dataclass
class NakshatraSynastryResult:
    profiles_a: Dict[str, NakshatraProfile]
    profiles_b: Dict[str, NakshatraProfile]
    cross_links: List[NakshatraCrossLink]
    repeated_themes: List[NakshatraRepeatedTheme]
    lord_graph_edges: List[Tuple[str, str, str]]   # (from_label, to_label, relation)


@dataclass
class KutaScore:
    name: str
    points: float
    max_points: float
    rule_used: str
    table_reference: str
    interpretation: str
    limitation: str


@dataclass
class AshtakootaResult:
    person_a_moon_nakshatra: str
    person_b_moon_nakshatra: str
    kutas: List[KutaScore]
    total_points: float
    max_points: float
    cancellations: List[str]


@dataclass
class KujaDoshaAssessment:
    person_label: str
    houses_involved: Dict[str, int]     # "Ascendent"/"Mjesec"/"Venera" -> kuća Marsa
    afflicted_from: List[str]            # koje osnove (Asc/Mjesec/Venera) pokazuju dosha kuću
    severity: str                        # "nema" | "blaga" | "umjerena" | "jaka"
    severity_score: float                # 0-100 (orijentacijski, ne "postotak doshe")
    reasons: List[str]
    possible_cancellations: List[str]


@dataclass
class KujaDoshaComparison:
    person_a: KujaDoshaAssessment
    person_b: KujaDoshaAssessment
    mutual_balancing: bool
    balancing_note: str
    balancing_fraction: float = 0.0   # 0 (nema uravnoteženja) - 1 (jednak intenzitet kod oboje)
                                        # = min(severity)/max(severity); vidi core/synastry/kuja_dosha.py


@dataclass
class SignificatorComparison:
    label: str
    person_a_detail: str
    person_b_detail: str
    cross_notes: List[str]


@dataclass
class SynastryPoint:
    """
    Jedna imenovana, osoba-svjesna "točka" u karti (planet ili izvedena
    uloga poput Darakarake) - koristi se za GENERIČKO građenje unakrsnih
    parova u core/synastry/relationship_significators.py, tako da provjera
    "person_id se NE smije poklopiti na obje strane para" postane trivijalna
    i testabilna (vidi tests/test_relationship_significators.py).
    """
    person_id: str          # "A" ili "B"
    role: str                 # "darakaraka", "atmakaraka", "7th_lord", "UL_lord", "A7_lord", ...
    planet: str
    longitude: float
    sign: str
    house: int


@dataclass
class PersonSignificatorProfile:
    person_label: str
    seventh_house_sign: str
    seventh_house_planets: List[str]
    seventh_lord: str
    seventh_lord_house: int
    seventh_lord_sign: str
    venus_house: int
    venus_sign: str
    mars_house: int
    mars_sign: str
    jupiter_house: int
    jupiter_sign: str
    moon_house: int
    moon_sign: str
    atmakaraka_planet: str
    darakaraka_planet: str
    arudha_lagna_sign: str
    upapada_lagna_sign: str
    upapada_house: int
    upapada_lord: str
    upapada_planets: List[str]
    second_from_upapada_sign: str
    eighth_from_upapada_sign: str
    darapada_sign: str
    darapada_house: int


@dataclass
class RelationshipSignificatorsResult:
    profile_a: PersonSignificatorProfile
    profile_b: PersonSignificatorProfile
    cross_notes: List[str]


# ---------------------------------------------------------------------------
# Faza 3: generička divizijska (varga) sinastrija - potpuno implementirano
# za D9 (Navamsha); ista struktura vrijedi za D7/D10/D12 (proslijedi drugu
# varga_func).
# ---------------------------------------------------------------------------

@dataclass
class VargaHouseOverlayRow:
    source_person: str
    target_person: str
    planet: str
    varga_sign: str
    house: int
    is_significant_house: bool
    label: str


@dataclass
class VargaSameSignContact:
    person_a_object: str
    person_b_object: str
    varga_sign: str


@dataclass
class VargaSynastryResult:
    varga_code: str
    varga_name: str
    ascendant_sign_a: str
    ascendant_sign_b: str
    seventh_sign_a: str
    seventh_sign_b: str
    seventh_lord_a: str
    seventh_lord_b: str
    key_points_a: Dict[str, str]
    key_points_b: Dict[str, str]
    overlay_a_to_b: List[VargaHouseOverlayRow]
    overlay_b_to_a: List[VargaHouseOverlayRow]
    drishti_a_to_b: List[GrahaDrishtiContact]
    drishti_b_to_a: List[GrahaDrishtiContact]
    same_sign_contacts: List[VargaSameSignContact]
    repeated_pattern_notes: List[str]
    # Person-svjesni contact_key (core.synastry.deduplication.contact_key) za
    # svaku stavku u repeated_pattern_notes, ISTIM redoslijedom - koristi ih
    # core/synastry/scoring.py da D1/D9 potvrdu primijeni kao OGRANIČEN bonus
    # na POSTOJEĆI D1 par, ne kao nov, neovisan bod (spec 9).
    repeated_pattern_pair_keys: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Faza 3: kategorijsko bodovanje (transparentno, konfigurabilno, bez
# dvostrukog brojanja iste veze - vidi core/synastry/scoring.py)
# ---------------------------------------------------------------------------

@dataclass
class ScoringFactor:
    description: str
    pair_key: str
    weight: float
    contribution: float
    polarity: str   # "positive" | "challenging" | "neutral"
    layer: str = "drishti"   # "drishti" | "conjunction" | "overlay" | "ashtakoota" | "kuja" |
                                # "nakshatra" | "d9" | "significator" - koristi se za brojanje
                                # NEOVISNIH slojeva prije dopuštanja visokog rezultata (spec 10)
    is_partial_drishti: bool = False   # True za three_quarter/half/quarter Graha Drishti (spec 5/10.6)


@dataclass
class CategoryScore:
    category: str
    score: float
    factors: List[ScoringFactor]
    excluded_duplicates: List[str]
    method: str
    positive_score: float = 0.0     # zbroj samo "positive" doprinosa (0-100, informativno)
    challenge_score: float = 0.0    # zbroj samo "challenging" doprinosa (0-100, informativno)
    net_score: float = 0.0          # = score (zadržano radi jasnoće u izvještaju/JSON-u)
    confidence: str = "niska"       # "niska" | "srednja" | "visoka" - iz broja neovisnih slojeva
    independent_layers: int = 0
    confirmations: int = 0
    contradictions_count: int = 0
    top_positive_notes: List[str] = field(default_factory=list)
    top_challenge_notes: List[str] = field(default_factory=list)


@dataclass
class SynastryScoreResult:
    categories: Dict[str, CategoryScore]
    not_available: List[str]


# ---------------------------------------------------------------------------
# Faza 4: prediktivna sinastrija (tranzitna aktivacija natalne sinastrije,
# dvostruki tranzit Jupitera/Saturna, Vimshottari Dasha aktivacije, vremenska
# crta). Varshaphala/Mudda Dasha aktivacije, fina mjesečna/dnevna analiza,
# optimizacija/cache i izvoz su Faza 5.
# ---------------------------------------------------------------------------

@dataclass
class NatalSynastryLink:
    link_id: str
    link_type: str          # "graha_drishti" | "conjunction" | "nakshatra"
    person_a_object: str      # npr. "Venera (A)"
    person_b_object: str      # npr. "Mjesec (B)"
    anchor_longitude_a: float
    anchor_longitude_b: float
    description: str


@dataclass
class TransitActivation:
    transit_planet: str
    link: NatalSynastryLink
    activation_types: List[str]
    strength: float
    is_slow_planet: bool
    interpretation: str


@dataclass
class PersonTransitRow:
    planet: str
    sign: str
    longitude: float
    house_from_ascendant: int
    house_from_moon: int
    house_from_upapada: int
    nakshatra: str
    pada: int
    dispositor: str
    is_retrograde: bool
    is_slow: bool


@dataclass
class DoubleTransitResult:
    jupiter_hits_a: List[str]
    saturn_hits_a: List[str]
    jupiter_hits_b: List[str]
    saturn_hits_b: List[str]
    simultaneous_both_charts: bool
    note: str


@dataclass
class DashaProfile:
    person_label: str
    maha_lord: str
    antar_lord: str
    pratyantar_lord: str
    maha_start: str
    maha_end: str
    antar_start: str
    antar_end: str
    maha_houses_ruled: List[int]
    maha_lord_natal_sign: str
    maha_lord_natal_nakshatra: str
    maha_lord_d9_sign: str
    relation_to_seventh: str
    relation_to_venus: str
    relation_to_darakaraka: str
    relation_to_upapada: str


@dataclass
class DashaMutualActivationResult:
    profile_a: DashaProfile
    profile_b: DashaProfile
    mutual_notes: List[str]


@dataclass
class PredictiveSnapshot:
    date_label: str
    transits_a: Dict[str, PersonTransitRow]
    transits_b: Dict[str, PersonTransitRow]
    activations: List[TransitActivation]
    double_transit: DoubleTransitResult
    dasha_result: DashaMutualActivationResult


@dataclass
class TimelinePoint:
    date_label: str
    total_strength: float
    active_slow_transits: List[str]
    active_dasha_lords: List[str]
    themes: List[str]
    top_notes: List[str]
    # ISPRAVAK: (transit_planet, strength, teme_tog_planeta) po svakoj
    # aktivaciji tog dana - potrebno da UI filtar teme na Vremenskoj crti
    # stvarno preračuna jačinu SAMO za odabranu temu, ne uvijek ukupnu
    # dnevnu jačinu (vidi ui/pages_synastry.py:_render_timeline).
    activation_strengths: List[Tuple[str, float, List[str]]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Faza 5: Varshaphala/Mudda Dasha aktivacije u sinastriji, mjesečne/dnevne
# (Mjesečeve) aktivacije, izvoz.
# ---------------------------------------------------------------------------

@dataclass
class VarshaphalaProfile:
    person_label: str
    target_year: int
    ascendant_sign: str
    muntha_sign: str
    muntha_lord: str
    varsheshwara_planet: Optional[str]
    seventh_sign: str
    seventh_lord: str
    venus_house: int
    moon_house: int
    saturn_house: int
    jupiter_house: int
    active_mudda_dasha_lord: Optional[str]
    tajika_ithasala_count: int
    tajika_isarapha_count: int


@dataclass
class VarshaphalaSynastryResult:
    profile_a: VarshaphalaProfile
    profile_b: VarshaphalaProfile
    b_planets_on_a_sensitive_points: List[str]
    a_planets_on_b_sensitive_points: List[str]
    mudda_dasha_activates_natal_link: List[str]
    simultaneous_annual_activation: bool
    notes: List[str]


@dataclass
class MoonTriggerDay:
    date_label: str
    notes: List[str]
