"""
Geokodiranje mjesta rođenja u koordinate.

Ovo je JEDINI mrežni poziv koji aplikacija radi - upit prema javnom
Nominatim (OpenStreetMap) geocoding servisu, isključivo radi pretvorbe
naziva grada u koordinate. Nikakvi drugi podaci se ne šalju van računala.
"""

from dataclasses import dataclass
from geopy.geocoders import Nominatim

_geolocator = Nominatim(user_agent="privatna_jyotish_aplikacija")


@dataclass
class GeoResult:
    display_name: str
    latitude: float
    longitude: float


def geocode_city(city: str, country: str = "") -> GeoResult:
    """
    Traži koordinate grada. Ako je zadana i država, upit je precizniji.
    Baca ValueError ako grad nije pronađen - korisničko sučelje treba
    to uhvatiti i zatražiti precizniji unos prije spremanja osobe.
    """
    query = f"{city}, {country}" if country else city
    location = _geolocator.geocode(query)
    if location is None:
        raise ValueError(
            f"Nije moguće pronaći koordinate za '{query}'. "
            "Pokušaj s preciznijim nazivom (npr. dodaj državu ili regiju)."
        )
    return GeoResult(
        display_name=location.address,
        latitude=location.latitude,
        longitude=location.longitude,
    )
