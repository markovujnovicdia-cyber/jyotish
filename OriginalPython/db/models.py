"""
Jednostavni dataclass modeli koji odgovaraju SQLite tablicama.
Namjerno bez ORM-a - baza je mala i lokalna, sqlite3 je dovoljan.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Person:
    id: Optional[int]
    name: str
    birth_date: str        # 'YYYY-MM-DD'
    birth_time: str         # 'HH:MM:SS'
    birth_place: str        # naziv grada kako ga je korisnik unio
    country: str
    latitude: float
    longitude: float
    timezone: str            # IANA naziv, npr. 'Europe/Zagreb'
    time_confirmed: bool      # potvrđeno da je vrijeme rođenja sigurno
