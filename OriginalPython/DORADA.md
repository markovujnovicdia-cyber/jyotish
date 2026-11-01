Dorada 01.10.2026.

Karta je početna stranica; Osobe su zadnje. Sinastrija je uklonjena iz navigacije.
Karte, tablice i detalji biraju se zasebno; varge se prikazuju pojedinačno.
Tranzitni kotač ima točne oznake položaja i odabir planeta, sahama i posebnih točaka.
Dodano je 20 sahama za natalnu, godišnju i mjesečnu kartu.
Formule: PVR Narasimha Rao, Vedic Astrology: An Integrated Approach, §28.8, Table 74.
https://www.vedicastrologer.org/articles/vedic_astro_textbook.pdf
Metoda uključuje dan/noć i korekciju luka 30°. Rezultati se mogu razlikovati od stare verzije.
Stare formule u core/tajika.py ostaju samo za stare interne module; novi prikazi koriste core/sahams.py.

INSTALACIJA NA MACU
Zatvorite aplikaciju. Raspakirajte ZIP, otvorite Primijeni_doradu.command.
Skripta pronalazi postojeću mapu Dokumenti/jyotish_app, izrađuje sigurnosnu kopiju četiri
izmijenjene datoteke i zamjenjuje samo njih. Podaci, baza i postojeće okruženje ostaju sačuvani.
Pokrenite aplikaciju svojim postojećim Pokreni Jyotish.command.
Ako Mac ne dopušta skriptu, prenesite ručno app.py, core/sahams.py,
ui/pages_chart.py i ui/transit_wheel.py u odgovarajuće postojeće mape.
Nemojte zamijeniti cijelu mapu niti kopirati priloženu data mapu preko svoje novije baze.

Provjera: 28 postojećih testova prošlo; sve izmijenjene stranice i podprikazi provjereni
Streamlit AppTestom, uključujući datum tranzita; 3 izračunska primjera iz izvora prošla.
Prikaz kotača pregledan kao renderirani SVG. Prikaz na vašem Macu nije izravno provjeren.
Na manjim ekranima detaljne tablice mogu zahtijevati listanje.
