"""Plain Croatian explanations of the traditional symbolism of natal yogas.
Editorial summaries; formation rules remain in core/yoga_engine.
Further reading: PVR Narasimha Rao, Vedic Astrology: An Integrated Approach,
chapter 11; the individual rule's source is displayed alongside its definition.
"""
MEANINGS = {
'ruchaka': 'Naglašava Marsove teme: inicijativu, hrabrost, natjecanje i sposobnost vođenja. Važno je kako osoba usmjerava tu energiju.',
'bhadra': 'Naglašava Merkur: razmišljanje, govor, računanje, pregovaranje i praktičnu snalažljivost.',
'hamsa': 'Naglašava Jupiter: učenje, savjetovanje, etiku, duhovne interese i poštovanje stečeno znanjem.',
'malavya': 'Naglašava Veneru: ljepotu, umjetnost, odnose, udobnost i osjećaj za kvalitetu.',
'sasa': 'Naglašava Saturn: disciplinu, organizaciju, izdržljivost i autoritet koji se gradi s vremenom.',
'sunapha': 'Tradicionalno se povezuje sa samostalnim stvaranjem sredstava i oslanjanjem na vlastite sposobnosti.',
'anapha': 'Tradicionalno naglašava osobni ugled, samokontrolu i mogućnost ugodnog života.',
'durudhara': 'Naglašava podršku Mjesecu s obje strane: upravljanje resursima i sposobnost održavanja životne stabilnosti.',
'kemadruma': 'Tradicionalno opisuje manjak potpore Mjesecu i potrebu za većim vlastitim naporom. Obavezno treba provjeriti uvjete poništenja.',
'adhi_yoga': 'Povezuje se s podrškom, odgovornošću i upravljačkim sposobnostima. Snaga uključenih planeta određuje razinu izražavanja.',
'gajakesari': 'Veza Mjeseca i Jupitera tradicionalno naglašava razumijevanje, ugled i sposobnost pružanja ili primanja podrške.',
'chandra_mangala': 'Spaja Mjesečevu osjetljivost s Marsovom inicijativom: poduzetnost i brzo djelovanje, uz moguću impulzivnost.',
'amala_from_moon': 'Naglašava dobar glas, etičnost i doprinos kroz rad ili javno djelovanje.',
'vesi': 'Opisuje način na koji se Sunčeva volja izražava kroz djelovanje i resurse. Značenje ovisi o planetu koji oblikuje yogu.',
'vosi': 'Opisuje pozadinsku potporu Sunčevoj volji: navike, pripremu i unutarnje oslonce. Tumači se kroz uključene planete.',
'ubhayachari': 'Povezuje potporu s obje strane Sunca s ravnotežom pripreme i djelovanja. Dobrotvori i zlotvori daju različit ton.',
'budha_aditya': 'Naglašava spoj volje i intelekta: komunikaciju, analizu i izražavanje vlastitih ideja. Blizinu Merkura Suncu treba posebno procijeniti.',
'raja_yoga_sweep': 'Veza vladara kendre i trikone tradicionalno opisuje mogućnosti napredovanja, odgovornosti i utjecaja.',
'dharma_karmadhipati_yoga': 'Spaja životni smjer i vrijednosti s radom i karijerom; može podržati smislen profesionalni razvoj.',
'yogakaraka': 'Jedan planet istodobno povezuje kendru i trikonu, pa ima posebno povoljnu funkcionalnu ulogu za ovu lagnu.',
'atmakaraka_raja_yoga': 'U Jaiminijevu pristupu povezuje teme Atmakarake s položajem i utjecajem. Tumači se prema prikazanoj varijanti pravila.',
'dhana_yoga_lords': 'Povezuje kuće sredstava, sposobnosti i dobitaka: potencijal za stvaranje i očuvanje materijalnih resursa.',
'dhana_yoga_benefic_placement': 'Dobrotvor u području sredstava ili dobitaka tradicionalno podržava prihode i korisne prilike.',
'neecha_bhanga': 'Uvjeti poništenja pada mogu ublažiti slabost planeta. Poništenje pada samo po sebi nije automatski snažna Raja yoga.',
'harsha_yoga': 'Viparita yoga povezana sa šestom kućom: mogućnost napretka kroz rješavanje prepreka, obveza i sukoba.',
'sarala_yoga': 'Viparita yoga povezana s osmom kućom: snalaženje u promjenama, složenim situacijama i krizama.',
'vimala_yoga': 'Viparita yoga povezana s dvanaestom kućom: samostalnost, razborito raspolaganje troškovima i odmak od nepotrebnih vezanosti.',
'parivartana_yoga': 'Dva vladara razmjenjuju znakove, pa njihove kuće djeluju povezano. Maha, Khala i Dainya razmjene imaju različito značenje.',
'lakshmi_yoga': 'Tradicionalno naglašava blagostanje i povoljne prilike uz snažan osobni temelj i potporu devete kuće.',
'saraswati_yoga': 'Povezuje se s učenjem, govorom, pisanjem, umjetnošću i prenošenjem znanja.',
'kalanidhi_yoga': 'Naglašava spoj znanja, umjetničkog izraza i vještina koje mogu donijeti priznanje.',
'vasumati_yoga': 'Tradicionalno opisuje materijalni rast koji se razvija kroz trud, iskustvo i postupno napredovanje.',
'lagnadhi_yoga': 'Naglašava potporu osobnom položaju i sposobnostima, s dobrotvornim utjecajem na važne životne odnose i okolnosti.',
'chamara_yoga': 'Povezuje se s ugledom, učenošću, govorničkim sposobnostima i priznanjem za osobne kvalitete.',
'daridra_yoga': 'Tradicionalno upozorava na slabije veze prihoda i obveza te potrebu za pažljivim upravljanjem sredstvima; nije presuda o siromaštvu.',
'shakata_dosha_moon_jupiter': 'Odnos Mjeseca i Jupitera tradicionalno se povezuje s promjenjivom potporom i oscilacijama životnih okolnosti.',
'rajju': 'Nabhasa obrazac pokretnih znakova: kretanje, putovanja i promjenjiv životni ritam.',
'musala': 'Nabhasa obrazac nepokretnih znakova: postojanost, ustrajnost i zadržavanje odabranog smjera.',
'nala': 'Nabhasa obrazac dvojnih znakova: prilagodljivost, raznolike vještine i više usporednih interesa.',
'mala_yoga': 'Dobrotvorni obrazac kendri tradicionalno se povezuje s potporom i ugodnijim životnim okolnostima.',
'sarpa_yoga': 'Obrazac kendri sa zlotvorima tradicionalno naglašava pritisak i zahtjevne okolnosti; procjenjuje se i ublažavajuća potpora.',
'vajra_yoga': 'Mješovit obrazac dobrotvora i zlotvora: tradicionalno naglašava hrabrost i neujednačenu raspodjelu lakoće i napora.',
'yava_yoga': 'Mješovit obrazac tradicionalno povezan s ustrajnošću, vrijednostima i povoljnijim razvojem kroz zrelost.',
'kamala_yoga': 'Naglašava djelovanje u ključnim životnim područjima i mogućnost javne vidljivosti ili odgovornosti.',
'gada_yoga': 'Naglašava koncentraciju životne aktivnosti u dvije povezane kendre. Tradicionalna simbolika uključuje znanje i sredstva.',
'sakata_yoga': 'Nabhasa obrazac prve i sedme kuće: snažna koncentracija na sebe i odnose, uz tradicionalno zahtjevniju simboliku. Razlikuje se od Mjesec–Jupiter Shakate.',
'vihaga_yoga': 'Nabhasa obrazac četvrte i desete kuće tradicionalno naglašava kretanje i promjenjivost između privatnog života i djelovanja.',
'sringataka_yoga': 'Koncentracija u trikonama naglašava osobne sposobnosti, stvaralaštvo i životni smjer.',
'hala_yoga': 'Naziv znači plug; tradicionalna simbolika naglašava rad i napor usmjeren na održavanje životnih uvjeta.',
'vapi_yoga': 'Naziv označuje spremnik vode; tradicionalno se povezuje s prikupljanjem i čuvanjem resursa.',
'yupa_yoga': 'Naziv označuje obredni stup; tradicionalno naglašava posvećenost, pravila i unutarnje vrijednosti.',
'sara_yoga': 'Naziv znači strijela; tradicionalna simbolika naglašava oštrinu djelovanja i zahtjevne ili disciplinirane uloge.',
'sakti_yoga': 'Naziv označuje moć ili oružje; tradicionalno opisuje borbu, pritisak i potrebu za usmjeravanjem snage.',
'danda_yoga': 'Naziv znači štap; tradicionalno naglašava obveze, ograničenja i zahtjevnije iskustvo odnosa s autoritetom.',
'nauka_yoga': 'Naziv znači brod; tradicionalna simbolika povezuje kretanje, sredstva i brojne želje.',
'kuta_yoga': 'Tradicionalno naglašava zatvorenije ili zaštićene okolnosti i zahtjevne uloge. Procjenjuje se kroz cjelinu karte.',
'chatra_yoga': 'Naziv znači kišobran; tradicionalno naglašava zaštitu, pomaganje i potporu drugim ljudima.',
'chapa_yoga': 'Naziv znači luk; tradicionalno opisuje kretanje i napetost u usmjeravanju ciljeva.',
'ardhachandra_yoga': 'Naziv znači polumjesec; tradicionalno se povezuje s organizacijom, vodstvom i snažnim djelovanjem.',
'chakra_yoga': 'Naziv znači kotač; tradicionalno označuje široko područje djelovanja, autoritet i utjecaj.',
'samudra_yoga': 'Naziv znači ocean; tradicionalno naglašava obilje, akumulaciju resursa i stabilnost.',
'gola_yoga': 'Sedam planeta u jednom znaku: izrazita koncentracija životnih tema u jednom području.',
'yuga_yoga': 'Sedam planeta u dva znaka: polarizacija interesa između dva područja života.',
'sula_yoga': 'Sedam planeta u tri znaka: koncentriran i intenzivan obrazac s manjom raspršenošću interesa.',
'kedara_yoga': 'Sedam planeta u četiri znaka: simbolika obrade i izgradnje, s naglaskom na praktičan rad.',
'pasha_yoga': 'Sedam planeta u pet znakova: simbolika vezivanja, obveza i međusobno povezanih interesa.',
'dama_yoga': 'Sedam planeta u šest znakova: širi raspon aktivnosti i mogućnosti povezivanja resursa.',
'vina_yoga': 'Sedam planeta u sedam znakova: raznolikost sposobnosti i simbolika sklada ili umjetničkog izraza.',
}

def meaning_for(yoga_id):
    return MEANINGS.get(yoga_id, 'Značenje ove varijante još nije uređeno; pogledaj definiciju i napomenu izvora.')

def interpretation_note(result):
    if not result.present:
        return 'Ovo je opis yoge; njezini uvjeti u odabranoj karti nisu ispunjeni.'
    if result.cancellation_factors:
        return 'Prikazani uvjeti poništenja ili ublažavanja mijenjaju osnovno značenje; pročitaj ih uz opis.'
    if result.weakening_factors:
        return 'U ovoj karti postoje slabe točke, pa se osnovno značenje tumači opreznije.'
    return 'Izražavanje se procjenjuje kroz uključene kuće, snagu planeta i njihove daše.'
