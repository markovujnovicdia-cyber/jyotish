# Jyotish aplikacija (privatna, lokalna)

Privatna lokalna Jyotish aplikacija za osobnu upotrebu. Radi isključivo na
tvom računalu, bez hostinga, bez domene, bez javnog pristupa i bez login
sustava. Jedini mrežni poziv koji aplikacija radi je pretraga koordinata
grada (geocoding) prilikom unosa nove osobe - ništa se drugo ne šalje van
računala.

## Astrološke postavke (fiksne u ovoj verziji)

- Ayanamsha: Lahiri
- Zodijak: sidereal
- Rahu/Ketu: mean node
- Sustav kuća: Whole Sign
- Prikaz karte: sjevernoindijski dijamant

## 1. Instalacija (testiranje kao web aplikacija u pregledniku)

Preduvjet: Python 3.10 ili noviji (provjeri s `python3 --version`).

```bash
cd jyotish_app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Pokretanje:

```bash
streamlit run app.py
```

Aplikacija se otvara na `http://localhost:8501`.

### Pokretanje testova

```bash
pip install -r requirements-dev.txt
pytest tests/
```

## 2. Pokretanje kao desktop prozor (bez adrese preglednika)

Dodatna instalacija:

```bash
pip install -r requirements-desktop.txt
```

Pokretanje:

```bash
python desktop_launcher.py
```

Ovo otvara nativni prozor (macOS WKWebView) koji prikazuje aplikaciju -
izgleda kao desktop app, iako ispod radi isti lokalni Streamlit server.

## 3. Pakiranje u pravu .app datoteku (dvoklik za pokretanje)

Kad si zadovoljan/na da sve radi kroz `desktop_launcher.py`, spakiraj u
samostalnu .app aplikaciju pomoću PyInstaller-a:

```bash
pyinstaller --name "Jyotish" --windowed --onedir \
  --add-data "app.py:." \
  --add-data "core:core" \
  --add-data "db:db" \
  --add-data "ui:ui" \
  desktop_launcher.py
```

Gotova aplikacija bit će u `dist/Jyotish/Jyotish.app`. Možeš je premjestiti
u `/Applications` i pokretati dvoklikom kao svaku drugu Mac aplikaciju.

Napomena: PyInstaller ponekad treba dodatno podešavanje za pakete poput
`pyswisseph` (koji uključuje binarne ephemeris datoteke) i `timezonefinder`
(koji uključuje podatkovne datoteke). Ako se aplikacija ne pokrene nakon
pakiranja, prva provjera je jesu li sve potrebne data-datoteke uključene -
javi mi grešku iz terminala pa riješimo zajedno.

## Struktura projekta

```
jyotish_app/
  app.py                    - glavna Streamlit aplikacija
  desktop_launcher.py       - pokreće app kao desktop prozor
  requirements.txt          - osnovne ovisnosti
  requirements-desktop.txt  - dodatne ovisnosti za desktop pakiranje
  data/                     - SQLite baza (jyotish.db), stvara se automatski
  core/                     - astrološka logika (bez UI-a)
    constants.py, time_utils.py, geocoding.py, ephemeris.py, natal.py
    nakshatra.py, houses.py, varga.py, dasha.py, transits.py
    special_points.py, argala.py, aspects.py, ashtakavarga.py
    planet_strength.py, combustion.py, yogas.py, panchang.py
    tajika.py, karyesha_yogas.py, varshaphala.py, varsheshwara.py
    masa_pravesha.py, chara_karaka.py
    synastry/                - sinastrijski modul (Faza 1-5, vidi ispod)
      config.py, models.py, overlays.py, graha_drishti.py
      conjunctions.py, interpretation.py, report.py
      nakshatra_matching.py, ashtakoota.py, kuja_dosha.py
      relationship_significators.py
      divisional_synastry.py, scoring.py, scoring_config.py
      transit_activations.py, dasha_activations.py, predictive.py
      varshaphala_activations.py, monthly_daily_activations.py, export.py
  db/                       - sloj baze podataka
    database.py, models.py
  ui/                       - Streamlit stranice i prikazi
    north_indian_chart.py, rect_chart.py, aspect_wheel.py, transit_wheel.py
    chart_labels.py, df_utils.py, export_chatgpt.py
    pages_persons.py, pages_chart.py, pages_synastry.py
  tests/                    - pytest testovi (core logika, uklj. sinastriju)
```

## Status implementacije

**Natalna karta (potpuno implementirano):**
- Unos i spremanje osoba (SQLite), s automatskim geokodiranjem i
  potvrdom sigurnog vremena rođenja
- D1 (Rashi), D7 (Saptamsha), D9 (Navamsha), D10 (Dashamsha), D12
  (Dvadashamsha) - sve formule provjerene protiv referentne literature
  (vidi `core/varga.py`)
- Nakshatra i pada za svaki planet
- Whole Sign kuće (osnovni sustav) i Bhava Chalit (dodatni prikaz)
- Sjevernoindijski dijamant prikaz karte
- Arudha Lagna (AL), Upapada Lagna (UL), Darapada (A7), Bhrigu Bindu (BP),
  Gulika/Mandi - `core/special_points.py`
- Vimshottari Dasha (5 razina: Maha/Antar/Pratyantar/Sookshma/Prana)
- Tranziti (od ascendenta i od Mjeseca), Ashtakavarga i Kakshya
- Varshaphala (solarni povratak, Muntha, Varsheshwara, Tajika
  aspekti/Sahami/yoge, Mudda Dasha), Masa Pravesha
- Argala, odabrane Yoge (Pancha Mahapurusha, Gajakesari, Chandra-Mangal,
  Budhaditya), snaga planeta (pojednostavljena, ne puni Shadbala)
- Gumb "Kopiraj za ChatGPT" s strukturiranim sažetkom karte

**Sinastrija (Faza 1-5 implementirana - sve faze prema izvornoj specifikaciji,
`core/synastry/`, `core/chara_karaka.py` i `ui/pages_synastry.py`):**
- Kućni overlay D1 (oba smjera, Whole Sign + Bhava Chalit) s dispozitorom,
  nakšatrom, dostojanstvom i odnosom prema vladaru kuće
- Graha Drishti između karata (klasična Parashari metoda, konfigurabilan
  tretman Rahu/Ketu)
- Stupanjske konjunkcije (konfigurabilni orbisi, ispravno preko granice
  znaka)
- Chara Karake (Atmakaraka/Darakaraka - novo, `core/chara_karaka.py`,
  konfigurabilna 7- ili 8-karaka shema)
- Nakšatra sinastrija (Mjesec/Ascendent/Venera/Mars/Sunce/vladar 7./
  Darakaraka - Gana/Yoni/Nadi/devata, unakrsne veze preko vladara
  nakšatri, ponovljeni obrasci, tablični graf odnosa)
- Ashtakoota (Guna Milan, 36 bodova - svih 8 kuta, s tradicionalnim
  poništenjima Bhakoot/Nadi Doshe gdje su pouzdano potvrđena)
- Kuja (Mangal) Dosha (stupnjevana procjena, konfigurabilne kuće,
  tradicionalna poništenja, uzajamno uravnoteženje)
- Ključni signifikatori odnosa (7. kuća, Venera/Mars/Jupiter/Mjesec,
  Atmakaraka/Darakaraka, Arudha Lagna, Upapada Lagna, Darapada i njihove
  unakrsne veze)
- D9 (Navamsha) sinastrija (generička arhitektura, spremna i za D7/D10/D12)
  s ponovljenim obrascima D1↔D9
- Kategorijsko bodovanje (9 kategorija, 0-100, transparentan raspis po
  faktoru, dedupliciranje sprječava dvostruko brojanje iste veze,
  zasićujuća krivulja sprječava neinformativno "zaravnjivanje" na 100/100)
- Preklopljeni grafički prikaz (D1/D9 prekidač, uključivi slojevi A/B,
  tekstualne oznake umjesto oslanjanja na boju, izbornik s detaljima
  planeta kao praktična zamjena za hover tooltip/klik-isticanje)
- Osnovni tekstualni izvještaj (13 sekcija, izvoz u .txt)
- Prediktivna sinastrija: tranziti prema objema kartama za odabrani datum,
  aktivacija natalne sinastrije tranzitom (konjunkcija/Graha Drishti/isti
  znak/nakšatra/vladar nakšatre/dispozitor/D9), dvostruki tranzit Jupitera
  i Saturna, Vimshottari Dasha aktivacije i uzajamne dasha veze
- Vremenska crta (raspon datuma, dnevni/tjedni/mjesečni korak, ukupna
  jačina aktivacije, filtriranje po temi, traka napretka za veće raspone,
  rezultat se kešira u session_state po "otisku prsta" ulaza - promjena
  filtra teme ne zahtijeva ponovni izračun)
- Varshaphala (solarni povratak)/Mudda Dasha aktivacije u sinastriji -
  godina solarnog povratka po osobi, preklapanja s osjetljivim točkama
  (Varsha Lagna/Muntha/godišnja 7./Varsha AL), Mudda Dasha aktivacija
  natalnih veza. Metoda je isključivo Tajika Ithasala/Isarapha - namjerno
  se NE miješa s Parashari Graha Drishtijem
- Fina mjesečna/dnevna analiza (Mjesec kao kratkotrajni okidač, ne
  samostalan dokaz): aktivacija natalne veze, isti znak ključnih planeta,
  ulazak u UL/A7, ulazak u nakšatru Ascendenta/Darakarake, poklapanje s
  ≥2 aktivna spora tranzita - prikaz kroz tablicu dana + izbornik detalja
- Izvoz: JSON (svi strukturirani rezultati), CSV (kontakti i posebno
  vremenska crta), PDF (fpdf2, preoblikuje tekstualni izvještaj), izravan
  SVG download overlay karata
- Iskreno nedovršeno/izvan opsega: pravi crtani graf vladara nakšatri
  (trenutno tablični prikaz bridova), puna klik-interaktivnost/hover na
  SVG karti (izbornik kao praktična zamjena), rasterizirani (PNG) izvoz
  karte, puna D7/D10/D12 sinastrija u UI-u (arhitektura to podržava, UI
  izlaže samo D9), zapadnjački stupanjski aspekti kao dodatni sloj

## Napomena o Swiss Ephemeris licenci

Ova aplikacija koristi `pyswisseph`, Python omot oko Swiss Ephemeris
biblioteke (Astrodienst AG). Swiss Ephemeris se smije besplatno koristiti
za privatne, nekomercijalne svrhe pod AGPL licencom. Ako bi u budućnosti
ova aplikacija bila objavljena, distribuirana drugima ili korištena u
komercijalne svrhe, potrebno je ili objaviti izvorni kod pod AGPL uvjetima
ili kupiti komercijalnu licencu od Astrodiensta. Za privatnu upotrebu na
vlastitom računalu (svrha ove aplikacije) nema dodatnih obveza.

Detalji: https://www.astro.com/swisseph/
