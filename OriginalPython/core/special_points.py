"""
Posebne osjetljive točke (upagraha/pada), dodatne uz 9 planeta:

- AL (Arudha Lagna): "projekcija" ascendenta - kako svijet percipira osobu.
  Formula (Jaimini): prebroji udaljenost (u znakovima) od Lagne do njenog
  vladara, pa istu udaljenost prebroji dalje od vladara. Iznimka (BPHS,
  poglavlje o Arudhama - "Own house, Seventh house cannot become Arudha
  of a house"): Arudha ne smije ispasti ISTA kao kuća sama, ni njen 7.
  znak. TOČNA zamjena OVISI koji je slučaj:
    - ako rezultat padne u ISTI znak kao kuća -> uzmi 10. znak OD KUĆE
    - ako rezultat padne u 7. znak OD KUĆE -> uzmi 4. znak OD KUĆE (NE
      10. - ovo je čest izvor grešaka; 4. je zapravo "10. znak od mjesta
      gdje je Arudha privremeno pala", što se svodi na 4. od kuće jer je
      ta privremena pozicija već sama 7. od kuće: 6+9=15=3 -> 4. znak)
  Formula potvrđena protiv nezavisnog izvora (BPHS Arudha poglavlje,
  prijevod Madura Krishnamurthi Sastri, saptarishisastrology.com) s
  eksplicitnom tablicom slučajeva.

- UL (Upapada Lagna): Arudha Pada 12. kuće (A12) - klasična Jaimini točka
  za brak/partnerstva (analogna AL-u, ali za 12. kuću umjesto za Lagnu).
  ISTA formula i ISTA iznimka kao AL (vidi gore), samo primijenjena na
  12. kuću umjesto na Lagnu.

- A7 (Darapada): Arudha Pada 7. kuće - klasična Jaimini točka za brak/
  partnerstva (dopunjuje UL, koji je danas mnogo autora smatra glavnom
  bračnom točkom, dok je A7/Darapada starija/tradicionalnija). ISTA
  formula i ISTA iznimka kao AL (vidi gore), samo primijenjena na 7.
  kuću.

- BP (Bhrigu Bindu): matematička sredina između Rahua i Mjeseca, računajući
  KRAĆI luk od Rahua prema Mjesecu (u smjeru kretanja). Potvrđeno protiv
  više neovisnih izvora s brojčanim primjerima.

- GK (Gulika, zvana i Mandi): osjetljiva točka vezana uz Saturn. Dan (ili
  noć) rođenja dijeli se na 8 jednakih dijelova, svaki dio ima svog
  "vladara" (planetu) prema danu u tjednu; Gulika je ascendent koji je bio
  na horizontu na POČETKU dijela kojim vlada Saturn (BPHS: "gulikārambha-
  kāle yat sphuṭaṁ" - "u trenutku POČETKA Gulike"; tumačenje da se uzima
  KRAJ dijela je izričito označeno kao pogrešno u tradicionalnim izvorima).
  Cijeli postupak (dnevni redoslijed vladara od vladara dana u tjednu;
  noćni redoslijed od vladara 5. dana u tjednu računajući od dana rođenja;
  formula za koji je dio Saturnov; korištenje početka a ne kraja dijela)
  je unakrsno provjeren protiv više neovisnih tradicionalnih izvora i
  radnih primjera (npr. "Saturn je uvijek 7. dio za nedjelju", "noć srijede
  počinje od nedjelje" - oba se poklapaju s ovom implementacijom).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from core.constants import RASHI, RASHI_LORD

# Redoslijed planeta po danu u tjednu (klasični redoslijed dana), koristi se
# i za dnevne/noćne dijelove za Guliku. Python weekday(): Monday=0 ... Sunday=6
_WEEKDAY_LORD_ORDER = ["Sunce", "Mjesec", "Mars", "Merkur", "Jupiter", "Venera", "Saturn"]
# indeks u _WEEKDAY_LORD_ORDER za dan u tjednu (0=ponedjeljak...6=nedjelja od Pythona)
# PROVJERENO protiv opće poznate, nesporne astrološke činjenice (nedjelja=Sunce,
# ponedjeljak=Mjesec, utorak=Mars, srijeda=Merkur, četvrtak=Jupiter, petak=Venera,
# subota=Saturn - vidljivo i iz imena dana u većini europskih jezika).
_PYTHON_WEEKDAY_TO_LORD_INDEX = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0}
# ponedjeljak->Mjesec(idx1), utorak->Mars(2), srijeda->Merkur(3), četvrtak->Jupiter(4),
# petak->Venera(5), subota->Saturn(6), nedjelja->Sunce(0)


def compute_arudha_pada_sign_index(house_sign_index: int, planet_sign_index_map: dict) -> int:
    """
    Opća Jaimini Arudha Pada formula, primjenjiva na BILO KOJU kuću (ne
    samo Lagnu): prebroji udaljenost (u znakovima) od kuće do njenog
    vladara, pa istu udaljenost prebroji dalje od vladara.

    Iznimka (BPHS, Arudha poglavlje): rezultat NE SMIJE ispasti isti znak
    kao kuća sama, niti njen 7. znak. Zamjena OVISI koji je slučaj (ovo
    NIJE uvijek "10. znak od kuće" - čest izvor grešaka):
      - rezultat == kuća sama       -> uzmi 10. znak OD KUĆE
      - rezultat == 7. znak od kuće -> uzmi 4. znak OD KUĆE (ne 10.)
    (Oba slučaja su zapravo "10. znak od PRIVREMENOG rezultata" - u prvom
    slučaju je privremeni rezultat = kuća, pa 10. od njega = 10. od kuće;
    u drugom je privremeni rezultat = 7. od kuće, pa 10. od njega =
    7+9=16=4. znak od kuće.)

    house_sign_index: sign_index (0-11) kuće za koju se traži Arudha Pada
    planet_sign_index_map: {naziv_planeta: sign_index} za sve planete (D1)
    """
    house_sign_name = RASHI[house_sign_index]
    lord = RASHI_LORD[house_sign_name]
    lord_sign_index = planet_sign_index_map[lord]

    distance = (lord_sign_index - house_sign_index) % 12
    pada_index = (lord_sign_index + distance) % 12

    if pada_index == house_sign_index:
        pada_index = (house_sign_index + 9) % 12  # 10. znak od kuće
    elif pada_index == (house_sign_index + 6) % 12:
        pada_index = (house_sign_index + 3) % 12  # 4. znak od kuće

    return pada_index


def compute_arudha_lagna_sign_index(ascendant_sign_index: int, planet_sign_index_map: dict) -> int:
    """
    AL = Arudha Pada 1. kuće (Lagne). planet_sign_index_map: {naziv_planeta:
    sign_index} za sve planete (D1). Vraća sign_index (0-11) Arudha Lagne.
    """
    return compute_arudha_pada_sign_index(ascendant_sign_index, planet_sign_index_map)


def compute_upapada_lagna_sign_index(ascendant_sign_index: int, planet_sign_index_map: dict) -> int:
    """
    UL = Arudha Pada 12. kuće (A12), računata od Lagne. Vidi napomenu na
    vrhu ove datoteke.
    """
    twelfth_house_sign_index = (ascendant_sign_index + 11) % 12
    return compute_arudha_pada_sign_index(twelfth_house_sign_index, planet_sign_index_map)


def compute_darapada_sign_index(ascendant_sign_index: int, planet_sign_index_map: dict) -> int:
    """
    A7 (Darapada) = Arudha Pada 7. kuće, računata od Lagne. Vidi napomenu
    na vrhu ove datoteke.
    """
    seventh_house_sign_index = (ascendant_sign_index + 6) % 12
    return compute_arudha_pada_sign_index(seventh_house_sign_index, planet_sign_index_map)


def compute_bhrigu_bindu(moon_longitude: float, rahu_longitude: float) -> float:
    """Vraća apsolutnu sidereal dužinu (0-360) Bhrigu Bindua."""
    forward_arc = (moon_longitude - rahu_longitude) % 360.0
    return (rahu_longitude + forward_arc / 2.0) % 360.0


@dataclass
class GulikaResult:
    longitude: float
    is_day_birth: bool
    segment_number: int  # 1-8
    weekday_for_lord: int = 0  # dan u tjednu (Python konvencija) STVARNO korišten za vladara - uzima u obzir noćni pomak za rano jutro
    period_start: Optional[datetime] = None  # početak dnevnog/noćnog razdoblja (za Mandi referentnu točku)
    mandi_longitude: Optional[float] = None       # pojednostavljena (fiksna ghatika) alternativa
    mandi_ghatikas: Optional[float] = None


# Mandi (POJEDNOSTAVLJENA, fiksna metoda) - NIJE isto što i Gulika iznad.
# Neki izvori/softveri koriste ovu jednostavniju tablicu koja PRETPOSTAVLJA
# da dan (i noć) uvijek traje točno 30 ghatija (12h), umjesto da stvarno
# izmjeri lokalni izlazak/zalazak Sunca i podijeli STVARNO trajanje dana na
# 8 dijelova. To je netočno za sve dane osim onih blizu ekvinocija, i daje
# sve veću grešku što je dan/noć duži ili kraći od točno 12h (npr. zimi na
# sjevernim geografskim širinama). Držimo ovo ODVOJENO i jasno označeno -
# NIJE preporučena metoda, nego dostupna kao alternativna/usporedna opcija.
# Provjereno protiv više neovisnih izvora (uključujući dan I noć tablicu).
MANDI_GHATIKA_TABLE_DAY = {
    6: 26.0,  # nedjelja (Python weekday=6)
    0: 22.0,  # ponedjeljak
    1: 18.0,  # utorak
    2: 14.0,  # srijeda
    3: 10.0,  # četvrtak
    4: 6.0,   # petak
    5: 2.0,   # subota
}
MANDI_GHATIKA_TABLE_NIGHT = {
    6: 10.0,  # nedjelja (Python weekday=6)
    0: 6.0,   # ponedjeljak
    1: 2.0,   # utorak
    2: 26.0,  # srijeda
    3: 22.0,  # četvrtak
    4: 18.0,  # petak
    5: 14.0,  # subota
}
GHATIKA_MINUTES = 24.0  # 1 ghatika = 24 minute (60 ghatija = 24 sata)


@dataclass
class MandiResult:
    longitude: float
    ghatikas_after_sunrise: float


def compute_mandi_fixed_ghatika(
    reference_utc: datetime, birth_weekday_python: int,
    is_day_birth: bool, ascendant_longitude_at,
) -> Optional[MandiResult]:
    """
    POJEDNOSTAVLJENA (ne preporučena) alternativa Gulici - koristi fiksnu
    ghatika tablicu umjesto stvarne podjele dana. reference_utc je početak
    relevantnog razdoblja (izlazak Sunca za dan, ISPRAVAN zalazak - večerašnji
    ili prethodni - za noć, već ispravno određen u compute_gulika).
    """
    table = MANDI_GHATIKA_TABLE_DAY if is_day_birth else MANDI_GHATIKA_TABLE_NIGHT
    if birth_weekday_python not in table:
        return None
    ghatikas = table[birth_weekday_python]
    mandi_time = reference_utc + timedelta(minutes=ghatikas * GHATIKA_MINUTES)
    return MandiResult(longitude=ascendant_longitude_at(mandi_time), ghatikas_after_sunrise=ghatikas)


def compute_gulika(
    birth_dt_utc: datetime,
    birth_weekday_python: int,
    sunrise_utc: datetime,
    sunset_utc: datetime,
    prev_sunset_utc: datetime,
    next_sunrise_utc: datetime,
    ascendant_longitude_at,
) -> GulikaResult:
    """
    ascendant_longitude_at: funkcija (datetime_utc) -> ascendant_longitude,
    koja poziva swisseph za dani trenutak (koristi core.ephemeris.get_ascendant
    uz pretvorbu u Julijanski dan).

    sunrise_utc/sunset_utc: izlazak/zalazak Sunca NA DAN rođenja.
    prev_sunset_utc: zalazak Sunca PRETHODNOG dana (za slučaj rođenja noću prije ponoći).
    next_sunrise_utc: izlazak Sunca SLJEDEĆEG dana (za slučaj rođenja poslije ponoći, prije izlaska).
    """
    is_day = sunrise_utc <= birth_dt_utc < sunset_utc

    if is_day:
        period_start = sunrise_utc
        period_end = sunset_utc
        weekday_for_lord = birth_weekday_python
    else:
        if birth_dt_utc >= sunset_utc:
            # noć koja počinje VEČERAS - pripada DANAŠNJEM danu u tjednu
            period_start = sunset_utc
            period_end = next_sunrise_utc
            weekday_for_lord = birth_weekday_python
        else:
            # rođenje prije jutrošnjeg izlaska Sunca - ta noć je počela
            # PRETHODNE večeri, pa "vlasnik" te noći je JUČERAŠNJI dan u
            # tjednu, ne današnji (klasična konvencija: dan počinje izlaskom
            # Sunca, ne ponoći)
            period_start = prev_sunset_utc
            period_end = sunrise_utc
            weekday_for_lord = (birth_weekday_python - 1) % 7

    start_lord_index = _PYTHON_WEEKDAY_TO_LORD_INDEX[weekday_for_lord]
    if is_day:
        sequence_start = start_lord_index
    else:
        # noćni dijelovi kreću od 5. planeta (uključivo) od dnevnog vladara
        sequence_start = (start_lord_index + 4) % 7

    saturn_index_in_order = _WEEKDAY_LORD_ORDER.index("Saturn")
    i = (saturn_index_in_order - sequence_start) % 7
    segment_number = i + 1  # 1-8, Saturnov dio

    segment_duration = (period_end - period_start) / 8
    segment_start_time = period_start + segment_duration * (segment_number - 1)

    gulika_longitude = ascendant_longitude_at(segment_start_time)

    return GulikaResult(
        longitude=gulika_longitude, is_day_birth=is_day, segment_number=segment_number,
        weekday_for_lord=weekday_for_lord, period_start=period_start,
    )


def compute_gulika_from_birth_data(
    birth_jd_ut: float,
    birth_local_date_str: str,
    latitude: float,
    longitude: float,
) -> "GulikaResult":
    """
    Praktični wrapper: sam računa izlazak/zalazak Sunca (swisseph
    rise_trans) za dan rođenja na zadanoj lokaciji, pa poziva compute_gulika.
    Koristi se i za natalnu i za Varshaphala (Gulika trenutka solarnog
    povratka) kartu.
    """
    import swisseph as swe
    from datetime import timezone as _tz
    from core.ephemeris import get_ascendant
    from core.time_utils import utc_to_julian_day

    geopos = (longitude, latitude, 0)

    def _rise_or_set(jd_start, rsmi):
        _flag, tret = swe.rise_trans(jd_start, swe.SUN, rsmi, geopos)
        return tret[0]

    def _jd_to_dt(jd):
        y, m, d, h = swe.revjul(jd)
        hour = int(h)
        minute = int((h - hour) * 60)
        return datetime(y, m, d, hour, minute, tzinfo=_tz.utc)

    # Robusno traženje izlaska/zalaska Sunca NA DAN rođenja: krene se
    # pretraga 1.5 dana prije rođenja (dovoljna margina za bilo koje
    # geografsko doba/mjesto), pa se provjeri bracket-a li nađeni par
    # ispravno trenutak rođenja - ako se nađeni zalazak dogodio PRIJE
    # rođenja, taj par pripada prethodnom danu pa se uzima SLJEDEĆI par.
    # Ovo izbjegava fiksnu "-1.2 dana" pretpostavku koja može, ovisno o
    # dužini dana na toj lokaciji/datumu, uhvatiti pogrešan kalendarski dan.
    candidate_sunrise = _rise_or_set(birth_jd_ut - 1.5, swe.CALC_RISE)
    candidate_sunset = _rise_or_set(candidate_sunrise, swe.CALC_SET)

    if candidate_sunset < birth_jd_ut:
        # ovaj par je iz proslog dana (rođenje je poslije ovog zalaska) -
        # treba sljedeći par
        sunrise_today = _rise_or_set(candidate_sunset, swe.CALC_RISE)
        sunset_today = _rise_or_set(sunrise_today, swe.CALC_SET)
        prev_sunset = candidate_sunset
    else:
        sunrise_today = candidate_sunrise
        sunset_today = candidate_sunset
        prev_sunset = _rise_or_set(candidate_sunrise - 1.5, swe.CALC_SET)

    next_sunrise = _rise_or_set(sunset_today, swe.CALC_RISE)

    local_date = datetime.strptime(birth_local_date_str, "%Y-%m-%d")
    weekday_python = local_date.weekday()

    def ascendant_longitude_at(dt):
        jd = utc_to_julian_day(dt)
        return get_ascendant(jd, latitude, longitude)

    gulika_result = compute_gulika(
        birth_dt_utc=_jd_to_dt(birth_jd_ut),
        birth_weekday_python=weekday_python,
        sunrise_utc=_jd_to_dt(sunrise_today),
        sunset_utc=_jd_to_dt(sunset_today),
        prev_sunset_utc=_jd_to_dt(prev_sunset),
        next_sunrise_utc=_jd_to_dt(next_sunrise),
        ascendant_longitude_at=ascendant_longitude_at,
    )

    mandi = compute_mandi_fixed_ghatika(
        gulika_result.period_start, gulika_result.weekday_for_lord,
        gulika_result.is_day_birth, ascendant_longitude_at,
    )
    if mandi is not None:
        gulika_result.mandi_longitude = mandi.longitude
        gulika_result.mandi_ghatikas = mandi.ghatikas_after_sunrise

    return gulika_result
