# Jyotish · nativni iPhone projekt

SwiftUI aplikacija za iOS 17+ sada koristi **lokalni Swift paket JyotishCore i
ugrađeni Swiss Ephemeris C 2.10.03**. Za računanje na iPhoneu nije potreban Mac,
Python, internet ni vanjski server. Xcode na Macu potreban je za kompilaciju,
simulator i instaliranje razvojne aplikacije.

## Pokretanje iPhone aplikacije

1. Na Macu otvorite `Jyotish.xcodeproj` u punom Xcodeu.
2. Odaberite zajedničku shemu `Jyotish` i iPhone simulator s iOS-om 17 ili novijim.
3. Pokrenite aplikaciju i dodajte osobu: lokalni datum/vrijeme rođenja, koordinate
   i IANA vremensku zonu. Postojeća ponavljanja sata pri DST-u traže odabir
   stvarnog trenutka; nepostojeće vrijeme se odbija.
4. Za fizički iPhone u Signing & Capabilities postavite svoj Team i Bundle ID.

**Stvarna Xcode kompilacija i simulator još nisu potvrđeni.** Razvojno okruženje
je Linux, bez Apple SDK-a. Pripremljena je ponovljiva provjera na macOS-u:

```sh
bash scripts/validate-ios.sh
```

Skripta gradi i testira aplikaciju u simulatoru te sprema zapis i novi `.xcresult`.
Istu provjeru izvodi `.github/workflows/ios.yml` kada promjene stignu u GitHub
repozitorij. Workflow još nije izvršen u ovom radu.

## Implementirano u nativnom računanju i sučelju

- Lahiri ayanamsha, siderealni zodijak, Mean Rahu/Ketu i Whole Sign kuće.
- Natalna karta i stvarni sjevernoindijski dijagram; D1/D7/D9/D10/D12 za planete i lagnu.
- Nakshatre/pade, Arudha Lagna, Upapada, Darapada, Bhrigu Bindu, Gulika i Mandi.
- Vimshottari kroz svih pet razina, puni početni period i pregled podrazdoblja.
- Varshaphala/aktivna godišnja karta, Muntha, svih pet kandidata Varsheshe i
  svih pet komponenti Panchavargiya Bale.
- Tajika aspekti, postojeće računske provjere 11 yoga za odabrani par i tri
  globalne provjere; svih 20 sahama i Mudda do sljedećeg solarnog povratka.
- Svih 12 Masa Praveša i tranzitni položaji.
- Lokalno spremanje, uređivanje i brisanje osoba; računanje u pozadini.

Nativni prikazi sadrže podatke i izračune, bez astroloških interpretacija.
`OriginalPython/` ostaje nepromijenjen referentni izvor, uključujući njegove
stare analize i izvještaje. Ostali Python moduli (primjerice sinastrija,
Ashtakavarga, Argala, Bhava Chalit, natalni yoga engine i PDF izvoz) nisu preneseni
u ovu nativnu inačicu; njihov izvor nije uklonjen ni zamijenjen.

## Testovi i provjerene razlike

```sh
bash scripts/test-core.sh
bash scripts/test-core.sh -c release
python3 scripts/validate_xcode_project.py
```

U ovom Linux okruženju stvarno je kompajlirana C/Swift računska jezgra i
**38 XCTest testova prolazi u Debug i Release konfiguraciji**. Referentni slučajevi
pokrivaju četiri natalne, pet godišnjih i 60 mjesečnih karata te stotine Tajika
provjera. Položaji se s istim Swiss datotekama uspoređuju unutar 1e-7 stupnja.
Ispravljena je i pogreška simulatora: Swiss Ephemeris tiho odbacuje putanje
dulje od 242 UTF-8 bajta. Takve se ugrađene efemeride sada pripremaju kao
identična kopija u kratkoj lokalnoj mapi. Za provjeru stvarnih resursa u putanji
duljoj od 350 bajtova na Linuxu pokrenite `bash scripts/test-long-resource-path.sh`
nakon builda. Astronomske formule i zabrana tihog Moshier fallbacka ostaju iste.

Dodatno su provjereni izvorni aplikacijski računski most i spremanje osoba na
Linuxu uz privremenu Combine zamjenu; to nije zamjena za SwiftUI/iOS test.

Izvorni Python paket: **225 prolazi, dva PDF testa padaju** zbog prethodno
postojećeg problema s hrvatskim znakovima u fontu Helvetica. Svih 128 datoteka
`OriginalPython/` ostalo je jednako ZIP izvoru.

Izvorni Python bez `.se1` datoteka prelazio je na Moshier. Nova aplikacija
ugrađuje Swiss podatke i odbija tihi fallback. Izmjerene razlike backendova i
popravak nepotvrđenog intervala solarnog povratka za neka rođenja 31. dana
objašnjeni su u [numeričkoj usporedbi](docs/NUMERICAL_PARITY.md). Masa sada
čuva sekunde, a unos rođenja koristi stvarnu odabranu zonu. Ostale navedene
konvencije izvornog računanja zadržane su; povijesna ispravnost Hadda tablice
nije dodatno potvrđena.

Efemeridne datoteke pokrivaju 1800–2399; godišnji izbor završava 2398 jer treba
i sljedeći povratak. Za zahtjev čiji stvarni povratak izlazi iz dostupnih
podataka prikazuje se pogreška. Izlazak/zalazak na polarnim lokacijama može biti
nedostupan; takva Gulika/Mandi vrijednost nije izmišljena.

## Licenca i status distribucije

Swiss Ephemeris traži **AGPL ili Professional License** prije distribucije.
Licencni izbor za cijelu aplikaciju nije donesen i profesionalni ugovor nije
pribavljen. Projekt nije objavljen na App Storeu. Detalji, izvorni pravni tekstovi
i porijeklo podataka su u [licencnoj bilješci](docs/SWISS_EPHEMERIS_LICENSE.md).

[Dokaz i ograničenja Xcode provjera](docs/XCODE_VALIDATION.md).
