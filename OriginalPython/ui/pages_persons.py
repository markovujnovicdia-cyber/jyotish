"""
Streamlit stranica: unos i pregled osoba.
"""

from datetime import date, datetime

import streamlit as st

from core.geocoding import geocode_city
from core.time_utils import find_timezone
from db import database
from db.models import Person


def render():
    st.header("Osobe")

    tab_new, tab_list = st.tabs(["Nova osoba", "Popis osoba"])

    with tab_new:
        _render_new_person_form()

    with tab_list:
        _render_person_list()


def _render_new_person_form():
    st.subheader("Dodaj novu osobu")

    name = st.text_input("Ime i prezime")
    col1, col2 = st.columns(2)
    with col1:
        birth_date = st.date_input(
            "Datum rođenja",
            value=date(1990, 1, 1),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
        )
    with col2:
        birth_time = st.time_input("Vrijeme rođenja", step=300)

    col3, col4 = st.columns(2)
    with col3:
        city = st.text_input("Grad rođenja")
    with col4:
        country = st.text_input("Država (opcionalno, preporučeno)")

    # Geokodiranje se pokreće ručno, prije spremanja, da korisnik može
    # provjeriti je li pronađen ispravan grad.
    if "geo_result" not in st.session_state:
        st.session_state.geo_result = None
        st.session_state.geo_tz = None

    if st.button("Pronađi koordinate grada"):
        if not city:
            st.warning("Unesi naziv grada prije pretrage koordinata.")
        else:
            try:
                geo = geocode_city(city, country)
                tz_name = find_timezone(geo.latitude, geo.longitude)
                st.session_state.geo_result = geo
                st.session_state.geo_tz = tz_name
            except ValueError as e:
                st.error(str(e))
                st.session_state.geo_result = None

    geo = st.session_state.geo_result
    if geo:
        st.success(
            f"Pronađeno: {geo.display_name}\n\n"
            f"Koordinate: {geo.latitude:.4f}, {geo.longitude:.4f}\n\n"
            f"Vremenska zona: {st.session_state.geo_tz}"
        )

    time_confirmed = st.checkbox(
        "Potvrđujem da je ovo vrijeme rođenja sigurno i točno "
        "(npr. iz rodnog lista, ne procjena)."
    )

    if st.button("Spremi osobu", type="primary"):
        if not name:
            st.warning("Unesi ime osobe.")
        elif not geo:
            st.warning("Prvo pronađi koordinate grada.")
        elif not time_confirmed:
            st.warning(
                "Aplikacija prihvaća samo potvrđeno/sigurno vrijeme rođenja. "
                "Označi potvrdu prije spremanja."
            )
        else:
            person = Person(
                id=None,
                name=name,
                birth_date=birth_date.strftime("%Y-%m-%d"),
                birth_time=birth_time.strftime("%H:%M:%S"),
                birth_place=city,
                country=country,
                latitude=geo.latitude,
                longitude=geo.longitude,
                timezone=st.session_state.geo_tz,
                time_confirmed=True,
            )
            new_id = database.save_person(person)
            st.success(f"Osoba '{name}' spremljena (ID {new_id}).")
            st.session_state.geo_result = None
            st.session_state.geo_tz = None


def _render_person_list():
    st.subheader("Spremljene osobe")
    persons = database.list_persons()
    if not persons:
        st.info("Još nema spremljenih osoba.")
        return

    for p in persons:
        with st.expander(f"{p.name} ({p.birth_date})"):
            st.write(f"Vrijeme rođenja: {p.birth_time}")
            st.write(f"Mjesto: {p.birth_place}, {p.country}")
            st.write(f"Koordinate: {p.latitude:.4f}, {p.longitude:.4f}")
            st.write(f"Vremenska zona: {p.timezone}")
            st.write(f"Vrijeme potvrđeno: {'Da' if p.time_confirmed else 'Ne'}")

            col_edit, col_delete = st.columns(2)
            edit_key = f"editing_{p.id}"
            if col_edit.button("Uredi", key=f"edit_btn_{p.id}", use_container_width=True):
                st.session_state[edit_key] = True
            if col_delete.button("Obriši", key=f"delete_btn_{p.id}", use_container_width=True):
                st.session_state[f"confirm_delete_{p.id}"] = True

            if st.session_state.get(f"confirm_delete_{p.id}"):
                st.warning(f"Sigurno obrisati '{p.name}'? Ovo se ne može poništiti.")
                col_yes, col_no = st.columns(2)
                if col_yes.button("Da, obriši", key=f"confirm_yes_{p.id}", use_container_width=True):
                    database.delete_person(p.id)
                    st.session_state[f"confirm_delete_{p.id}"] = False
                    st.rerun()
                if col_no.button("Odustani", key=f"confirm_no_{p.id}", use_container_width=True):
                    st.session_state[f"confirm_delete_{p.id}"] = False
                    st.rerun()

            if st.session_state.get(edit_key):
                _render_edit_person_form(p)


def _render_edit_person_form(p):
    st.markdown("---")
    st.markdown("**Uredi podatke**")

    name = st.text_input("Ime i prezime", value=p.name, key=f"edit_name_{p.id}")
    col1, col2 = st.columns(2)
    with col1:
        birth_date = st.date_input(
            "Datum rođenja",
            value=date.fromisoformat(p.birth_date),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            key=f"edit_date_{p.id}",
        )
    with col2:
        birth_time = st.time_input(
            "Vrijeme rođenja",
            value=datetime.strptime(p.birth_time, "%H:%M:%S").time(),
            step=300,
            key=f"edit_time_{p.id}",
        )

    col3, col4 = st.columns(2)
    with col3:
        city = st.text_input("Grad rođenja", value=p.birth_place, key=f"edit_city_{p.id}")
    with col4:
        country = st.text_input("Država", value=p.country, key=f"edit_country_{p.id}")

    geo_key = f"edit_geo_{p.id}"
    tz_key = f"edit_tz_{p.id}"
    if geo_key not in st.session_state:
        st.session_state[geo_key] = None
        st.session_state[tz_key] = p.timezone

    if st.button("Ponovno pronađi koordinate (ako si promijenio/la grad)", key=f"edit_geo_btn_{p.id}"):
        if not city:
            st.warning("Unesi naziv grada.")
        else:
            try:
                geo = geocode_city(city, country)
                tz_name = find_timezone(geo.latitude, geo.longitude)
                st.session_state[geo_key] = geo
                st.session_state[tz_key] = tz_name
            except ValueError as e:
                st.error(str(e))

    geo = st.session_state[geo_key]
    if geo:
        st.success(
            f"Pronađeno: {geo.display_name}\n\n"
            f"Koordinate: {geo.latitude:.4f}, {geo.longitude:.4f}\n\n"
            f"Vremenska zona: {st.session_state[tz_key]}"
        )
        latitude, longitude, timezone_val = geo.latitude, geo.longitude, st.session_state[tz_key]
    else:
        # zadrži postojeće koordinate/vremensku zonu ako grad nije ponovno tražen
        latitude, longitude, timezone_val = p.latitude, p.longitude, p.timezone

    col_save, col_cancel = st.columns(2)
    if col_save.button("Spremi promjene", key=f"save_edit_{p.id}", type="primary", use_container_width=True):
        if not name:
            st.warning("Unesi ime osobe.")
        else:
            updated = Person(
                id=p.id,
                name=name,
                birth_date=birth_date.strftime("%Y-%m-%d"),
                birth_time=birth_time.strftime("%H:%M:%S"),
                birth_place=city,
                country=country,
                latitude=latitude,
                longitude=longitude,
                timezone=timezone_val,
                time_confirmed=p.time_confirmed,
            )
            database.update_person(updated)
            st.session_state[f"editing_{p.id}"] = False
            st.session_state[geo_key] = None
            st.success("Podaci ažurirani.")
            st.rerun()
    if col_cancel.button("Odustani", key=f"cancel_edit_{p.id}", use_container_width=True):
        st.session_state[f"editing_{p.id}"] = False
        st.session_state[geo_key] = None
        st.rerun()
