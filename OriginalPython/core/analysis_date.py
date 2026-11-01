"""
Centralni servis za referentni datum/vrijeme analize.

Sva mjesta u aplikaciji koja trebaju "trenutačni datum" radi određivanja
NEČEGA AKTIVNOG (npr. koja je Varshaphala trenutačno aktivna) moraju taj
datum dobiti kroz ovaj servis, a ne pozivati datetime.now() izravno -
time je omogućeno da se cijela aplikacija kasnije analizira za proizvoljan
povijesni ili budući datum, mijenjanjem samo jednog mjesta.

Ako aplikacija dobije UI opciju "datum analize", treba pozvati
set_reference_datetime() s tim datumom; dok god nije postavljen, servis
vraća stvarni tekući datum/vrijeme (UTC).
"""

from datetime import datetime, timezone
from typing import Optional


class AnalysisDateService:
    def __init__(self):
        self._override: Optional[datetime] = None

    def set_reference_datetime(self, dt: Optional[datetime]) -> None:
        """Postavlja fiksni 'datum analize'. None poništava override (natrag na tekući datum/vrijeme)."""
        if dt is not None and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        self._override = dt

    def get_reference_datetime(self) -> datetime:
        """Vraća referentni datum/vrijeme (UTC-aware) koji treba koristiti za analizu."""
        if self._override is not None:
            return self._override
        return datetime.now(timezone.utc)


# Jedina instanca koju cijela aplikacija dijeli.
analysis_date_service = AnalysisDateService()
