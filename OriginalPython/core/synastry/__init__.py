"""
Sinastrija (usporedba dviju natalnih karata).

Faza 1 (dovršeno): modeli podataka, kućni overlay D1, Graha Drishti
između karata, stupanjske konjunkcije, osnovna tablica kontakata, osnovni
tekstualni izvještaj.

Faza 2 (dovršeno): core.chara_karaka (Atmakaraka/Darakaraka - NOVO, prije
nije postojalo nigdje u projektu), core/synastry/nakshatra_matching.py
(nakšatra sinastrija), ashtakoota.py (36-bodovna Kuta kompatibilnost),
kuja_dosha.py (stupnjevana Marsova afflikcija), relationship_significators.py
(7. kuća, Venera/Mars/Jupiter/Mjesec, AK/DK, AL/UL/A7 i unakrsne veze).

Faza 3 (dovršeno): core/synastry/divisional_synastry.py (D9 Navamsha
sinastrija - GENERIČKA arhitektura, spremna i za D7/D10/D12 uz drugu
varga_func), scoring.py + scoring_config.py (kategorijsko bodovanje, 9
kategorija, dedupliciranje spriječava dvostruko brojanje iste veze,
zasićujuća tanh krivulja sprječava neinformativno "zaravnjivanje" na
100/100 kod kontaktima bogatih karata), preklopljeni grafički prikaz u
ui/pages_synastry.py (D1/D9 prekidač, uključivi slojevi A/B, tekstualne
oznake ⟨X:planet⟩ umjesto oslanjanja na boju, izbornik s detaljima kao
zamjena za hover tooltip/klik-isticanje).

Faza 4 (dovršeno): core/synastry/transit_activations.py (aktivacija
natalne sinastrije tranzitom - konjunkcija, Graha Drishti, isti znak/
nakšatra, tranzit vladara nakšatre/dispozitora veze, D9 aktivacija;
generička veza NatalSynastryLink gradi se iz VEĆ izračunatih Graha Drishti/
konjunkcija/nakšatra kontakata), dasha_activations.py (Vimshottari Dasha
profili i uzajamne aktivacije preko core.dasha.get_current_dasha_5_levels),
predictive.py (dvostruki tranzit Jupitera/Saturna, jedan-datum "snapshot",
i vremenska crta preko raspona datuma s trakom napretka).

Faza 5 (dovršeno, POSLJEDNJA faza prema izvornoj specifikaciji):
- core/synastry/varshaphala_activations.py: Varshaphala (solarni
  povratak) i Mudda Dasha aktivacije u sinastriji - ponovno koristi
  core.varshaphala.compute_varshaphala u cijelosti (Muntha, Varsheshwara,
  Tajika Ithasala/Isarapha, Mudda Dasha - ne duplicira NIJEDAN izračun).
  VAŽNO: namjerno NE miješa Tajika aspekte s Parashari Graha Drishtijem -
  jedina aspektna metoda ovdje su već izračunati Ithasala/Isarapha parovi,
  jasno tako označeno u UI-u.
- core/synastry/monthly_daily_activations.py: fina mjesečna/dnevna
  analiza gdje je Mjesec izričito tretiran kao KRATKOTRAJNI OKIDAČ (ne
  samostalan dokaz), provjeren dan-po-dan preko 5 kategorija (aktivacija
  natalne veze, isti znak Venere/Marsa/Mjeseca/vladara 7., ulazak u UL/A7,
  ulazak u nakšatru Ascendenta/Darakarake, poklapanje s ≥2 aktivna spora
  tranzita istog dana). Kategorija (a) je ograničena na top 8 najjačih
  aktivacija po danu (sortirano po jačini) uz napomenu o ukupnom broju -
  otkriveno tijekom testiranja da Mjesec, ostajući ~2-3 dana u istom znaku,
  lako "pogodi" desetke pohranjenih natalnih veza istog dana bez ovog
  ograničenja.
- core/synastry/export.py: JSON (svi strukturirani rezultati + postavke +
  algoritam verzija), CSV (kontakti; vremenska crta zasebno), PDF (fpdf2,
  preoblikuje POSTOJEĆI tekstualni izvještaj - ne duplicira izračune) i
  izravan SVG download već generiranih overlay karata. Novi ovisan paket:
  fpdf2 (vidi requirements.txt).
- UI: Varshaphala sekcija u tabu "Prediktivna sinastrija" (godina
  solarnog povratka po osobi), Mjesečevi okidači u tabu "Vremenska crta"
  (tablica dana + izbornik za detalje jednog dana - NAMJERNO ne
  zaseban st.expander po danu, jer Streamlit drži sadržaj svih tabova
  mountan u DOM-u pa bi npr. 90 expandera nepotrebno usporilo cijelu
  stranicu), 4 gumba za izvoz u tabu "Izvještaj" plus 2 SVG gumba u tabu
  "Sažetak". Vremenska crta sad kešira rezultat u session_state po
  "otisku prsta" ulaza - promjena filtra teme više NE zahtijeva ponovni
  klik na "Izračunaj vremensku crtu" (poznati nedostatak iz Faze 4,
  ispravljen ovdje).

Ovaj modul NE računa nikakve nove astronomske podatke - sve pozicije,
kuće, nakshatre, dostojanstva i Graha Drishti geometrija dolaze iz
core/ (ephemeris, houses, nakshatra, varga, planet_strength, aspects,
special_points, natal, chara_karaka, dasha, transits, varshaphala,
tajika, varsheshwara). Sinastrija samo UNAKRSNO primjenjuje te iste
izračune na dvije osobe i dodaje interpretaciju/bodovanje specifične
za odnos.

Iskreno priznata ograničenja opsega (nisu implementirana, izvan opsega
dosadašnje arhitekture):
- Pravi crtani graf odnosa vladara nakšatri (trenutno samo tablični
  prikaz bridova) i puna klik-interaktivnost/hover na SVG karti (trenutno
  zamijenjena izbornikom - zahtijeva prilagođenu Streamlit komponentu s
  JS-om)
- Rasterizirani (PNG) izvoz karte - izvoz je SVG (već vektorski, bez
  dodatne ovisnosti poput cairosvg)
- Puna D7/D10/D12 sinastrija u UI-u (generička arhitektura u
  divisional_synastry.py to podržava - trenutno izložen samo D9 prekidač)
- Zapadnjački stupanjski aspekti (sekstil/kvadrat/trigon/opozicija) kao
  dodatni sloj uz konjunkcije - namjerno izostavljeno, spomenuto u
  postavkama kao još neimplementirana opcija
"""
