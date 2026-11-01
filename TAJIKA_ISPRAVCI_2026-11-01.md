# Tajika – ispravci u verziji 1. 11. 2026.

## Implementirano

1. Ispravljena zrcalna orijentacija konjunkcije, sekstila, kvadrata, trigona i opozicije (prije su se ± aspekti pogrešno odbacivali).
2. Ithasala i Isharafa izračunavaju se prema stvarnim potpisanim brzinama efemerida i smjeru približavanja točnom aspektu; egzaktna i stacionarna stanja zasebna su i ne proglašavaju se separacijom.
3. Tri-Rashi Pati tablica zamijenjena je Tajika tablicom prema *Hāyanaratna*, poglavlje 5, odjeljak 7.
4. Vivaha i Putra Saham računaju se jednako danju i noću, prema odabranoj fiksnoj varijanti, s korekcijom +30° prema zadanoj arc-metodi. Druge škole mogu koristiti drugačiju formulu.
5. Varsheshwara zahtijeva kvalificirani aspekt na godišnju lagnu, umjesto prisilnog izbora kada ga nema. Pancha Vargiya Bala/Hadda zahtijeva još vanjsku numeričku validaciju.
6. Mudda Dasha Varshaphale pokriva razmak do sljedećeg solarnog povratka umjesto stvaranja ~5-dnevne rupe; tradicionalni omjeri skalirani su na taj interval. Stari API bez krajnjeg datuma i dalje računa 360 dana.
7. Solarni povratak više se ne zaokružuje na cijelu minutu.
8. Kamboola se ne dodjeljuje automatski svakoj Ithasali s Mjesecom; zahtijeva odabrani Lagnesha/Karyesha i dodatni Mjesečev aspekt.
9. Dodan endpoint `POST /varshaphala` te pravi numerički godišnji prikaz u SwiftUI sučelju, bez interpretacija i bez ručnog unosa natalne lagne.
10. Kod sinastrijskih godišnjih profila, datum izvan godišnje karte više ne izaziva iznimku niti se izmišlja daša tog trenutka.

## Kako provjeriti

```bash
cd OriginalPython
python3 -m pip install -r requirements.txt -r requirements-dev.txt
python3 -m pytest -q
cd ../LocalEphemerisServer
python3 -m unittest -v test_server
```

Na Macu u Xcodeu otvoriti `Jyotish.xcodeproj`. iPhone i Mac moraju biti na pouzdanoj lokalnoj mreži, a Python server pokrenut. iOS build nije bilo moguće izvršiti u ovom razvojnom okruženju.

## Ostala ograničenja

- Nije proveden nezavisan astrološki benchmark Hadda i Pancha Vargiya Bale.
- Različite škole Tajike mogu dati druge rezultate za sahame i rangiranje kandidata.
- Dva ranije postojeća PDF testa nisu prolazila jer ugrađeni Helvetica font ne podržava hrvatske dijakritike. Nisu promijenjeni u ovom Tajika ispravku.
- Trenutna iPhone aplikacija ovisi o lokalnom Mac/Python servisu; nije samostalna offline aplikacija. Ostali iPhone moduli izvan natalnog i godišnjeg prikaza nisu još integrirani.

**Izvori:** Martin Gansten, *Hāyanaratna* (2020), [Triplicity Rulers](https://www.wisdomlib.org/hinduism/book/hayanaratna-the-jewel-of-annual-astrology/d/doc1500935.html) i [Ruler of the Year](https://www.wisdomlib.org/hinduism/book/hayanaratna-the-jewel-of-annual-astrology/d/doc1500936.html).
