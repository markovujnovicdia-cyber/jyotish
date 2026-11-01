"""
Sloj za pristup lokalnoj SQLite bazi (data/jyotish.db).
Baza se nikad ne šalje nikamo - postoji isključivo na disku korisnika.
"""

import os
import sqlite3
from typing import List, Optional

from db.models import Person

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "jyotish.db")


def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            birth_time TEXT NOT NULL,
            birth_place TEXT NOT NULL,
            country TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            timezone TEXT NOT NULL,
            time_confirmed INTEGER NOT NULL DEFAULT 0
        )
    """)
    # Događajni dnevnik je uklonjen iz aplikacije - obriši staru tablicu (i
    # njen sadržaj) ako postoji od prijašnje verzije.
    cur.execute("DROP TABLE IF EXISTS events")
    # Pamti odabranu VRSTU ODNOSA po PARU osoba (core.synastry.
    # relationship_profiles) - rješava prijavljenu grešku da se izbor "tiho"
    # gubi/zamjenjuje pri ponovnom otvaranju iste sinastrije. Nema starih
    # podataka za migrirati - sinastrija prije ovoga nije ništa spremala.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS synastry_preferences (
            person_a_id INTEGER NOT NULL,
            person_b_id INTEGER NOT NULL,
            relationship_type TEXT NOT NULL,
            PRIMARY KEY (person_a_id, person_b_id)
        )
    """)
    conn.commit()
    conn.close()


# --- Persons -----------------------------------------------------------

def save_person(p: Person) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO persons (name, birth_date, birth_time, birth_place, country,
                              latitude, longitude, timezone, time_confirmed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (p.name, p.birth_date, p.birth_time, p.birth_place, p.country,
          p.latitude, p.longitude, p.timezone, int(p.time_confirmed)))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def list_persons() -> List[Person]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM persons ORDER BY name").fetchall()
    conn.close()
    return [
        Person(
            id=r["id"], name=r["name"], birth_date=r["birth_date"], birth_time=r["birth_time"],
            birth_place=r["birth_place"], country=r["country"], latitude=r["latitude"],
            longitude=r["longitude"], timezone=r["timezone"], time_confirmed=bool(r["time_confirmed"]),
        )
        for r in rows
    ]


def get_person(person_id: int) -> Optional[Person]:
    conn = get_connection()
    r = conn.execute("SELECT * FROM persons WHERE id = ?", (person_id,)).fetchone()
    conn.close()
    if r is None:
        return None
    return Person(
        id=r["id"], name=r["name"], birth_date=r["birth_date"], birth_time=r["birth_time"],
        birth_place=r["birth_place"], country=r["country"], latitude=r["latitude"],
        longitude=r["longitude"], timezone=r["timezone"], time_confirmed=bool(r["time_confirmed"]),
    )


def update_person(p: Person) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE persons
        SET name = ?, birth_date = ?, birth_time = ?, birth_place = ?, country = ?,
            latitude = ?, longitude = ?, timezone = ?, time_confirmed = ?
        WHERE id = ?
    """, (p.name, p.birth_date, p.birth_time, p.birth_place, p.country,
          p.latitude, p.longitude, p.timezone, int(p.time_confirmed), p.id))
    conn.commit()
    conn.close()


def delete_person(person_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM persons WHERE id = ?", (person_id,))
    conn.commit()
    conn.close()


# --- Sinastrija: preferencija vrste odnosa po paru osoba ----------------

def _normalized_pair(person_a_id: int, person_b_id: int):
    """
    Par se pamti NEOVISNO o tome tko je odabran kao 'Osoba A' a tko kao
    'Osoba B' u tom trenutku - "Lea+Marko" i "Marko+Lea" moraju pogoditi
    ISTU spremljenu preferenciju.
    """
    return (person_a_id, person_b_id) if person_a_id <= person_b_id else (person_b_id, person_a_id)


def save_synastry_relationship_type(person_a_id: int, person_b_id: int, relationship_type: str) -> None:
    pair_a, pair_b = _normalized_pair(person_a_id, person_b_id)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO synastry_preferences (person_a_id, person_b_id, relationship_type)
        VALUES (?, ?, ?)
        ON CONFLICT(person_a_id, person_b_id) DO UPDATE SET relationship_type = excluded.relationship_type
    """, (pair_a, pair_b, relationship_type))
    conn.commit()
    conn.close()


def get_synastry_relationship_type(person_a_id: int, person_b_id: int) -> Optional[str]:
    pair_a, pair_b = _normalized_pair(person_a_id, person_b_id)
    conn = get_connection()
    r = conn.execute(
        "SELECT relationship_type FROM synastry_preferences WHERE person_a_id = ? AND person_b_id = ?",
        (pair_a, pair_b),
    ).fetchone()
    conn.close()
    return r["relationship_type"] if r is not None else None
