"""
Pomoćna funkcija za prikaz tablica bez skrolanja - Streamlit dataframe
inače ograničava visinu i prikazuje unutarnji scroll ako ima puno redaka;
ovdje izračunamo točnu visinu potrebnu za sve retke odjednom.
"""

_HEADER_HEIGHT = 38
_ROW_HEIGHT = 35
_BUFFER = 3


def full_table_height(rows: list) -> int:
    """Visina (u pikselima) dovoljna da se cijela tablica prikaže bez skrolanja."""
    return _HEADER_HEIGHT + _ROW_HEIGHT * max(len(rows), 1) + _BUFFER
