"""
Konfiguracija težina za kategorijsko bodovanje (poglavlje 4 specifikacije).

Sve težine su OVDJE (ne raspršene kroz scoring.py) - korisnik ih kasnije
može urediti. Nijedna vrijednost ovdje nije "znanstveno izmjerena" - riječ
je o RAZUMNIM, DOKUMENTIRANIM početnim vrijednostima namijenjenima
transparentnoj usporedbi, ne o preciznoj psihometriji.

NAPOMENA O OPSEGU: popis signala po kategoriji NIJE iscrpan (to bi
zahtijevalo modeliranje stotina mogućih kombinacija planeta/kuća/aspekata
i bilo bi lažno precizno) - ovo je razuman, reprezentativan izbor
najznačajnijih klasičnih pokazatelja po kategoriji, jasno dokumentiran
ovdje da bude lako proširiv.

ISPRAVAK (rekalibracija bodovanja - bivši rezultati poput 97-99/100 za
gotovo svaku kategoriju): sama tanh zasićujuća krivulja (SATURATION_SCALE)
nije bila dovoljna kad karta ima puno kontakata. Dodano niže:
  - DRISHTI_WEIGHT: puni aspekt (7. kuća/posebni puni aspekti) nosi punu
    težinu, ali DJELOMIČNI aspekti (3./10., 5./9., 4./8. kad NISU posebni
    puni aspekt planeta) nose MNOGO manju težinu nego prije (gdje se
    linearno koristilo 0.75/0.5/0.25 - preblago gušenje).
  - MAX_PAIR_CONTRIBUTION_PER_CATEGORY / MAX_PARTIAL_DRISHTI_SHARE /
    SECONDARY_CATEGORY_FRACTION: sprječavaju da jedan par ili djelomični
    aspekti sami zasite jednu ili više kategorija.
  - DIMINISHING_RETURN_FACTOR: svaki sljedeći (slabiji) doprinos u istoj
    kategoriji broji se s progresivno manjom težinom (umjesto ravnog
    zbroja prije tanh koraka).
  - SCORE_GATE_*: rezultat >80/>90 zahtijeva minimalan broj NEOVISNIH
    slojeva (core.synastry.models.ScoringFactor.layer) - vidi
    core/synastry/scoring.py:_finalize_category.

ISPRAVAK 2 (rezultati zbijeni u uskom pojasu 50-77 bez obzira na par -
empirijski potvrđeno na svih 78 mogućih parova iz lokalne baze, stdev ~5):
uzrok NIJE bio oblik tanh/diminishing-returns krivulje (retuniranje samo
POMIČE zbijenu hrpu gore-dolje po skali, ne širi je) nego to što je 7 od 9
kategorija (sve osim "Konflikt i pritisak" i djelomično "Bračni potencijal"
preko Kuja Doshe) strukturno moglo SAMO zbrajati pozitivan doprinos -
nijedan signal nije mogao kategoriju gurnuti ISPOD BASE_SCORE=50, pa je
`score = 50 + 50*tanh(nenegativno)` bio matematički zaključan na [50,100)
bez obzira koliko su karte stvarno neskladne. Dodano niže:
  - NATURAL_MALEFICS / MALEFIC_AFFLICTION_FACTOR: kad malefik (Mars/Saturn/
    Rahu/Ketu) aspektira ili je u konjunkciji s "mekim" značiteljem
    (Mjesec/Merkur/Venera/Jupiter), ta ista kategorija (Emocionalna
    povezanost/Komunikacija/Privlačnost/Podrška) dobiva DODATAN, NEOVISAN
    izazovan (negativan) doprinos - simetrično s already postojećim
    OVERLAY_CHALLENGING_* mehanizmom za overlay. Izuzetak: par već posebno
    tretiran u DRISHTI_CATEGORY_WEIGHTS/CONJUNCTION-analognoj logici za tu
    kategoriju (npr. Venera-Mars za "Privlačnost i kemija") se NE
    dodatno kažnjava - taj par je klasično SAM svoj signal, ne "aflikcija".
  - KUTA_NEUTRAL_FRACTION: Ashtakoota kuta doprinos je sada CENTRIRAN oko
    ove frakcije (0.5) umjesto oko 0 - kuta na 0% aktivno ODUZIMA puni
    max_contribution (klasičan dosha signal), na 50% je neutralna (0), tek
    iznad 50% dodaje pozitivno. Prije je i 0%-kuta doprinosila "0" (nikad
    negativno), što je bio dio istog strukturnog problema.
"""

NATURAL_MALEFICS = {"Mars", "Saturn", "Rahu", "Ketu"}
# Koliki dio POZITIVNE težine "mekog" značitelja (Mjesec/Merkur/Venera/
# Jupiter) malefik oduzima kad ga aspektira/konjungira - EMPIRIJSKI
# kalibrirano (core/synastry/scoring.py rekalibracija, kolovoz 2026) na
# svih 78 mogućih parova iz lokalne baze: 1.3 daje realan raspon rezultata
# (~18-82, stdev ~15 umjesto prijašnjih ~50-77, stdev ~5) bez ponovnog
# uvođenja stare greške (gotovo sve kategorije uvijek >90).
MALEFIC_AFFLICTION_FACTOR = 1.3

# Frakcija Ashtakoota kute (points/max_points) koja se smatra "neutralnom"
# (doprinos 0) - ispod nje kuta oduzima, iznad dodaje. 0.5 = pola bodova.
KUTA_NEUTRAL_FRACTION = 0.5

CATEGORY_NAMES = [
    "Emocionalna povezanost",
    "Privlačnost i kemija",
    "Komunikacija",
    "Stabilnost",
    "Podrška i prijateljstvo",
    "Bračni potencijal",
    "Konflikt i pritisak",
    "Karmička/intenzivna povezanost",
    "Praktična kompatibilnost",
]

# Faza 4 (tranziti/dashe/Varshaphala) - kategorija postoji u specifikaciji,
# ali nema podataka dok prediktivna sinastrija ne bude implementirana.
NOT_YET_AVAILABLE_CATEGORIES = ["Trenutačna prediktivna aktivacija"]

BASE_SCORE = 50.0  # neutralna polazna točka (0-100 skala) prije primjene signala

# Skala zasićenja (core.synastry.scoring._finalize_category): sirovo
# odstupanje od BASE_SCORE se propušta kroz tanh (50*tanh(sirovo/SATURATION_SCALE))
# umjesto TVRDOG rezanja na 0/100 - vidi i DIMINISHING_RETURN_FACTOR niže
# (primjenjuje se PRIJE tanh koraka, kao dodatna, ne zamjenska, kočnica).
# ISPRAVAK 2 (empirijska rekalibracija, vidi napomenu iznad): stara
# vrijednost 90 je gotovo NIKAD nije bila stvarno dosegnuta jer je
# diminishing-returns asimptota (MAX_PAIR_CONTRIBUTION_PER_CATEGORY /
# (1-DIMINISHING_RETURN_FACTOR)) bila puno manja od nje - tanh je time
# koristio samo malen dio svog raspona i sve je ispadalo blizu BASE_SCORE.
# 75 (uz DIMINISHING_RETURN_FACTOR=0.74 niže) daje realan raspon na svih
# 78 mogućih parova iz lokalne baze bez ponovnog uvođenja stare "gotovo
# sve >90" greške.
SATURATION_SCALE = 75.0

# --- Diminishing returns (spec 10.4): svaki sljedeći (po jačini sortiran)
# doprinos u kategoriji broji se s množiteljem koji progresivno opada -
# sprječava da desetci SLABIH nalaza naivno zbrojeni gurnu kategoriju u
# zasićenje jednako "lako" kao par jakih nalaza.
DIMINISHING_RETURN_FACTOR = 0.74

# --- Gornje ograde po jednom paru/nalazu (spec 10.5/10.11) ---
MAX_PAIR_CONTRIBUTION_PER_CATEGORY = 15.0

# --- Maksimalni udio koji SAMO djelomični (three_quarter/half/quarter)
# Graha Drishti aspekti smiju činiti u ukupnom apsolutnom doprinosu
# kategorije (spec 5/10.6) - preostatak se razmjerno smanjuje ako je
# premašeno.
MAX_PARTIAL_DRISHTI_SHARE = 0.20

# --- Jedan planetarni par smije PUNOM težinom doprinijeti u najviše ovoliko
# kategorija (spec 10.1/10.2/11) - u ostalim kategorijama u kojima bi
# teoretski isti par nešto značio, doprinos se svede na SECONDARY_CATEGORY_FRACTION.
MAX_CATEGORIES_PER_PAIR = 2
SECONDARY_CATEGORY_FRACTION = 0.15

# --- Pragovi za "koliko neovisnih slojeva treba za visok rezultat" (spec 10.7/10.8) ---
SCORE_GATE_80_MIN_LAYERS = 3
SCORE_GATE_90_MIN_LAYERS = 4

# --- Konflikt/Bračni potencijal međuovisnost (spec 10.9) ---
HIGH_CONFLICT_THRESHOLD = 75.0
MARRIAGE_HIGH_CEILING_WITHOUT_STABILIZERS = 90.0

# --- Graha Drishti (D1) ---
# DRISHTI_WEIGHT: koliko od "pune" kategorijske težine (DRISHTI_CATEGORY_WEIGHTS/
# DRISHTI_SINGLE_PLANET_WEIGHTS niže) nosi aspekt OVISNO o njegovoj vrsti -
# zamjenjuje bivše linearno c.strength (1.0/0.75/0.5/0.25) množenje, koje je
# djelomičnim aspektima davalo previsoku (3/4 do 1/4) težinu.
DRISHTI_WEIGHT = {
    "full": 1.00,
    "three_quarter": 0.30,
    "half": 0.18,
    "quarter": 0.08,
}
_STRENGTH_TO_TIER = {1.0: "full", 0.75: "three_quarter", 0.5: "half", 0.25: "quarter"}
# Planetov VLASTITI puni aspekt (Mars 4./8., Jupiter 5./9., Saturn 3./10.)
# dobiva dodatni multiplikator iznad "full" - klasično se smatra jednako
# snažnim kao 7. aspekt, ali specifikacija traži da bude BLAGO istaknutiji
# od običnog punog 7. aspekta drugih planeta.
SPECIAL_FULL_MULTIPLIER = 1.15

# Ključ: frozenset({planet_a, planet_b}) ili pojedinačni planet (znači "kad god je uključen")
DRISHTI_CATEGORY_WEIGHTS = {
    frozenset({"Venera", "Mars"}): {"Privlačnost i kemija": 22.0},
    frozenset({"Mjesec", "Mjesec"}): {"Emocionalna povezanost": 20.0},
    frozenset({"Merkur", "Merkur"}): {"Komunikacija": 18.0},
    frozenset({"Jupiter", "Jupiter"}): {"Podrška i prijateljstvo": 18.0},
}
# Signali "kad god je UKLJUČEN planet X" (bilo koji par u kojem sudjeluje)
DRISHTI_SINGLE_PLANET_WEIGHTS = {
    "Mjesec": {"Emocionalna povezanost": 8.0},
    "Merkur": {"Komunikacija": 8.0},
    "Saturn": {"Stabilnost": 6.0, "Konflikt i pritisak": 6.0},
    "Jupiter": {"Podrška i prijateljstvo": 8.0},
    "Venera": {"Privlačnost i kemija": 6.0},
    "Mars": {"Privlačnost i kemija": 5.0, "Konflikt i pritisak": 6.0},
    "Rahu": {"Karmička/intenzivna povezanost": 12.0},
    "Ketu": {"Karmička/intenzivna povezanost": 12.0},
}
# Dodatni bonus kad je udaljenost aspekta baš 7. kuća (izravno partnerstvo) -
# OPIS namjerno kaže "puni opozicijski Graha Drishti", ne "natalna 7. kuća"
# (spec 6) - vidi core/synastry/interpretation.py za točnu terminologiju.
SEVENTH_HOUSE_ASPECT_BONUS = {"Bračni potencijal": 10.0}

# --- Konjunkcije (D1) ---
CONJUNCTION_SINGLE_PLANET_WEIGHTS = {
    "Mjesec": {"Emocionalna povezanost": 12.0},
    "Venera": {"Privlačnost i kemija": 10.0},
    "Mars": {"Privlačnost i kemija": 8.0, "Konflikt i pritisak": 8.0},
    "Merkur": {"Komunikacija": 10.0},
    "Jupiter": {"Podrška i prijateljstvo": 10.0},
    "Saturn": {"Stabilnost": 8.0, "Konflikt i pritisak": 8.0},
    "Rahu": {"Karmička/intenzivna povezanost": 15.0},
    "Ketu": {"Karmička/intenzivna povezanost": 15.0},
}
EXACT_CONJUNCTION_MULTIPLIER = 1.3  # egzaktna (≤1°) konjunkcija dobiva 30% veći doprinos

# --- Kućni overlay (D1) - planet u SPECIFIČNOJ kući druge osobe ---
OVERLAY_HOUSE_WEIGHTS = {
    4: {"Emocionalna povezanost": 10.0, "Stabilnost": 5.0},
    5: {"Privlačnost i kemija": 8.0},
    7: {"Bračni potencijal": 12.0},
    8: {"Karmička/intenzivna povezanost": 10.0},
    9: {"Podrška i prijateljstvo": 6.0},
    10: {"Praktična kompatibilnost": 8.0},
    11: {"Praktična kompatibilnost": 6.0, "Podrška i prijateljstvo": 5.0},
    2: {"Praktična kompatibilnost": 6.0},
}
OVERLAY_PLANET_MULTIPLIER = {
    "Venera": 1.2, "Mars": 1.1, "Mjesec": 1.2, "Jupiter": 1.1,
    "Saturn": 1.0, "Rahu": 1.1, "Ketu": 1.1,
}
# ISPRAVAK (spec 8): overlay se ranije UVIJEK bodovao kao "positive", čak i
# za Mars/Saturn/Rahu/Ketu u 8./12. kući. Ovi planeti u ovim kućama sada
# doprinose i "Konflikt i pritisak" umjesto isključivo pozitivnih kategorija.
OVERLAY_CHALLENGING_PLANETS = {"Mars", "Saturn", "Rahu", "Ketu"}
OVERLAY_CHALLENGING_HOUSES = {8, 12}
OVERLAY_CHALLENGING_WEIGHT = {"Konflikt i pritisak": 6.0}

# --- Ashtakoota kute -> kategorije (razmjerno prema udjelu bodova/maksimuma) ---
KUTA_CATEGORY_WEIGHTS = {
    "Graha Maitri": {"category": "Podrška i prijateljstvo", "max_contribution": 15.0},
    "Nadi": {"category": "Stabilnost", "max_contribution": 12.0},
    "Bhakoot (Rashi)": {"category": "Stabilnost", "max_contribution": 8.0},
    "Yoni": {"category": "Privlačnost i kemija", "max_contribution": 10.0},
    "Varna": {"category": "Praktična kompatibilnost", "max_contribution": 4.0},
    "Vashya": {"category": "Praktična kompatibilnost", "max_contribution": 6.0},
    "Gana": {"category": "Emocionalna povezanost", "max_contribution": 8.0},
}

# --- Kuja Dosha -> Konflikt i pritisak (po ozbiljnosti), i Bračni potencijal
# (samo ako NIJE uravnoteženo - vidi core.synastry.kuja_dosha.balancing_fraction) ---
KUJA_DOSHA_CONFLICT_WEIGHT = 15.0        # * (severity_score/100), po osobi, max se uzima (ne zbraja)
KUJA_DOSHA_MARRIAGE_PENALTY = 10.0        # * (1 - balancing_fraction) - DJELOMIČNA, ne sve-ili-ništa kazna

# --- Nakšatra: samo POTVRĐENE kategorije (2/3/4 iz core/synastry/
# nakshatra_matching.py) nose bod - kategorija 5 (dispositor_symbolic) je
# NAMJERNO izostavljena iz scoring.py (spec 3: "peta kategorija ne smije
# dobivati bodove"). ---
NAKSHATRA_REPEATED_THEME_WEIGHT = 3.0
NAKSHATRA_SAME_LORD_WEIGHT = 3.0
NAKSHATRA_MUTUAL_DISPOSITOR_WEIGHT = 5.0
NAKSHATRA_DISPOSITOR_CONFIRMED_WEIGHT = 4.0

# --- D1<->D9 ponovljeni obrasci -> karmička povezanost ---
# ISPRAVAK (spec 9): ovo VIŠE NE ulazi kao neovisan bod - vidi
# core/synastry/divisional_synastry.py (D1_D9_REPEAT_MIN_SCORE prag) i
# core/synastry/scoring.py (bonus se primjenjuje na POSTOJEĆI D1 par,
# ograničen na D1_D9_REPEAT_BONUS_CAP udjela tog para, ne novi bucket).
D1_D9_REPEAT_MIN_SCORE = 0.55
D1_D9_REPEAT_BONUS_CAP = 0.20
