"""
Streamlit stranica: natalna karta, dasha, tranziti, Varshaphala.
"""

import calendar
from datetime import date, datetime, timezone, timedelta
from zoneinfo import ZoneInfo

import streamlit as st
from ui.colors import colored_dataframe

from core.sahams import compute_sahams, SAHAM_INFO, is_daytime
from core.nakshatra import get_nakshatra
from core.houses import whole_sign_house, ascendant_sign_index, bhava_chalit_house
from core.ashtakavarga import (
    compute_bhinnashtakavarga, compute_sarvashtakavarga, ASHTAKAVARGA_PLANETS,
    get_kakshya_lord, is_kakshya_activated,
)
from core.yoga_engine.context import ChartContext
from core.varga import d9_navamsha_sign_index, d7_saptamsha_sign_index, d10_dashamsha_sign_index, d12_dvadashamsha_sign_index
from core.dasha import get_current_dasha_snapshot, get_current_dasha_5_levels
from core.transits import compute_transits
from core.time_utils import utc_to_julian_day
from core.varshaphala import (
    compute_varshaphala, find_solar_return_jd, find_active_varshaphala_year,
    get_varshaphala_period_info,
)
from core.analysis_date import analysis_date_service
from core.masa_pravesha import compute_masa_pravesha_sequence
from core.planet_strength import compute_planet_strength
from core.argala import compute_argala, count_active_argala
from core.tajika import (
    TAJIKA_PLANETS, compute_saham_punya, compute_saham_vidya, compute_saham_yasha,
    compute_saham_vivaha, compute_saham_putra,
)
from core.karyesha_yogas import (
    analyze_karyesha_yogas, compute_ishkavala, compute_induvara, compute_khallasara,
)
from core.constants import RASHI, PLANET_ORDER, NAKSHATRA_ABBR, PLANET_ABBR, RASHI_LORD
from core.panchang import get_tithi
from core.combustion import check_combustion
from core.aspects import compute_graha_drishti, ASPECTING_PLANETS, ASPECT_STRENGTH_LABEL, is_special_full_aspect
from core.natal import get_natal_context
from db import database
from ui.pages_yogas import render_yogas_tab
from ui.north_indian_chart import render_north_indian_svg, group_planets_by_house
from ui.transit_wheel import render_transit_wheel_svg, ORB_DEGREES, angular_distance
from ui.varsha_navigation import resolve_varsha_target_year
from ui.chart_labels import format_planet_label, format_point_label
from ui.df_utils import full_table_height
from ui.person_picker import select_person


def render(section="D1"):

    persons = database.list_persons()
    if not persons:
        st.info("Prvo dodaj barem jednu osobu na stranici 'Osobe'.")
        return

    person = select_person(persons)

    ctx = get_natal_context(person)
    utc_dt, asc_lon, positions = ctx.utc_dt, ctx.ascendant_longitude, ctx.positions
    asc_sign_idx = ctx.ascendant_sign_index
    special_points = ctx.special_points


    if section == "D1":
        _render_d1(person, asc_lon, asc_sign_idx, positions, special_points)
    elif section == "Varge":
        _render_vargas(positions, asc_lon, special_points)
    elif section == "Daše":
        _render_dasha(positions, utc_dt)
    elif section == "Tranziti":
        _render_transits(asc_lon, positions, special_points, utc_dt, person, ctx.jd_ut)
    elif section == "Sahame":
        _render_sahams(person, ctx)
    elif section in ("Varshaphala", "Masa Pravesha", "Tajika"):
        _render_varshaphala(person, positions, asc_lon, utc_dt, section)
    elif section == "Yoge":
        render_yogas_tab(ChartContext(ascendant_longitude=asc_lon, ascendant_sign_index=asc_sign_idx, positions=positions, special_points=special_points))
    else:
        st.info("Odaberite prikaz iz izbornika.")


def _build_house_data(asc_sign_idx, positions, label_house_map, exclude_from_argala=("AL",)):
    """
    Gradi house_data strukturu (planeti po kući, snaga, protok) - koristi se
    za prikaz uz dijamant kartu.

    label_house_map: {oznaka: broj_kuce} - može uključivati planete i
    posebne točke (AL/BP/GK/Lagna-nakshatra oznaku)
    """
    grouped_labels: dict = {}
    for label, house in label_house_map.items():
        grouped_labels.setdefault(house, []).append(label)

    # broj STVARNIH planeta po kući (bez AL/BP/GK/nakshatra-oznaka) - za Argalu
    real_planet_count_by_house: dict = {}
    for name in PLANET_ORDER:
        house = whole_sign_house(positions[name].sign_index, asc_sign_idx)
        real_planet_count_by_house[house] = real_planet_count_by_house.get(house, 0) + 1

    # snaga svakog planeta (za određivanje snage kuće preko vladara)
    planet_strengths = {}
    for name in PLANET_ORDER:
        pos = positions[name]
        house = whole_sign_house(pos.sign_index, asc_sign_idx)
        planet_strengths[name] = compute_planet_strength(name, pos.longitude, pos.sign_index, house)

    house_data = {}
    for house_num in range(1, 13):
        sign_index = (asc_sign_idx + house_num - 1) % 12
        sign_lord = RASHI_LORD[RASHI[sign_index]]
        lord_strength = planet_strengths.get(sign_lord)
        occupant_count = real_planet_count_by_house.get(house_num, 0)
        strength_score = (lord_strength.total_score if lord_strength else 50.0) + occupant_count * 5.0

        argala_count = count_active_argala(house_num, real_planet_count_by_house)

        house_data[house_num] = {
            "sign_index": sign_index,
            "planet_lines": grouped_labels.get(house_num, []),
            "strength": min(strength_score, 100.0),
            "argala_active": argala_count,
        }

    return house_data


def _render_d1(person, asc_lon, asc_sign_idx, positions, special_points):
    view = st.radio("D1 prikaz", ["Karta", "Položaji", "Detalji"], horizontal=True, label_visibility="collapsed")
    asc_nak = get_nakshatra(asc_lon)
    al_sign_idx = special_points["AL_sign_index"]
    al_house = whole_sign_house(al_sign_idx, asc_sign_idx)
    ul_sign_idx = special_points["UL_sign_index"]
    ul_house = whole_sign_house(ul_sign_idx, asc_sign_idx)
    a7_sign_idx = special_points["A7_sign_index"]
    a7_house = whole_sign_house(a7_sign_idx, asc_sign_idx)
    bp_lon = special_points["BP_longitude"]
    bp_house = whole_sign_house(int(bp_lon // 30), asc_sign_idx)
    if view == "Karta":
        asc_nak = get_nakshatra(asc_lon)
        st.markdown(
            f"Ascendent (Lagna): {RASHI[asc_sign_idx]} ({asc_lon % 30:.2f}°), "
            f"{asc_nak.name} pada {asc_nak.pada}"
        )
    
        label_house_map = {}
        label_house_map[f"({NAKSHATRA_ABBR[asc_nak.index]}-{asc_nak.pada})"] = 1
        for name in PLANET_ORDER:
            pos = positions[name]
            house = whole_sign_house(pos.sign_index, asc_sign_idx)
            label = format_planet_label(name, pos.longitude, pos.is_retrograde and name not in ("Rahu", "Ketu"))
            label_house_map[label] = house
    
        al_sign_idx = special_points["AL_sign_index"]
        al_house = whole_sign_house(al_sign_idx, asc_sign_idx)
        label_house_map["AL"] = al_house
    
        ul_sign_idx = special_points["UL_sign_index"]
        ul_house = whole_sign_house(ul_sign_idx, asc_sign_idx)
        label_house_map["UL"] = ul_house
    
        a7_sign_idx = special_points["A7_sign_index"]
        a7_house = whole_sign_house(a7_sign_idx, asc_sign_idx)
        label_house_map["A7"] = a7_house
    
        bp_lon = special_points["BP_longitude"]
        bp_house = whole_sign_house(int(bp_lon // 30), asc_sign_idx)
        label_house_map[format_point_label("BP", bp_lon)] = bp_house
    
        if special_points["GK_longitude"] is not None:
            gk_lon = special_points["GK_longitude"]
            gk_house = whole_sign_house(int(gk_lon // 30), asc_sign_idx)
            label_house_map[format_point_label("GK", gk_lon)] = gk_house
    
        if special_points.get("MANDI_longitude") is not None:
            mandi_lon = special_points["MANDI_longitude"]
            mandi_house = whole_sign_house(int(mandi_lon // 30), asc_sign_idx)
            label_house_map[format_point_label("Md", mandi_lon)] = mandi_house
    
        st.subheader("Sjevernoindijski dijamant prikaz")
        house_data = _build_house_data(asc_sign_idx, positions, label_house_map)
        grouped = group_planets_by_house(label_house_map)
        extra_info = {
            h: f"S:{house_data[h]['strength']:.0f} P:{house_data[h]['argala_active']}/4"
            for h in house_data
        }
        svg = render_north_indian_svg(asc_sign_idx, grouped, title=person.name, house_extra_info=extra_info)
        st.components.v1.html(f'<div style="height:445px;display:flex;justify-content:center">{svg}</div><style>svg {{max-height:440px;width:auto;max-width:100%;}}</style>', height=455)
        st.caption("AL · UL · A7 · BP · GK · Md | S = snaga kuće · P = aktivni izvori argale")
    elif view == "Položaji":
        rows = []
        rows.append({
            "Planet": "Lagna (Ascendent)",
            "Znak": RASHI[asc_sign_idx],
            "Stupanj u znaku": f"{asc_lon % 30:.2f}°",
            "Kuća": 1,
            "Nakshatra": asc_nak.name,
            "Pada": asc_nak.pada,
            "Retrogradan": "-",
            "Kombust": "-",
        })
        for name in PLANET_ORDER:
            pos = positions[name]
            house = whole_sign_house(pos.sign_index, asc_sign_idx)
            nak = get_nakshatra(pos.longitude)
            strength = compute_planet_strength(name, pos.longitude, pos.sign_index, house)
            combustion = check_combustion(name, pos.longitude, positions["Sunce"].longitude, pos.is_retrograde)
            combust_text = "-" if combustion is None else ("Da" if combustion.is_combust else "Ne")
            rows.append({
                "Planet": name,
                "Znak": pos.sign,
                "Stupanj u znaku": f"{pos.degree_in_sign:.2f}°",
                "Kuća": house,
                "Nakshatra": nak.name,
                "Pada": nak.pada,
                "Retrogradan": "Da" if pos.is_retrograde else "Ne",
                "Kombust": combust_text,
                "Snaga": f"{strength.total_score:.0f} ({strength.dignity})",
            })
    
        rows.append({
            "Planet": "AL (Arudha Lagna)",
            "Znak": RASHI[al_sign_idx],
            "Stupanj u znaku": "-",
            "Kuća": al_house,
            "Nakshatra": "-",
            "Pada": "-",
            "Retrogradan": "-",
            "Kombust": "-",
            "Snaga": "-",
        })
        rows.append({
            "Planet": "UL (Upapada Lagna)",
            "Znak": RASHI[ul_sign_idx],
            "Stupanj u znaku": "-",
            "Kuća": ul_house,
            "Nakshatra": "-",
            "Pada": "-",
            "Retrogradan": "-",
            "Kombust": "-",
            "Snaga": "-",
        })
        rows.append({
            "Planet": "A7 (Darapada)",
            "Znak": RASHI[a7_sign_idx],
            "Stupanj u znaku": "-",
            "Kuća": a7_house,
            "Nakshatra": "-",
            "Pada": "-",
            "Retrogradan": "-",
            "Kombust": "-",
            "Snaga": "-",
        })
        bp_nak = get_nakshatra(bp_lon)
        rows.append({
            "Planet": "BP (Bhrigu Bindu)",
            "Znak": RASHI[int(bp_lon // 30)],
            "Stupanj u znaku": f"{bp_lon % 30:.2f}°",
            "Kuća": bp_house,
            "Nakshatra": bp_nak.name,
            "Pada": bp_nak.pada,
            "Retrogradan": "-",
            "Kombust": "-",
            "Snaga": "-",
        })
        if special_points["GK_longitude"] is not None:
            gk_lon = special_points["GK_longitude"]
            gk_nak = get_nakshatra(gk_lon)
            rows.append({
                "Planet": "GK (Gulika, proporcionalna metoda)",
                "Znak": RASHI[int(gk_lon // 30)],
                "Stupanj u znaku": f"{gk_lon % 30:.2f}°",
                "Kuća": whole_sign_house(int(gk_lon // 30), asc_sign_idx),
                "Nakshatra": gk_nak.name,
                "Pada": gk_nak.pada,
                "Retrogradan": "-",
                "Kombust": "-",
                "Snaga": "-",
            })
        if special_points.get("MANDI_longitude") is not None:
            mandi_lon = special_points["MANDI_longitude"]
            mandi_nak = get_nakshatra(mandi_lon)
            rows.append({
                "Planet": f"Mandi (fiksna ghatika metoda, {special_points['MANDI_ghatikas']:.0f} ghatija)",
                "Znak": RASHI[int(mandi_lon // 30)],
                "Stupanj u znaku": f"{mandi_lon % 30:.2f}°",
                "Kuća": whole_sign_house(int(mandi_lon // 30), asc_sign_idx),
                "Nakshatra": mandi_nak.name,
                "Pada": mandi_nak.pada,
                "Retrogradan": "-",
                "Kombust": "-",
                "Snaga": "-",
            })
    
        colored_dataframe(rows, use_container_width=True, hide_index=True, height=min(full_table_height(rows), 490))
    
    else:
        label_house_map = {format_planet_label(n, positions[n].longitude, positions[n].is_retrograde): whole_sign_house(positions[n].sign_index, asc_sign_idx) for n in PLANET_ORDER}
        house_data = _build_house_data(asc_sign_idx, positions, label_house_map)
        with st.expander("Snaga i protok po kućama"):
            house_rows = []
            for house_num in range(1, 13):
                hd = house_data[house_num]
                argala_detail = compute_argala(house_num, {h: len(house_data[h]["planet_lines"]) for h in house_data})
                active_sources = ", ".join(f"{a.argala_house}." for a in argala_detail if a.active) or "-"
                house_rows.append({
                    "Kuća": house_num,
                    "Znak": RASHI[hd["sign_index"]],
                    "Snaga": f"{hd['strength']:.0f}",
                    "Aktivan protok (kuće)": active_sources,
                    "Broj aktivnih (od 4)": hd["argala_active"],
                })
            colored_dataframe(house_rows, use_container_width=True, hide_index=True, height=full_table_height(house_rows))
    
        with st.expander("Bhava Chalit (usporedba s Whole Sign)"):
            st.caption(
                "Bhava Chalit koristi točan stupanj ascendenta kao sredinu 1. kuće (ne njen "
                "početak), pa se planeti blizu granice kuće ponekad prebace u susjednu kuću. "
                "Retci gdje se kuća razlikuje su istaknuti u tekstu."
            )
            chalit_rows = []
            for name in PLANET_ORDER:
                pos = positions[name]
                ws_house = whole_sign_house(pos.sign_index, asc_sign_idx)
                chalit_house = bhava_chalit_house(pos.longitude, asc_lon)
                chalit_rows.append({
                    "Planet": name,
                    "Whole Sign kuća": ws_house,
                    "Bhava Chalit kuća": chalit_house,
                    "Razlika": "DA" if ws_house != chalit_house else "-",
                })
            colored_dataframe(chalit_rows, use_container_width=True, hide_index=True, height=full_table_height(chalit_rows))
    
        st.subheader("Aspekti na Lagnu (Graha Drishti)")
        lagna_aspecting_planets = ASPECTING_PLANETS + ["Rahu", "Ketu"]
        lagna_planet_sign_index = {name: positions[name].sign_index for name in lagna_aspecting_planets}
        lagna_relations = compute_graha_drishti(
            lagna_planet_sign_index, {"Lagna": asc_sign_idx}, include_rahu_ketu=True
        )
        lagna_rel_by_planet = {r.from_planet: r for r in lagna_relations}
        lagna_rows = []
        for name in lagna_aspecting_planets:
            rel = lagna_rel_by_planet.get(name)
            distance = (asc_sign_idx - positions[name].sign_index) % 12 + 1
            lagna_rows.append({
                "Planet": name,
                "Aspektira Lagnu": "Da" if rel else "Ne",
                "Udaljenost (kuća od planeta)": distance,
                "Snaga": ASPECT_STRENGTH_LABEL[rel.strength] if rel else "-",
            })
        colored_dataframe(lagna_rows, use_container_width=True, hide_index=True, height=full_table_height(lagna_rows))
        st.caption(
            "Graha Drishti (klasična Parashari metoda, BPHS) - koji planeti aspektiraju Lagnu "
            "(1. kuću) i kojom snagom. Rahu/Ketu tretirani KAO SATURN (puni aspekt 3./7./10.) "
            "- ovo je česta, ali NAKNADNA/sporna konvencija (BPHS izvorno ne definira njihove "
            "aspekte), uključena na izričit zahtjev (vidi core/aspects.py)."
        )


def _render_ashtakavarga_compact(asc_sign_idx, natal_positions, transit_rows):
    """
    Kompaktan prikaz uz kotač tranzita: Ashtakavarga tablica se gradi iz
    NATALNIH pozicija (fiksno, kako i treba klasično), a čita se za
    ZNAK u kojem je tranzitni planet TRENUTNO - standardna metoda za
    procjenu snage tranzita. Uz to i Kakshya (vladar pod-podjele znaka,
    3°45') za precizniji, uži vremenski prozor.
    """
    st.markdown("**Ashtakavarga + Kakshya (tranziti)**")
    sign_index_by_source = {name: natal_positions[name].sign_index for name in ASHTAKAVARGA_PLANETS}
    sign_index_by_source["Lagna"] = asc_sign_idx
    sarva = compute_sarvashtakavarga(sign_index_by_source)

    for planet in ASHTAKAVARGA_PLANETS:
        pos = transit_rows[planet]
        planet_sign_index = int(pos.longitude // 30) % 12
        bhinna = compute_bhinnashtakavarga(planet, sign_index_by_source)
        own_bav = bhinna[planet_sign_index]
        sav = sarva[planet_sign_index]
        kakshya_lord = get_kakshya_lord(pos.degree_in_sign)
        activated = is_kakshya_activated(planet, planet_sign_index, kakshya_lord, sign_index_by_source)
        abbr = PLANET_ABBR.get(planet, planet[:2])
        mark = " ●" if activated else ""
        st.caption(f"{abbr}: SAV {sav} · BAV {own_bav} · Kakshya {kakshya_lord}{mark}")
    st.caption("● = Kakshya vladar je dao bod ovom znaku - uži, aktivniji prozor")


_VARGA_INFO = {
    "D9": {
        "naziv": "Navamsha",
        "opis": "Brak, partnerstva, unutarnja snaga i dharma.",
        "func": d9_navamsha_sign_index,
        "todo": False,
    },
    "D7": {
        "naziv": "Saptamsha",
        "opis": "Djeca i potomstvo.",
        "func": d7_saptamsha_sign_index,
        "todo": False,
    },
    "D10": {
        "naziv": "Dashamsha",
        "opis": "Karijera, javni život i profesionalni uspjeh.",
        "func": d10_dashamsha_sign_index,
        "todo": False,
    },
    "D12": {
        "naziv": "Dvadashamsha",
        "opis": "Roditelji i obiteljsko podrijetlo.",
        "func": d12_dvadashamsha_sign_index,
        "todo": False,
    },
}


def _render_vargas(positions, asc_lon, special_points):
    st.caption(
        "D1, D9, D7, D10 i D12 su izračunate po klasičnim pravilima (Brihat "
        "Parashara Hora Shastra) i formule su potvrđene protiv referentne "
        "literature. BP (Bhrigu Bindu), GK (Gulika) i Md (Mandi) su preslikani u svaku "
        "vargu po istom pravilu kao planeti. AL (Arudha Lagna) se NE "
        "prikazuje u vargama jer je po definiciji samo znak (bez točnog "
        "stupnja), pa se ne može ispravno preslikati u divizijsku kartu."
    )

    bp_lon = special_points["BP_longitude"]
    gk_lon = special_points["GK_longitude"]
    mandi_lon = special_points.get("MANDI_longitude")

    selected_varga = st.radio("Varga", list(_VARGA_INFO), horizontal=True)
    for code, info in _VARGA_INFO.items():
        if code != selected_varga:
            continue
        varga_func = info["func"]
        asc_varga_idx = varga_func(asc_lon)

        label_house_map = {}
        for name in PLANET_ORDER:
            pos = positions[name]
            planet_varga_idx = varga_func(pos.longitude)
            label = format_planet_label(name, pos.longitude, pos.is_retrograde and name not in ("Rahu", "Ketu"))
            label_house_map[label] = whole_sign_house(planet_varga_idx, asc_varga_idx)

        bp_varga_idx = varga_func(bp_lon)
        label_house_map[format_point_label("BP", bp_lon)] = whole_sign_house(bp_varga_idx, asc_varga_idx)

        if gk_lon is not None:
            gk_varga_idx = varga_func(gk_lon)
            label_house_map[format_point_label("GK", gk_lon)] = whole_sign_house(gk_varga_idx, asc_varga_idx)

        if mandi_lon is not None:
            mandi_varga_idx = varga_func(mandi_lon)
            label_house_map[format_point_label("Md", mandi_lon)] = whole_sign_house(mandi_varga_idx, asc_varga_idx)

        grouped = group_planets_by_house(label_house_map)
        title = f"{code} - {info['naziv']}"
        svg = render_north_indian_svg(asc_varga_idx, grouped, title=title)

        st.markdown(f"**{code} — {info['naziv']}**  \n_{info['opis']}_")
        st.components.v1.html(f'<div style="height:445px;display:flex;justify-content:center">{svg}</div><style>svg {{max-height:440px;width:auto;max-width:100%;}}</style>', height=455)
        st.markdown("---")


def _render_dasha(positions, utc_dt):
    moon_lon = positions["Mjesec"].longitude
    d = st.date_input("Datum daše", value=date.today())
    at_dt = datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=12)
    try:
        current = get_current_dasha_5_levels(moon_lon, utc_dt, at_dt)
    except ValueError as exc:
        st.warning(str(exc))
        return
    level_names = ["Maha", "Antar", "Pratyantar", "Sookshma", "Prana"]
    st.caption("Natalna Vimshottari · natalni Mjesec · godina = 365,2425 dana · odabrani datum u 12:00 UTC")
    st.caption("Prva mahadaša može početi prije rođenja; podrazdoblja se računaju iz njezina punog trajanja.")
    st.markdown("**Aktivna daša:** " + " → ".join(p.lord for p in current))
    level = st.radio("Razina", level_names, horizontal=True)
    from core.dasha import get_mahadasha_sequence, get_sub_periods
    sequence = get_mahadasha_sequence(moon_lon, utc_dt)
    label = lambda p: f"{p.lord} · {p.start:%d.%m.%Y.} – {p.end:%d.%m.%Y.}"
    for i in range(level_names.index(level)):
        default = next((j for j,p in enumerate(sequence) if p.start <= at_dt < p.end),0)
        chosen = st.selectbox(level_names[i], sequence, index=default, format_func=label, key=f"dasha_parent_{i}")
        sequence = get_sub_periods(chosen.lord, chosen.start, chosen.end)
    table = [{"Vladar":p.lord,"Početak UTC":p.start.strftime("%d.%m.%Y. %H:%M"),"Kraj UTC":p.end.strftime("%d.%m.%Y. %H:%M")} for p in sequence]
    colored_dataframe(table, hide_index=True, use_container_width=True, height=min(full_table_height(table),400))


def _render_transits(natal_asc_lon, natal_positions, special_points, birth_dt_utc, person, natal_jd):
    if "transit_date" not in st.session_state:
        st.session_state.transit_date = datetime.now(ZoneInfo("Europe/Zagreb")).date()
    if "transit_time" not in st.session_state:
        st.session_state.transit_time = datetime.now(ZoneInfo("Europe/Zagreb")).time().replace(microsecond=0)

    def _shift_month(d, delta):
        month_index = d.month - 1 + delta  # 0-11 prosireno izvan raspona radi lakseg preljeva
        year = d.year + month_index // 12
        month = month_index % 12 + 1
        last_day = calendar.monthrange(year, month)[1]
        day = min(d.day, last_day)  # npr. 31.1. + 1 mjesec -> 28./29.2.
        return d.replace(year=year, month=month, day=day)

    def _shift_year(d, delta):
        try:
            return d.replace(year=d.year + delta)
        except ValueError:
            return d.replace(year=d.year + delta, day=28)  # 29. veljače edge slučaj

    view = st.radio("Tranzitni prikaz", ["Kotač", "Položaji tranzita", "Natalne točke"], horizontal=True, label_visibility="collapsed")
    st.session_state.transit_picker = st.session_state.transit_date
    def _date_changed():
        st.session_state.transit_date = st.session_state.transit_picker
    st.sidebar.date_input("Datum tranzita", key="transit_picker", on_change=_date_changed)
    st.session_state.transit_time_picker = st.session_state.transit_time.replace(second=0)
    st.session_state.transit_second_picker = st.session_state.transit_time.second
    def _time_changed():
        st.session_state.transit_time = st.session_state.transit_time_picker.replace(
            second=int(st.session_state.transit_second_picker)
        )
    st.sidebar.time_input("Vrijeme tranzita (Europe/Zagreb)", key="transit_time_picker", step=timedelta(minutes=1), on_change=_time_changed)
    st.sidebar.number_input("Sekunde", min_value=0, max_value=59, step=1, key="transit_second_picker", on_change=_time_changed)
    point_mode = st.sidebar.radio("Točke na kotaču", ["Planeti", "Planeti i sahame", "Sve točke"], index=1)
    transit_date = st.session_state.transit_date

    transit_local = datetime.combine(transit_date, st.session_state.transit_time, tzinfo=ZoneInfo("Europe/Zagreb"))
    at_dt = transit_local.astimezone(timezone.utc)
    jd_transit = utc_to_julian_day(at_dt)
    natal_moon_lon = natal_positions["Mjesec"].longitude

    rows = compute_transits(jd_transit, natal_asc_lon, natal_moon_lon)

    col_wheel, col_dasha = st.columns([3, 2])

    with col_wheel:
        st.subheader("Kotač tranzita")
        st.caption("Natalni položaji i NATALNE sahame unutra · tranziti izvana")
        st.caption(transit_local.strftime("%d.%m.%Y. %H:%M:%S %Z") + " · Europe/Zagreb · " + at_dt.strftime("%H:%M:%S UTC"))

        natal_labels = {}
        for name in PLANET_ORDER:
            pos = natal_positions[name]
            abbr = PLANET_ABBR.get(name, name[:2])
            if pos.is_retrograde and name not in ("Rahu", "Ketu"):
                abbr += "R"
            natal_labels[abbr] = pos.longitude

        al_sign_idx = special_points["AL_sign_index"]
        natal_labels["AL"] = al_sign_idx * 30 + 15  # AL nema točan stupanj; postavljamo ga na sredinu znaka radi prikaza
        natal_labels["BP"] = special_points["BP_longitude"]
        if special_points["GK_longitude"] is not None:
            natal_labels["GK"] = special_points["GK_longitude"]
        if special_points.get("MANDI_longitude") is not None:
            natal_labels["Md"] = special_points["MANDI_longitude"]

        saham_values = compute_sahams(natal_asc_lon, natal_positions, is_daytime(natal_jd, person.latitude, person.longitude))
        selected_sahams = st.sidebar.multiselect("Sahame na kotaču", list(SAHAM_INFO), default=["Punya", "Vivaha", "Preeti"], key="wheel_sahams")
        for name in selected_sahams:
            natal_labels[SAHAM_INFO[name][0]] = saham_values[name]

        transit_labels = {}
        name_to_transit_abbr = {}
        for name in PLANET_ORDER:
            r = rows[name]
            abbr = PLANET_ABBR.get(name, name[:2])
            if r.is_retrograde and name not in ("Rahu", "Ketu"):
                abbr += "R"
            transit_labels[abbr] = r.longitude
            name_to_transit_abbr[name] = abbr

        # Koliko toga svaka točka "dodiruje" - konjunkcija (unutar ORB_DEGREES)
        # ILI POSEBAN puni Graha Drishti aspekt (Mars 4./8., Jupiter 5./9.,
        # Saturn 3./10. - core.aspects.is_special_full_aspect) od TRANZITNOG
        # planeta na NATALNU točku (Gochara princip). NAMJERNO isključen
        # UNIVERZALNI 7. aspekt (svih 7 klasičnih grahe uvijek pogađa TOČNO
        # jedan znak nasuprot sebi) - budući da 7+3 planeta gotovo uvijek
        # zajedno pokrivaju gotovo CIJELI zodijak nekim punim aspektom u
        # bilo kojem trenutku, taj bi kriterij označio ~3/4 svih točaka kao
        # "istaknuto" i time poništio smisao isticanja (provjereno na
        # stvarnoj karti). Posebni aspekti (samo 3 planeta, po 2 dodatna
        # znaka) su rjeđi i stvarno izdvajaju trenutačno najaktivniji
        # tranzit. Broj dodira po točki (natal_hit_counts/transit_hit_counts)
        # određuje veličinu/isticanje - što više dodira, to veća točka.
        natal_touches = {}
        transit_touches = {}

        def _touch(n_label: str, t_label: str):
            natal_touches.setdefault(n_label, set()).add(t_label)
            transit_touches.setdefault(t_label, set()).add(n_label)

        for t_label, t_lon in transit_labels.items():
            for n_label, n_lon in natal_labels.items():
                if n_label == "AL":
                    continue  # AL nema pravi stupanj - nepouzdano za konjunkciju/aspekt
                if angular_distance(t_lon, n_lon) <= ORB_DEGREES:
                    _touch(n_label, t_label)

        transit_sign_index = {name: rows[name].longitude // 30 % 12 for name in PLANET_ORDER}
        transit_sign_index = {name: int(v) for name, v in transit_sign_index.items()}
        natal_sign_index_by_label = {
            label: int(lon % 360.0 // 30) for label, lon in natal_labels.items() if label != "AL"
        }
        for rel in compute_graha_drishti(transit_sign_index, natal_sign_index_by_label):
            if not is_special_full_aspect(rel.from_planet, rel.house_distance):
                continue  # samo POSEBAN (ne univerzalni 7.) puni aspekt broji se kao "aspektirano"
            t_label = name_to_transit_abbr.get(rel.from_planet)
            if t_label is None:
                continue
            _touch(rel.to_planet, t_label)

        natal_hit_counts = {label: len(s) for label, s in natal_touches.items()}
        transit_hit_counts = {label: len(s) for label, s in transit_touches.items()}

        try:
            maha, antar, pratyantar, sookshma, prana = get_current_dasha_5_levels(
                natal_moon_lon, birth_dt_utc, at_dt
            )
        except ValueError as exc:
            st.warning(str(exc))
            return
        dasha_lines = [
            PLANET_ABBR.get(p.lord, p.lord[:2]) for p in [maha, antar, pratyantar, sookshma, prana]
        ]
        center_lines = [transit_date.strftime("%d.%m.%Y."), transit_local.strftime("%H:%M:%S %Z")] + dasha_lines

        visible_labels = {k: v for k, v in natal_labels.items() if point_mode == "Sve točke" or k in {PLANET_ABBR[n] for n in PLANET_ORDER} or k.rstrip("R") in {PLANET_ABBR[n] for n in PLANET_ORDER} or (point_mode == "Planeti i sahame" and k.endswith("S"))}
        wheel_svg = render_transit_wheel_svg(
            visible_labels, transit_labels,
            natal_asc_lon, center_lines=center_lines,
            natal_hit_counts=natal_hit_counts, transit_hit_counts=transit_hit_counts,
        )
        if view == "Kotač":
            st.components.v1.html(f'<div style="height:485px;display:flex;justify-content:center">{wheel_svg}</div><style>svg {{height:480px;width:auto;max-width:100%;}}</style>', height=495)

    if view == "Kotač":
        with col_dasha:
            st.markdown("---")
            st.caption("Navigator · datum i vrijeme")
    
            col_yb, col_yf = st.columns(2)
            year_back_clicked = col_yb.button("« Godina", key="transit_year_back", use_container_width=True)
            year_fwd_clicked = col_yf.button("Godina »", key="transit_year_fwd", use_container_width=True)
            col_mb, col_mf = st.columns(2)
            month_back_clicked = col_mb.button("« Mjesec", key="transit_month_back", use_container_width=True)
            month_fwd_clicked = col_mf.button("Mjesec »", key="transit_month_fwd", use_container_width=True)
            col_db, col_df = st.columns(2)
            day_back_clicked = col_db.button("« Dan", key="transit_day_back", use_container_width=True)
            day_fwd_clicked = col_df.button("Dan »", key="transit_day_fwd", use_container_width=True)
    
            col_hb, col_hf = st.columns(2)
            hour_back_clicked = col_hb.button("« Sat", key="transit_hour_back", use_container_width=True)
            hour_fwd_clicked = col_hf.button("Sat »", key="transit_hour_fwd", use_container_width=True)
            if hour_back_clicked or hour_fwd_clicked:
                # Pomak predstavlja protekli sat, uključujući prijelaz ljetnog vremena.
                shifted = (at_dt + timedelta(hours=1 if hour_fwd_clicked else -1)).astimezone(ZoneInfo("Europe/Zagreb"))
                st.session_state.transit_date = shifted.date()
                st.session_state.transit_time = shifted.timetz().replace(tzinfo=None)
                st.rerun()

            # Napomena: gumbi izravno mijenjaju st.session_state.transit_date i
            # odmah pozivaju st.rerun() - više nema st.date_input widgeta s tim
            # key-em, pa nema ograničenja oko redoslijeda mutacije/instanciranja.
            if year_back_clicked:
                st.session_state.transit_date = _shift_year(st.session_state.transit_date, -1)
                st.rerun()
            if month_back_clicked:
                st.session_state.transit_date = _shift_month(st.session_state.transit_date, -1)
                st.rerun()
            if day_back_clicked:
                st.session_state.transit_date -= timedelta(days=1)
                st.rerun()
            if day_fwd_clicked:
                st.session_state.transit_date += timedelta(days=1)
                st.rerun()
            if month_fwd_clicked:
                st.session_state.transit_date = _shift_month(st.session_state.transit_date, 1)
                st.rerun()
            if year_fwd_clicked:
                st.session_state.transit_date = _shift_year(st.session_state.transit_date, 1)
                st.rerun()
    
            st.markdown("**Aktivni dodiri · orb 3°**")
            hits = [{"Tranzit": t, "Točka": n, "Razmak": f"{angular_distance(tl,nl):.2f}°"} for t,tl in transit_labels.items() for n,nl in visible_labels.items() if n != "AL" and angular_distance(tl,nl) <= ORB_DEGREES]
            colored_dataframe(hits, hide_index=True, use_container_width=True, height=180) if hits else st.caption("Nema konjunkcija unutar 3°.")
            with st.expander("Ashtakavarga i Kakshya"):
                _render_ashtakavarga_compact(ascendant_sign_index(natal_asc_lon), natal_positions, rows)
    

    if view == "Položaji tranzita":
        st.subheader("Tablica tranzita")
        table = []
        for name in PLANET_ORDER:
            r = rows[name]
            nak = get_nakshatra(r.longitude)
            table.append({
                "Planet": name + (" ⭐" if r.highlighted else ""),
                "Znak": r.sign,
                "Stupanj": f"{r.degree_in_sign:.2f}°",
                "Nakshatra": nak.name,
                "Pada": nak.pada,
                "Kuća od Ascendenta": r.house_from_ascendant,
                "Kuća od Mjeseca": r.house_from_moon,
                "Retrogradan": "Da" if r.is_retrograde else "Ne",
            })
        colored_dataframe(table, use_container_width=True, hide_index=True, height=full_table_height(table))
        st.caption("⭐ = posebno praćeni tranziti (Saturn, Jupiter, Rahu, Ketu, Mars)")
    
    elif view == "Natalne točke":
        st.subheader("Natalni planeti i posebne točke (za usporedbu)")
        natal_table = []
        asc_nak_display = get_nakshatra(natal_asc_lon)
        natal_table.append({
            "Planet": "Lagna (Ascendent)", "Znak": RASHI[int(natal_asc_lon // 30)],
            "Stupanj": f"{natal_asc_lon % 30:.2f}°",
            "Nakshatra": asc_nak_display.name, "Pada": asc_nak_display.pada, "Retrogradan": "-",
        })
        for name in PLANET_ORDER:
            pos = natal_positions[name]
            nak = get_nakshatra(pos.longitude)
            natal_table.append({
                "Planet": name,
                "Znak": pos.sign,
                "Stupanj": f"{pos.degree_in_sign:.2f}°",
                "Nakshatra": nak.name,
                "Pada": nak.pada,
                "Retrogradan": "Da" if pos.is_retrograde else "Ne",
            })
        al_sign_idx_display = special_points["AL_sign_index"]
        natal_table.append({
            "Planet": "AL (Arudha Lagna)", "Znak": RASHI[al_sign_idx_display], "Stupanj": "-",
            "Nakshatra": "-", "Pada": "-", "Retrogradan": "-",
        })
        bp_nak = get_nakshatra(special_points["BP_longitude"])
        natal_table.append({
            "Planet": "BP (Bhrigu Bindu)", "Znak": RASHI[int(special_points["BP_longitude"] // 30)],
            "Stupanj": f"{special_points['BP_longitude'] % 30:.2f}°",
            "Nakshatra": bp_nak.name, "Pada": bp_nak.pada, "Retrogradan": "-",
        })
        if special_points["GK_longitude"] is not None:
            gk_lon = special_points["GK_longitude"]
            gk_nak = get_nakshatra(gk_lon)
            natal_table.append({
                "Planet": "GK (Gulika)", "Znak": RASHI[int(gk_lon // 30)],
                "Stupanj": f"{gk_lon % 30:.2f}°",
                "Nakshatra": gk_nak.name, "Pada": gk_nak.pada, "Retrogradan": "-",
            })
        if special_points.get("MANDI_longitude") is not None:
            mandi_lon = special_points["MANDI_longitude"]
            mandi_nak = get_nakshatra(mandi_lon)
            natal_table.append({
                "Planet": "Md (Mandi)", "Znak": RASHI[int(mandi_lon // 30)],
                "Stupanj": f"{mandi_lon % 30:.2f}°",
                "Nakshatra": mandi_nak.name, "Pada": mandi_nak.pada, "Retrogradan": "-",
            })
        # Sahami (PuS/ViS/YaS/VvS/PtS) su prikazani u kotaču tranzita, ali dosad
        # nigdje nisu imali svoj točan stupanj u tablici - dodano na izričit
        # zahtjev korisnika. Vrijednosti su već izračunate gore u natal_labels.
        for abbr, full_name in {
            **{SAHAM_INFO[n][0]: n for n in SAHAM_INFO},
        }.items():
            saham_lon = saham_values[full_name]
            saham_nak = get_nakshatra(saham_lon)
            natal_table.append({
                "Planet": f"{abbr} ({full_name} Saham)", "Znak": RASHI[int(saham_lon % 360.0 // 30)],
                "Stupanj": f"{saham_lon % 30:.2f}°",
                "Nakshatra": saham_nak.name, "Pada": saham_nak.pada, "Retrogradan": "-",
            })
        colored_dataframe(natal_table, use_container_width=True, hide_index=True, height=490)


_ASPECT_EXPLANATION = {
    "konjunkcija": "planeti su u istom stupnju (0°) - spajaju svoje teme",
    "sekstil": "60° razmaka - blaga, podržavajuća prilika",
    "kvadrat": "90° razmaka - napetost, prepreka koju treba riješiti",
    "trigon": "120° razmaka - lagan, povoljan protok",
    "opozicija": "180° razmaka - suprotstavljene teme, potreban balans",
}

_SAHAM_INFO = {
    "Punya": ("Sreća i zaštita", "Pokazuje gdje je izvor sreće, zaštite i dobrih djela tijekom godine."),
    "Vidya": ("Obrazovanje i učenje", "Pokazuje temu učenja, studija i stjecanja znanja tijekom godine."),
    "Yasha": ("Slava i ugled", "Pokazuje gdje se gradi ugled i prepoznatljivost tijekom godine."),
    "Vivaha": ("Brak i partnerstva", "Pokazuje temu vezanu uz brak i bliska partnerstva tijekom godine."),
    "Putra": ("Djeca i potomstvo", "Pokazuje temu vezanu uz djecu i događaje povezane s potomstvom tijekom godine."),
}


def _render_varshaphala(person, natal_positions, natal_asc_lon, birth_dt_utc, entry="Varshaphala"):
    birth_year = int(person.birth_date.split("-")[0])
    birth_month = int(person.birth_date.split("-")[1])
    birth_day = int(person.birth_date.split("-")[2])
    natal_sun_lon = natal_positions["Sunce"].longitude
    natal_moon_lon = natal_positions["Mjesec"].longitude

    reference_dt = analysis_date_service.get_reference_datetime()
    active_year = find_active_varshaphala_year(
        natal_sun_lon, birth_year, birth_month, birth_day, reference_dt
    )
    max_year = birth_year + 120

    # NAMJERNO bez value=/index= argumenta uz postojeći key na widgetu ispod
    # - kombinacija "key" i "value"/"index" je poznat Streamlit anti-pattern
    # koji zna tiho vratiti widget na zadanu vrijednost kad se widget iznova
    # instancira (npr. kod prebacivanja tabova). session_state je jedini
    # izvor istine za odabranu godinu; ovdje se SAMO odlučuje treba li ga
    # (re)postaviti na trenutačno aktivnu Varshaphalu prije stvaranja
    # widgeta - vidi ui/varsha_navigation.py:resolve_varsha_target_year za
    # točna pravila (auto-select samo kod prve otvaranja, promjene osobe,
    # ili klika na "Trenutačna Varshaphala").
    person_key = f"{person.name}|{person.birth_date}|{person.birth_time}"
    previous_person_key = st.session_state.get("varsha_target_year_person")
    previous_target_year = st.session_state.get("varsha_target_year")

    col_prev, col_select, col_next, col_current = st.columns([1, 2, 1, 2])
    with col_prev:
        prev_clicked = st.button(
            "◀ Prethodna", key="varsha_prev_year",
            disabled=(previous_target_year is not None and previous_target_year <= birth_year),
        )
    with col_next:
        next_clicked = st.button(
            "Sljedeća ▶", key="varsha_next_year",
            disabled=(previous_target_year is not None and previous_target_year >= max_year),
        )
    with col_current:
        current_clicked = st.button("Trenutačna Varshaphala", key="varsha_current_year_btn")

    target_year = resolve_varsha_target_year(
        previous_person_key=previous_person_key,
        current_person_key=person_key,
        previous_target_year=previous_target_year,
        active_year=active_year,
        current_button_clicked=current_clicked,
    )
    if prev_clicked and previous_target_year is not None and previous_target_year > birth_year:
        target_year = previous_target_year - 1
    elif next_clicked and previous_target_year is not None and previous_target_year < max_year:
        target_year = previous_target_year + 1

    st.session_state.varsha_target_year = target_year
    st.session_state.varsha_target_year_person = person_key

    year_options = list(range(birth_year, max_year + 1))
    with col_select:
        target_year = st.selectbox(
            "Godina za Varshaphalu", year_options, key="varsha_target_year",
        )
    target_year = int(target_year)

    result = compute_varshaphala(
        natal_sun_lon, natal_asc_lon, birth_year, birth_month, birth_day,
        target_year, person.latitude, person.longitude,
        natal_moon_lon, birth_dt_utc,
    )
    jd_return = find_solar_return_jd(natal_sun_lon, int(target_year), birth_month, birth_day)
    period_info = get_varshaphala_period_info(natal_sun_lon, birth_year, birth_month, birth_day, target_year)
    asc_sign_idx = int(result.ascendant_longitude // 30)

    # --- 0. Jasno odvojena polja o OVOJ Varshaphali (koja godina, aktivna
    # li je, kad počinje/završava, dob na početku, redni broj godine života
    # - namjerno odvojena polja, vidi core.varshaphala.VarshaphalaPeriodInfo) ---
    if entry == "Masa Pravesha":
        annual_view = "Masa Pravesha"
    elif entry == "Tajika":
        annual_view = st.radio("Tajika", ["Tajika yoge", "Aspekti", "Varsheshwara"], horizontal=True)
    else:
        annual_view = st.radio("Godišnji prikaz", ["Karta", "Masa Pravesha", "Mudda Dasha", "Sahame", "Varsheshwara", "Tajika yoge", "Aspekti", "Položaji", "Bhava Chalit"], horizontal=True)
    st.caption(f"Varshaphala {period_info.start_datetime_utc:%d.%m.%Y. %H:%M} – {period_info.end_datetime_utc:%d.%m.%Y. %H:%M} UTC")
    with st.expander("Razdoblje i dob"):
        st.caption(f"Početak: {period_info.year}. · Navršena dob: {period_info.completed_years_at_start} · Godina života: {period_info.life_year_number}.")
    # --- 1. Dijamant karta (prvo, kako je zatraženo) ---


    label_house_map = {}
    varsha_asc_nak = get_nakshatra(result.ascendant_longitude)
    label_house_map[f"({NAKSHATRA_ABBR[varsha_asc_nak.index]}-{varsha_asc_nak.pada})"] = 1
    for name in PLANET_ORDER:
        pos = result.planet_positions[name]
        label = format_planet_label(name, pos.longitude, pos.is_retrograde and name not in ("Rahu", "Ketu"))
        label_house_map[label] = whole_sign_house(pos.sign_index, asc_sign_idx)

    al_sign_idx = RASHI.index(result.arudha_lagna_sign)
    label_house_map["AL"] = whole_sign_house(al_sign_idx, asc_sign_idx)
    muntha_sign_idx = RASHI.index(result.muntha_sign)
    label_house_map["Mu"] = whole_sign_house(muntha_sign_idx, asc_sign_idx)
    label_house_map[format_point_label("BP", result.bhrigu_bindu_longitude)] = whole_sign_house(
        int(result.bhrigu_bindu_longitude // 30), asc_sign_idx
    )
    if result.gulika_longitude is not None:
        label_house_map[format_point_label("GK", result.gulika_longitude)] = whole_sign_house(
            int(result.gulika_longitude // 30), asc_sign_idx
        )
    if result.mandi_longitude is not None:
        label_house_map[format_point_label("Md", result.mandi_longitude)] = whole_sign_house(
            int(result.mandi_longitude // 30), asc_sign_idx
        )

    house_data = _build_house_data(asc_sign_idx, result.planet_positions, label_house_map)
    grouped = group_planets_by_house(label_house_map)
    extra_info = {
        h: f"S:{house_data[h]['strength']:.0f} P:{house_data[h]['argala_active']}/4"
        for h in house_data
    }
    svg = render_north_indian_svg(asc_sign_idx, grouped, title=f"Varshaphala {target_year}", house_extra_info=extra_info)
    if annual_view == "Karta":
        st.components.v1.html(f'<div style="height:445px;display:flex;justify-content:center">{svg}</div><style>svg {{max-height:440px;width:auto;max-width:100%;}}</style>', height=455)
        st.caption(
            "AL = Arudha Lagna, Mu = Muntha, BP = Bhrigu Bindu, GK = Gulika, Md = Mandi. "
            "S = pojednostavljena snaga kuće (vladar + stanari, NE puni Bhava Bala). "
            "P = broj aktivnih Argala izvora od mogućih 4."
        )
    
        # --- 2. Tekstualni detalji (poslije karte) ---
        st.subheader("Osnovni podaci")
        asc_nak_varsha = get_nakshatra(result.ascendant_longitude)
        st.write(
            f"**Godišnji ascendent:** {result.ascendant_sign} ({result.ascendant_longitude % 30:.2f}°), "
            f"{asc_nak_varsha.name} pada {asc_nak_varsha.pada}"
        )
        st.write(f"**Muntha:** {result.muntha_sign}")
        st.write(f"**Arudha Lagna:** {result.arudha_lagna_sign}")
    
        bp_nak_display = get_nakshatra(result.bhrigu_bindu_longitude)
        bp_house_display = whole_sign_house(int(result.bhrigu_bindu_longitude // 30), asc_sign_idx)
        st.write(
            f"**Bhrigu Bindu:** {RASHI[int(result.bhrigu_bindu_longitude // 30)]} "
            f"{result.bhrigu_bindu_longitude % 30:.2f}°, K{bp_house_display} (kuća), "
            f"{bp_nak_display.name} pada {bp_nak_display.pada}"
        )
        if result.gulika_longitude is not None:
            gk_nak_display = get_nakshatra(result.gulika_longitude)
            gk_house_display = whole_sign_house(int(result.gulika_longitude // 30), asc_sign_idx)
            st.write(
                f"**Gulika:** {RASHI[int(result.gulika_longitude // 30)]} "
                f"{result.gulika_longitude % 30:.2f}°, K{gk_house_display} (kuća), "
                f"{gk_nak_display.name} pada {gk_nak_display.pada}"
            )
        if result.mandi_longitude is not None:
            mandi_nak_display = get_nakshatra(result.mandi_longitude)
            mandi_house_display = whole_sign_house(int(result.mandi_longitude // 30), asc_sign_idx)
            st.write(
                f"**Mandi** (pojednostavljena metoda, {result.mandi_ghatikas:.0f} ghatija): "
                f"{RASHI[int(result.mandi_longitude // 30)]} {result.mandi_longitude % 30:.2f}°, "
                f"K{mandi_house_display} (kuća), {mandi_nak_display.name} pada {mandi_nak_display.pada}"
            )
        st.write(f"**Rođenje (Varsha Pravesha):** {'dan' if result.is_day_birth else 'noć'}")
        v_tithi = get_tithi(result.planet_positions["Mjesec"].longitude, result.planet_positions["Sunce"].longitude)
        st.write(f"**Tithi (Varsha Pravesha):** {v_tithi.name} ({v_tithi.paksha} paksha)")
    
    if annual_view == "Varsheshwara":
        st.caption(
            "Pancha Vargiya Bala sa svih 5 klasičnih sastavnica (Kshetra/Uchcha/"
            "Hadda/Drekkana/Navamsa - točni klasični bodovi). ✓ = kandidat ima "
            "valjan Tajika aspekt na Varsha Lagnu (klasičan uvjet kvalifikacije)."
        )
        if not result.varsheshwara["any_qualified"]:
            st.caption("Nijedan kandidat nema potrebni Tajika aspekt na godišnju lagnu — vladar godine nije određen ovom metodom.")
        for c in result.varsheshwara["candidates"]:
            marker = " ← **pobjednik**" if c is result.varsheshwara["winner"] else ""
            qual = " ✓" if c.aspects_varsha_lagna else ""
            st.write(f"- {c.role}: {c.planet}{qual} (snaga {c.strength_score:.2f} — {c.bala_detail}){marker}")

    if annual_view == "Tajika yoge":
        st.caption(
            "Ithasala/Isarapha ispod (opća mreža) vrijede za SVE parove planeta. "
            "Ostale klasične Tajika yoge (Nakta, Yamaya, Manau...) traže konkretno "
            "pitanje - odaberi kuću o kojoj pitaš, pa se Karyesha (vladar te kuće) "
            "uspoređuje s Lagneshom (vladarom Varsha Lagne)."
        )
        karyesha_options = [
            "1. Ja / tijelo / zdravlje općenito", "2. Novac / obitelj / govor",
            "3. Hrabrost / komunikacija / kratka putovanja", "4. Dom / majka / mir",
            "5. Djeca / kreativnost / romantika", "6. Zdravlje / neprijatelji / posao (svakodnevni)",
            "7. Brak / partnerstva", "8. Transformacija / nasljedstvo / iznenađenja",
            "9. Sreća / duhovnost / putovanja", "10. Karijera / status",
            "11. Dobit / prijatelji / želje", "12. Gubitci / inozemstvo / povučenost",
        ]
        karyesha_house_label = st.selectbox(
            "O kojem životnom području pitaš?",
            karyesha_options,
            key="karyesha_house_select",
        )
        karyesha_house_num = int(karyesha_house_label.split(".")[0])

        lagnesha = RASHI_LORD[result.ascendant_sign]
        karyesha_sign_index = (asc_sign_idx + karyesha_house_num - 1) % 12
        karyesha = RASHI_LORD[RASHI[karyesha_sign_index]]

        tajika_positions_tuples = {
            name: (result.planet_positions[name].longitude, result.planet_positions[name].is_retrograde)
            for name in TAJIKA_PLANETS
        }
        sign_index_by_planet = {name: result.planet_positions[name].sign_index for name in TAJIKA_PLANETS}

        st.write(f"**Lagnesha:** {lagnesha} (vladar Varsha Lagne)  \n**Karyesha:** {karyesha} (vladar {karyesha_house_num}. kuće)")

        karyesha_results = analyze_karyesha_yogas(
            lagnesha, karyesha, tajika_positions_tuples, sign_index_by_planet, asc_sign_idx,
        )
        for yr in karyesha_results:
            icon = "✅" if yr.found else "—"
            st.write(f"{icon} **{yr.name}**: {yr.detail}")

        st.markdown("**Globalne yoge (cijela karta, neovisno o odabranom području):**")
        ishkavala_found = compute_ishkavala(sign_index_by_planet, asc_sign_idx)
        induvara_found = compute_induvara(sign_index_by_planet, asc_sign_idx)
        khallasara_found = compute_khallasara(tajika_positions_tuples)
        st.write(
            f"{'✅' if ishkavala_found else '—'} **Ishkavala**: "
            + ("svih 7 planeta u kendri/panaphari - povoljno." if ishkavala_found else "nije zadovoljeno.")
        )
        st.write(
            f"{'✅' if induvara_found else '—'} **Induvara**: "
            + ("svih 7 planeta u apoklimi - razočaranja, brige." if induvara_found else "nije zadovoljeno.")
        )
        st.write(
            f"{'✅' if khallasara_found else '—'} **Khallasara** (Hartova definicija): "
            + ("Mjesec nema Ithasalu niti s kim - nepovoljno za predmet pitanja." if khallasara_found else "Mjesec ima barem jednu Ithasalu.")
        )

        st.caption(
            "Nije implementirano (nejasna/proturječna definicija između izvora): "
            "Gairikambula, Kuttha."
        )

    if annual_view == "Aspekti":
        st.caption(
            "Ithasala = brža planeta se približava sporijoj unutar orba (deeptamsha) - "
            "ukazuje na uspješan ishod, ostvarenje. Isarapha = brža planeta se udaljava "
            "nakon prošlog aspekta - ukazuje na priliku koja je promašena ili slabi. "
            "Kamboola traži Ithasalu između signifikatora i dodatnu Mjesečevu Ithasalu. "
            "posredovanjem treće strane. Ovo je OPĆA mreža (svi parovi od 7 planeta, "
            "bez konteksta pitanja) - za yoge vezane uz konkretno životno područje "
            "vidi sekciju 'Tajika yoge za konkretno životno područje' iznad."
        )

        if result.ithasala_pairs:
            st.markdown("**Ithasala (primjenjujući aspekti):**")
            for rel in result.ithasala_pairs:
                st.write(
                    f"- {rel.planet_a} — {rel.planet_b}: {rel.aspect} "
                    f"({_ASPECT_EXPLANATION.get(rel.aspect, '')}), {rel.faster} se približava {rel.slower}"
                )
        else:
            st.write("Nema Ithasala aspekata unutar orba u ovoj godišnjoj karti.")

        if result.isarapha_pairs:
            st.markdown("**Isarapha (razdvajajući aspekti):**")
            for rel in result.isarapha_pairs:
                st.write(
                    f"- {rel.planet_a} — {rel.planet_b}: {rel.aspect} "
                    f"({_ASPECT_EXPLANATION.get(rel.aspect, '')}), {rel.faster} se udaljava od {rel.slower}"
                )
        else:
            st.write("Nema Isarapha aspekata unutar orba u ovoj godišnjoj karti.")

        if result.kamboola_pairs:
            st.markdown("**Kamboola (Mjesec u Ithasala odnosu):**")
            for rel in result.kamboola_pairs:
                other = rel.planet_b if rel.planet_a == "Mjesec" else rel.planet_a
                st.write(f"- Mjesec — {other}: dodatna potvrda ishoda posredovanjem/utjecajem Mjeseca")

    if annual_view == "Sahame":
        st.markdown("**Godišnje sahame · odabrana Varshaphala**")
        _saham_table(result.ascendant_longitude, result.planet_positions, is_daytime(jd_return, person.latitude, person.longitude))

    if annual_view == "Mudda Dasha":
        st.caption(
            "Klasična Tajika formula: početni vladar se određuje iz rednog broja "
            "NATALNE (rođenjske) nakshatre Mjeseca i navršenih godina (ne iz natalnog "
            "Mahadasha vladara aktivnog u tom trenutku, i ne iz Mjeseca Varsha Pravesha "
            "karte), zatim se 360 dana ove godine dijeli standardnim Vimshottari "
            "redoslijedom (Vimshottari godina × 3 dana). Balance početnog perioda dolazi "
            "od udjela natalne nakshatre koji je Mjesec već 'prošao' u trenutku rođenja. "
            "Svaki period pokazuje koji planet 'boji' taj dio godine."
        )
        mudda_table = [
            {"Vladar": p.lord, "Početak": p.start.date(), "Kraj": p.end.date(),
             "Trajanje (dana)": round((p.end - p.start).total_seconds() / 86400, 1)}
            for p in result.mudda_dasha
        ]
        st.caption("Mudda: konvencija 360 civilnih dana; ciklus završava približno 5–6 dana prije sljedećeg solarnog povratka. Nije ista daša kao natalna Vimshottari.")
        colored_dataframe(mudda_table, use_container_width=True, hide_index=True, height=full_table_height(mudda_table))

    if annual_view == "Masa Pravesha":
        jd_return = find_solar_return_jd(natal_sun_lon, int(target_year), birth_month, birth_day)
        masa_sequence = compute_masa_pravesha_sequence(natal_sun_lon, jd_return, person.latitude, person.longitude)

        # Muntha Pati (vladar Munthinog znaka) - Muntha se pomiče samo jednom
        # godišnje, pa je i njen vladar ISTI za svih 12 Masa; ono što se ipak
        # mijenja iz mjeseca u mjesec je NJEGOVA kuća u toj mjesečnoj karti
        # (jer se mjesečni ascendent pomiče), zato ga pratimo po mjesecu.
        muntha_lord = RASHI_LORD[result.muntha_sign]
        masa_select = st.selectbox(
            "Prikaži kartu za mjesec:",
            [f"{m.month_number}. mjesec ({m.datetime_utc.strftime('%Y-%m-%d')})" for m in masa_sequence],
            key="masa_detail_select",
        )
        masa_idx = int(masa_select.split(".")[0]) - 1
        chosen_masa = masa_sequence[masa_idx]

        masa_asc_sign_idx = int(chosen_masa.ascendant_longitude // 30)
        masa_label_house_map = {}
        masa_asc_nak = get_nakshatra(chosen_masa.ascendant_longitude)
        masa_label_house_map[f"({NAKSHATRA_ABBR[masa_asc_nak.index]}-{masa_asc_nak.pada})"] = 1
        for name in PLANET_ORDER:
            pos = chosen_masa.planet_positions[name]
            label = format_planet_label(name, pos.longitude, pos.is_retrograde and name not in ("Rahu", "Ketu"))
            masa_label_house_map[label] = whole_sign_house(pos.sign_index, masa_asc_sign_idx)

        masa_label_house_map["AL"] = whole_sign_house(chosen_masa.arudha_lagna_sign_index, masa_asc_sign_idx)
        # Muntha se pomiče samo JEDNOM GODIŠNJE (na Varsha Pravesha) - isti Munthin
        # znak vrijedi za svih 12 Masa unutar te godine, samo se kuća preračunava
        # relativno na ascendent TOG mjeseca.
        masa_label_house_map["Mu"] = whole_sign_house(muntha_sign_idx, masa_asc_sign_idx)
        masa_label_house_map[format_point_label("BP", chosen_masa.bhrigu_bindu_longitude)] = whole_sign_house(
            int(chosen_masa.bhrigu_bindu_longitude // 30), masa_asc_sign_idx
        )
        if chosen_masa.gulika_longitude is not None:
            masa_label_house_map[format_point_label("GK", chosen_masa.gulika_longitude)] = whole_sign_house(
                int(chosen_masa.gulika_longitude // 30), masa_asc_sign_idx
            )
        if chosen_masa.mandi_longitude is not None:
            masa_label_house_map[format_point_label("Md", chosen_masa.mandi_longitude)] = whole_sign_house(
                int(chosen_masa.mandi_longitude // 30), masa_asc_sign_idx
            )

        masa_house_data = _build_house_data(masa_asc_sign_idx, chosen_masa.planet_positions, masa_label_house_map)
        masa_grouped = group_planets_by_house(masa_label_house_map)
        masa_extra_info = {
            h: f"S:{masa_house_data[h]['strength']:.0f} P:{masa_house_data[h]['argala_active']}/4"
            for h in masa_house_data
        }
        masa_svg = render_north_indian_svg(
            masa_asc_sign_idx, masa_grouped,
            title=f"Masa Pravesha {chosen_masa.month_number}. mjesec ({chosen_masa.datetime_utc.date()})",
            house_extra_info=masa_extra_info,
        )
        st.components.v1.html(f'<div style="height:445px;display:flex;justify-content:center">{masa_svg}</div><style>svg {{max-height:440px;width:auto;max-width:100%;}}</style>', height=455)
        st.write(
            f"**Muntha lord:** {muntha_lord} (vladar znaka {result.muntha_sign}, gdje je "
            f"Muntha - isti planet za svih 12 mjeseci, samo mu se kuća mijenja)"
        )

        masa_rows = []
        for m in masa_sequence:
            asc_nak_m = get_nakshatra(m.ascendant_longitude)
            m_asc_sign_idx = int(m.ascendant_longitude // 30)
            muntha_lord_pos = m.planet_positions[muntha_lord]
            muntha_lord_house = whole_sign_house(muntha_lord_pos.sign_index, m_asc_sign_idx)
            row = {
                "Mjesec": m.month_number,
                "Datum/vrijeme (UTC)": m.datetime_utc.strftime("%Y-%m-%d %H:%M"),
                "Ascendent": f"{m.ascendant_sign} {m.ascendant_longitude % 30:.2f}°",
                "Nakshatra": f"{asc_nak_m.name} pada {asc_nak_m.pada}",
                "Mjesec (planet)": f"{m.planet_positions['Mjesec'].sign} {m.planet_positions['Mjesec'].degree_in_sign:.1f}°",
                "Arudha Lagna": RASHI[m.arudha_lagna_sign_index],
                f"Muntha lord ({muntha_lord})": f"{muntha_lord_pos.sign} {muntha_lord_pos.degree_in_sign:.1f}°, {muntha_lord_house}. kuća",
                "Bhrigu Bindu": f"{RASHI[int(m.bhrigu_bindu_longitude // 30)]} {m.bhrigu_bindu_longitude % 30:.1f}°",
                "Gulika": (
                    f"{RASHI[int(m.gulika_longitude // 30)]} {m.gulika_longitude % 30:.1f}°"
                    if m.gulika_longitude is not None else "-"
                ),
                "Mandi": (
                    f"{RASHI[int(m.mandi_longitude // 30)]} {m.mandi_longitude % 30:.1f}°"
                    if m.mandi_longitude is not None else "-"
                ),
            }
            masa_rows.append(row)
        with st.expander("Pregled svih 12 mjeseci"):
            colored_dataframe(masa_rows, use_container_width=True, hide_index=True, height=420)

        st.caption(
            "Klasična Tajika tehnika (spominje je K.S. Charak, i Suryasiddhanta govori "
            "o 'varsha i maasa pravesha' kartama) - baš kao što Varsha Pravesha traži "
            "trenutak kad Sunce ponovno dosegne natalnu dužinu (jednom godišnje), Masa "
            "Pravesha traži trenutak kad Sunce dosegne natalnu dužinu + n×30° - 12 "
            "'mjesečnih ulazaka' unutar godine. 1. mjesec je sam trenutak Varsha Pravesha."
        )
        st.caption(
            "AL = Arudha Lagna, Mu = Muntha (isti Munthin znak kao za cijelu godinu - "
            "Muntha se pomiče samo jednom godišnje, ne mjesečno), BP = Bhrigu Bindu, "
            "GK = Gulika, Md = Mandi. S = pojednostavljena snaga kuće, P = broj aktivnih "
            "Argala izvora od mogućih 4 (isti sustav kao za godišnju kartu)."
        )

        st.write(f"**Arudha Lagna:** {RASHI[chosen_masa.arudha_lagna_sign_index]}")
        st.write(f"**Muntha:** {result.muntha_sign} (ista kao za cijelu godinu)")
        masa_bp_nak = get_nakshatra(chosen_masa.bhrigu_bindu_longitude)
        masa_bp_house = whole_sign_house(int(chosen_masa.bhrigu_bindu_longitude // 30), masa_asc_sign_idx)
        st.write(
            f"**Bhrigu Bindu:** {RASHI[int(chosen_masa.bhrigu_bindu_longitude // 30)]} "
            f"{chosen_masa.bhrigu_bindu_longitude % 30:.2f}°, K{masa_bp_house} (kuća), "
            f"{masa_bp_nak.name} pada {masa_bp_nak.pada}"
        )
        if chosen_masa.gulika_longitude is not None:
            masa_gk_nak = get_nakshatra(chosen_masa.gulika_longitude)
            masa_gk_house = whole_sign_house(int(chosen_masa.gulika_longitude // 30), masa_asc_sign_idx)
            st.write(
                f"**Gulika:** {RASHI[int(chosen_masa.gulika_longitude // 30)]} "
                f"{chosen_masa.gulika_longitude % 30:.2f}°, K{masa_gk_house} (kuća), "
                f"{masa_gk_nak.name} pada {masa_gk_nak.pada}"
            )
        if chosen_masa.mandi_longitude is not None:
            masa_md_nak = get_nakshatra(chosen_masa.mandi_longitude)
            masa_md_house = whole_sign_house(int(chosen_masa.mandi_longitude // 30), masa_asc_sign_idx)
            st.write(
                f"**Mandi** (pojednostavljena metoda, {chosen_masa.mandi_ghatikas:.0f} ghatija): "
                f"{RASHI[int(chosen_masa.mandi_longitude // 30)]} {chosen_masa.mandi_longitude % 30:.2f}°, "
                f"K{masa_md_house} (kuća), {masa_md_nak.name} pada {masa_md_nak.pada}"
            )

    if annual_view == "Položaji":
        for name in PLANET_ORDER:
            pos = result.planet_positions[name]
            st.write(f"{name}: {pos.sign} {pos.degree_in_sign:.2f}°")

    if annual_view == "Bhava Chalit":
        st.caption(
            "Bhava Chalit koristi točan stupanj godišnjeg ascendenta kao sredinu 1. kuće."
        )
        chalit_rows = []
        for name in PLANET_ORDER:
            pos = result.planet_positions[name]
            ws_house = whole_sign_house(pos.sign_index, asc_sign_idx)
            chalit_house = bhava_chalit_house(pos.longitude, result.ascendant_longitude)
            chalit_rows.append({
                "Planet": name,
                "Whole Sign kuća": ws_house,
                "Bhava Chalit kuća": chalit_house,
                "Razlika": "DA" if ws_house != chalit_house else "-",
            })
        colored_dataframe(chalit_rows, use_container_width=True, hide_index=True, height=full_table_height(chalit_rows))


def _saham_table(asc, positions, day):
    values = compute_sahams(asc, positions, day)
    group = st.radio("Područje", ["Odnosi", "Posao i novac", "Obitelj i zdravlje", "Sve"], horizontal=True, key="saham_group")
    groups = {"Odnosi": ["Punya", "Vivaha", "Preeti", "Mitra", "Sraddha"], "Posao i novac": ["Karma", "Vyapara", "Artha", "Labha", "Yasha", "Rajya", "Vidya", "Sastra", "Paradesa"], "Obitelj i zdravlje": ["Putra", "Matri", "Pitri", "Bhratri", "Bandhu", "Roga"]}
    names = list(SAHAM_INFO) if group == "Sve" else groups[group]
    data = []
    for name in names:
        lon = values[name]; nak = get_nakshatra(lon); sign = int(lon // 30)
        data.append({"Sahama": name, "Tema": SAHAM_INFO[name][1], "Znak": RASHI[sign], "Stupanj": f"{lon%30:.2f}°", "Kuća": whole_sign_house(sign,int(asc//30)), "Nakshatra": nak.name, "Pada": nak.pada, "Vladar": RASHI_LORD[RASHI[sign]]})
    colored_dataframe(data, hide_index=True, use_container_width=True, height=min(full_table_height(data),450))
    st.caption("Metoda PVR Narasimha Rao · dan/noć prema položaju Sunca nad horizontom · korekcija luka +30° · kućne točke zadržavaju stupanj ascendenta.")


def _render_sahams(person, ctx):
    scope = st.radio("Karta za sahame", ["Natalna", "Godišnja", "Mjesečna"], horizontal=True)
    asc, positions, jd = ctx.ascendant_longitude, ctx.positions, ctx.jd_ut
    if scope != "Natalna":
        ref = analysis_date_service.get_reference_datetime()
        year = find_active_varshaphala_year(ctx.positions["Sunce"].longitude, int(person.birth_date[:4]), int(person.birth_date[5:7]), int(person.birth_date[8:10]), ref)
        year = st.number_input("Godina početka Varshaphale", value=year, min_value=int(person.birth_date[:4]), max_value=int(person.birth_date[:4])+120, step=1)
        jd = find_solar_return_jd(ctx.positions["Sunce"].longitude, year, int(person.birth_date[5:7]), int(person.birth_date[8:10]))
        from core.ephemeris import get_ascendant, get_planet_positions
        if scope == "Mjesečna":
            months = compute_masa_pravesha_sequence(ctx.positions["Sunce"].longitude,jd,person.latitude,person.longitude)
            index = st.selectbox("Mjesec",range(12),format_func=lambda i:f"{i+1}. · {months[i].datetime_utc:%d.%m.%Y. %H:%M} UTC")
            m=months[index];asc=m.ascendant_longitude;positions=m.planet_positions;jd=__import__("core.time_utils", fromlist=["utc_to_julian_day"]).utc_to_julian_day(m.datetime_utc)
        else:
            asc=get_ascendant(jd,person.latitude,person.longitude);positions=get_planet_positions(jd)
    st.markdown(f"**{scope} karta · sahame**")
    _saham_table(asc, positions, is_daytime(jd,person.latitude,person.longitude))
