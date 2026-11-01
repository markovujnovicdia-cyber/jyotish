"""
Čista (bez Streamlit ovisnosti) logika koja odlučuje koja godina Varshaphale
treba biti prikazana u tabu "Varshaphala" - izdvojeno iz
ui/pages_chart.py:_render_varshaphala radi testabilnosti bez pokretanja
Streamlit aplikacije.

Pravilo: aktivna Varshaphala (prema solarnom povratku, core.varshaphala.
find_active_varshaphala_year) se auto-selektira SAMO pri prvom otvaranju,
nakon promjene osobe, ili nakon klika na "Trenutačna Varshaphala". U svim
drugim slučajevima zadržava se ručno odabrana godina korisnika.
"""

from typing import Optional


def resolve_varsha_target_year(
    *,
    previous_person_key: Optional[str],
    current_person_key: str,
    previous_target_year: Optional[int],
    active_year: int,
    current_button_clicked: bool,
) -> int:
    """
    previous_person_key: session_state vrijednost iz prethodnog renderiranja
        (None ako je ovo prvo ikad otvaranje).
    current_person_key: identifikator trenutačno odabrane osobe.
    previous_target_year: prethodno odabrana godina u session_state (None
        ako još nikad nije postavljena).
    active_year: godina koju vraća core.varshaphala.find_active_varshaphala_year
        za trenutačnu osobu i referentni datum.
    current_button_clicked: True ako je korisnik upravo kliknuo "Trenutačna
        Varshaphala" u ovom renderiranju.
    """
    person_changed = previous_person_key != current_person_key
    first_open = previous_target_year is None

    if person_changed or current_button_clicked or first_open:
        return active_year
    return previous_target_year
