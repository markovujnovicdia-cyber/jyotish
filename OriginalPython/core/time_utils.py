"""
Pomoćne funkcije za rad s vremenom: pretvaranje lokalnog vremena rođenja
(datum + vrijeme + grad) u UTC te izračun Julijanskog dana za Swiss Ephemeris.
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from timezonefinder import TimezoneFinder

_tf = TimezoneFinder()


def find_timezone(lat: float, lon: float) -> str:
    """
    Pronalazi IANA timezone string (npr. 'Europe/Zagreb') na temelju koordinata.
    Koristi se automatski nakon geokodiranja grada, prije spremanja osobe.
    """
    tz_name = _tf.timezone_at(lat=lat, lng=lon)
    if tz_name is None:
        # fallback za rijetke slučajeve (npr. točke na oceanu)
        tz_name = _tf.closest_timezone_at(lat=lat, lng=lon)
    if tz_name is None:
        raise ValueError("Nije moguće odrediti vremensku zonu za zadane koordinate.")
    return tz_name


def local_to_utc(date_str: str, time_str: str, tz_name: str) -> datetime:
    """
    date_str: 'YYYY-MM-DD'
    time_str: 'HH:MM' ili 'HH:MM:SS'
    tz_name: IANA naziv zone, npr. 'Europe/Zagreb'

    Vraća datetime u UTC-u. zoneinfo automatski uzima u obzir DST (ljetno/zimsko
    vrijeme) za povijesni datum, što je ključno za točan izračun.
    """
    if len(time_str.split(":")) == 2:
        time_str = time_str + ":00"
    naive = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    local_dt = naive.replace(tzinfo=ZoneInfo(tz_name))
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
    return utc_dt


def utc_to_julian_day(utc_dt: datetime) -> float:
    """
    Pretvara UTC datetime u Julijanski dan (UT), format koji swisseph očekuje.
    Uvoz swisseph je lokalan da izbjegnemo tvrdu ovisnost u modulima koji
    ovu funkciju ne koriste direktno.
    """
    import swisseph as swe

    hour_decimal = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour_decimal)
    return jd
