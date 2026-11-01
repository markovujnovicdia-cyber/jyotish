"""
Streamlit stranica: Sinastrija (usporedba dviju natalnih karata).

Faza 1: kućni overlay D1, Graha Drishti između karata, stupanjske
konjunkcije, osnovna tablica kontakata, osnovni tekstualni izvještaj.
Faza 2: nakšatra sinastrija, Ashtakoota, Kuja Dosha, ključni signifikatori
odnosa (7. kuća, Venera, Mars, Jupiter, Mjesec, Atmakaraka/Darakaraka,
Arudha Lagna, UL, A7).
Faza 3: D9 (Navamsha) sinastrija, kategorijsko bodovanje (transparentno,
bez dvostrukog brojanja), preklopljeni grafički prikaz (D1/D9, uključivi
slojevi A/B, tekstualne oznake umjesto oslanjanja samo na boju).
Faza 4: prediktivna sinastrija - tranzitna aktivacija natalne sinastrije,
dvostruki tranzit Jupitera/Saturna, Vimshottari Dasha aktivacije, vremenska
crta.
Faza 5: Varshaphala/Mudda Dasha aktivacije, fina mjesečna/dnevna (Mjesec kao
okidač) analiza, izvoz (JSON/CSV/PDF/SVG).
"""

from datetime import date, datetime, timedelta, timezone

import streamlit as st

from core.constants import RASHI, RASHI_LORD, PLANET_ORDER, PLANET_ABBR
from core.natal import get_natal_context
from core.houses import whole_sign_house
from core.varga import d1_sign_index, d9_navamsha_sign_index
from core.chara_karaka import get_atmakaraka, get_darakaraka
from core.synastry.config import (
    SynastryConfig, DEFAULT_CONJUNCTION_ORBS, DEFAULT_NODE_ASPECT_MODE,
    DEFAULT_CHARA_KARAKA_SCHEME, DEFAULT_KUJA_DOSHA_HOUSES,
)
from core.synastry.overlays import compute_house_overlay, find_mutual_emphasis
from core.synastry.graha_drishti import build_graha_drishti_contacts
from core.synastry.conjunctions import find_conjunctions
from core.synastry.interpretation import (
    enrich_graha_drishti_contacts, enrich_conjunction_contacts,
    enrich_graha_drishti_contacts_with_axis_context,
)
from core.synastry.deduplication import build_role_map
from core.synastry.relationship_profiles import (
    RELATIONSHIP_TYPE_KEYS, RELATIONSHIP_TYPE_LABELS, DEFAULT_RELATIONSHIP_TYPE,
    get_relationship_profile, resolve_relationship_key,
)
from core.synastry.nakshatra_matching import compute_nakshatra_synastry
from core.synastry.ashtakoota import compute_ashtakoota
from core.synastry.kuja_dosha import compare_kuja_dosha
from core.synastry.relationship_significators import compute_relationship_significators
from core.synastry.divisional_synastry import compute_navamsha_synastry
from core.synastry.scoring import compute_synastry_scores
from core.synastry.scoring_config import CATEGORY_NAMES
from core.synastry.transit_activations import build_natal_synastry_links
from core.synastry.predictive import compute_predictive_snapshot, compute_timeline
from core.synastry.varshaphala_activations import compute_varshaphala_synastry
from core.synastry.monthly_daily_activations import compute_moon_trigger_days_over_range
from core.synastry.export import build_csv_contacts, build_csv_timeline, build_json_export, build_pdf_report
from core.synastry.report import build_basic_report
from db import database
from ui.north_indian_chart import render_north_indian_svg, group_planets_by_house
from ui.df_utils import full_table_height

RELATIONSHIP_TYPES = [RELATIONSHIP_TYPE_LABELS[k] for k in RELATIONSHIP_TYPE_KEYS]

_NODE_MODE_LABELS = {
    "seventh_only": "Samo 7. aspekt (zadano)",
    "5_7_9": "5., 7. i 9. aspekt (analogno Jupiteru)",
    "none": "Bez aspekata čvorova",
}
_NODE_MODE_BY_LABEL = {v: k for k, v in _NODE_MODE_LABELS.items()}


def _init_settings_state():
    if "synastry_node_mode" not in st.session_state:
        st.session_state.synastry_node_mode = DEFAULT_NODE_ASPECT_MODE
    if "synastry_orb_luminaries" not in st.session_state:
        st.session_state.synastry_orb_luminaries = DEFAULT_CONJUNCTION_ORBS["Sunce"]
    if "synastry_orb_personal" not in st.session_state:
        st.session_state.synastry_orb_personal = DEFAULT_CONJUNCTION_ORBS["Mars"]
    if "synastry_orb_jup_sat" not in st.session_state:
        st.session_state.synastry_orb_jup_sat = DEFAULT_CONJUNCTION_ORBS["Jupiter"]
    if "synastry_orb_nodes" not in st.session_state:
        st.session_state.synastry_orb_nodes = DEFAULT_CONJUNCTION_ORBS["Rahu"]
    if "synastry_orb_sensitive" not in st.session_state:
        st.session_state.synastry_orb_sensitive = DEFAULT_CONJUNCTION_ORBS["_sensitive"]
    if "synastry_bhava_chalit" not in st.session_state:
        st.session_state.synastry_bhava_chalit = True
    if "synastry_karaka_scheme" not in st.session_state:
        st.session_state.synastry_karaka_scheme = DEFAULT_CHARA_KARAKA_SCHEME
    if "synastry_kuja_houses" not in st.session_state:
        st.session_state.synastry_kuja_houses = set(DEFAULT_KUJA_DOSHA_HOUSES)


def _build_config_from_state() -> SynastryConfig:
    orbs = {
        "Sunce": st.session_state.synastry_orb_luminaries, "Mjesec": st.session_state.synastry_orb_luminaries,
        "Mars": st.session_state.synastry_orb_personal, "Merkur": st.session_state.synastry_orb_personal,
        "Venera": st.session_state.synastry_orb_personal,
        "Jupiter": st.session_state.synastry_orb_jup_sat, "Saturn": st.session_state.synastry_orb_jup_sat,
        "Rahu": st.session_state.synastry_orb_nodes, "Ketu": st.session_state.synastry_orb_nodes,
        "_sensitive": st.session_state.synastry_orb_sensitive,
    }
    return SynastryConfig(
        node_aspect_mode=st.session_state.synastry_node_mode,
        conjunction_orbs=orbs,
        use_bhava_chalit=st.session_state.synastry_bhava_chalit,
        chara_karaka_scheme=st.session_state.synastry_karaka_scheme,
        kuja_dosha_houses=frozenset(st.session_state.synastry_kuja_houses),
    )


def render():
    st.header("Sinastrija")

    persons = database.list_persons()
    if len(persons) < 2:
        st.info("Potrebne su barem dvije spremljene osobe za sinastriju (dodaj ih na stranici 'Osobe').")
        return

    from ui.person_picker import select_person

    col_a, col_b = st.columns(2)
    with col_a:
        person_a = select_person(persons, container=st, label="Osoba A", key="synastry_person_a")
    with col_b:
        person_b = select_person(persons, container=st, label="Osoba B", key="synastry_person_b", default_index=1)

    if person_a.id == person_b.id:
        st.warning("Odaberi dvije RAZLIČITE osobe za sinastriju.")
        return

    # ISPRAVAK (spec 1): ključ je scope-an PO PARU osoba (ne globalno) da
    # izbor vrste odnosa jednog para NE "procuri" tiho na drugi par pri
    # prebacivanju osoba - i eksplicitni index=0 (ljubavni/partnerski) kao
    # jasan zadani odabir umjesto oslanjanja na Streamlitovu implicitnu
    # zadanu vrijednost.
    relationship_key_field = f"synastry_relationship_type_{person_a.id}_{person_b.id}"
    saved_preference = database.get_synastry_relationship_type(person_a.id, person_b.id)
    if relationship_key_field not in st.session_state:
        st.session_state[relationship_key_field] = (
            RELATIONSHIP_TYPE_LABELS.get(saved_preference, RELATIONSHIP_TYPE_LABELS[DEFAULT_RELATIONSHIP_TYPE])
        )
    relationship_type = st.selectbox(
        "Vrsta odnosa", RELATIONSHIP_TYPES, key=relationship_key_field,
    )
    relationship_type_key = resolve_relationship_key(relationship_type)
    database.save_synastry_relationship_type(person_a.id, person_b.id, relationship_type_key)
    relationship_profile = get_relationship_profile(relationship_type_key)
    st.caption(
        "Vrsta odnosa utječe SAMO na izbor/naglasak interpretacijskih tema i na blagu "
        "(±15%) prilagodbu kategorijskih težina u bodovanju - astronomski položaji, kuće i "
        "aspekti su identični za sve vrste odnosa. " + relationship_profile.framing_note
    )

    if not person_a.time_confirmed or not person_b.time_confirmed:
        st.warning(
            "Barem jedna od osoba nema potvrđeno sigurno vrijeme rođenja - kućni overlay, "
            "Bhava Chalit i posebne točke (AL/UL/A7) mogu biti netočni za tu osobu."
        )

    _init_settings_state()

    (tab_summary, tab_overlay, tab_drishti, tab_conj, tab_nakshatra, tab_ashtakoota,
     tab_significators, tab_navamsha, tab_scoring, tab_predictive, tab_timeline,
     tab_report, tab_settings) = st.tabs([
        "Sažetak", "Kućni overlay", "Graha Drishti", "Konjunkcije", "Nakšatre",
        "Ashtakoota", "Signifikatori (UL/A7/DK)", "D9 sinastrija", "Bodovanje",
        "Prediktivna sinastrija", "Vremenska crta", "Izvještaj", "Postavke",
    ])

    # VAŽNO: postavke se moraju instancirati (i time ažurirati session_state)
    # PRIJE nego što se iz njih izgradi config - inače bi promjena postavke
    # kasnila jedan rerun (widget bi ažurirao session_state tek NAKON što je
    # config već izgrađen s prijašnjom vrijednosti). `with tab_settings:` se
    # smije pozvati ovdje, izvan vizualnog redoslijeda tabova - Streamlit
    # kontejner prima elemente bez obzira na to kad je taj `with` blok
    # izvršen unutar skripte.
    with tab_settings:
        _render_settings()

    config = _build_config_from_state()

    ctx_a = get_natal_context(person_a)
    ctx_b = get_natal_context(person_b)

    overlay_a_to_b = compute_house_overlay(ctx_a, ctx_b, "A", "B")
    overlay_b_to_a = compute_house_overlay(ctx_b, ctx_a, "B", "A")
    mutual_notes = find_mutual_emphasis(overlay_a_to_b, overlay_b_to_a)

    drishti_a_to_b = enrich_graha_drishti_contacts(build_graha_drishti_contacts(ctx_a, ctx_b, "A", "B", config))
    drishti_b_to_a = enrich_graha_drishti_contacts(build_graha_drishti_contacts(ctx_b, ctx_a, "B", "A", config))

    points_a = {name: pos.longitude for name, pos in ctx_a.positions.items()}
    points_a["Lagna"] = ctx_a.ascendant_longitude
    points_b = {name: pos.longitude for name, pos in ctx_b.positions.items()}
    points_b["Lagna"] = ctx_b.ascendant_longitude
    seventh_lord_a = _seventh_lord(ctx_a.ascendant_sign_index)
    seventh_lord_b = _seventh_lord(ctx_b.ascendant_sign_index)
    conjunctions = enrich_conjunction_contacts(
        find_conjunctions(points_a, points_b, config, seventh_lord_a, seventh_lord_b)
    )

    karaka_positions_a = {p: pos for p, pos in ctx_a.positions.items() if p != "Ketu"}
    karaka_positions_b = {p: pos for p, pos in ctx_b.positions.items() if p != "Ketu"}
    darakaraka_a = get_darakaraka(karaka_positions_a, config.chara_karaka_scheme).planet
    darakaraka_b = get_darakaraka(karaka_positions_b, config.chara_karaka_scheme).planet
    atmakaraka_a = get_atmakaraka(karaka_positions_a, config.chara_karaka_scheme).planet
    atmakaraka_b = get_atmakaraka(karaka_positions_b, config.chara_karaka_scheme).planet

    nakshatra_result = compute_nakshatra_synastry(
        ctx_a, ctx_b, seventh_lord_a, seventh_lord_b, darakaraka_a, darakaraka_b,
        drishti_a_to_b + drishti_b_to_a, conjunctions,
    )
    ashtakoota_result = compute_ashtakoota(
        ctx_a.positions["Mjesec"].longitude, ctx_b.positions["Mjesec"].longitude,
    )
    kuja_comparison = compare_kuja_dosha(ctx_a, ctx_b, config)
    significators_result = compute_relationship_significators(
        ctx_a, ctx_b, config, drishti_a_to_b + drishti_b_to_a, conjunctions,
    )
    navamsha_result = compute_navamsha_synastry(
        ctx_a, ctx_b, config, seventh_lord_a, seventh_lord_b,
        darakaraka_a, darakaraka_b, atmakaraka_a, atmakaraka_b,
        drishti_a_to_b + drishti_b_to_a, conjunctions,
    )

    # Druga (obogaćena) enrichment putanja - SADA kad navamsha_result postoji,
    # osi 3./10., 4./8., 5./9. dobivaju funkcionalnu prirodu/dostojanstvo/D9
    # potvrdu umjesto paušalnog teksta (spec 7). Mutira iste objekte iz
    # drishti_a_to_b/drishti_b_to_a, pa se rezultat automatski vidi i u
    # tabu "Graha Drishti" i u izvještaju.
    enrich_graha_drishti_contacts_with_axis_context(drishti_a_to_b, ctx_a, ctx_b, navamsha_result)
    enrich_graha_drishti_contacts_with_axis_context(drishti_b_to_a, ctx_a, ctx_b, navamsha_result)

    asc_lord_a = RASHI_LORD[RASHI[ctx_a.ascendant_sign_index]]
    asc_lord_b = RASHI_LORD[RASHI[ctx_b.ascendant_sign_index]]

    def _house_lord(asc_idx: int, house_num: int) -> str:
        return RASHI_LORD[RASHI[(asc_idx + house_num - 1) % 12]]

    role_map = build_role_map(
        darakaraka_a=darakaraka_a, atmakaraka_a=atmakaraka_a, seventh_lord_a=seventh_lord_a,
        darakaraka_b=darakaraka_b, atmakaraka_b=atmakaraka_b, seventh_lord_b=seventh_lord_b,
        upapada_lord_a=significators_result.profile_a.upapada_lord,
        upapada_lord_b=significators_result.profile_b.upapada_lord,
        first_lord_a=asc_lord_a, first_lord_b=asc_lord_b,
        fifth_lord_a=_house_lord(ctx_a.ascendant_sign_index, 5), fifth_lord_b=_house_lord(ctx_b.ascendant_sign_index, 5),
        eighth_lord_a=_house_lord(ctx_a.ascendant_sign_index, 8), eighth_lord_b=_house_lord(ctx_b.ascendant_sign_index, 8),
        eleventh_lord_a=_house_lord(ctx_a.ascendant_sign_index, 11), eleventh_lord_b=_house_lord(ctx_b.ascendant_sign_index, 11),
        darapada_lord_a=RASHI_LORD[significators_result.profile_a.darapada_sign],
        darapada_lord_b=RASHI_LORD[significators_result.profile_b.darapada_sign],
    )

    score_result = compute_synastry_scores(
        drishti_a_to_b + drishti_b_to_a, conjunctions, overlay_a_to_b + overlay_b_to_a,
        ashtakoota_result, kuja_comparison, nakshatra_result, navamsha_result, role_map,
        relationship_profile.category_weight_multipliers,
    )

    natal_links = build_natal_synastry_links(
        ctx_a, ctx_b, drishti_a_to_b + drishti_b_to_a, conjunctions, nakshatra_result,
    )

    with tab_summary:
        _render_summary(
            person_a, person_b, ctx_a, ctx_b, mutual_notes, drishti_a_to_b + drishti_b_to_a, conjunctions,
            overlay_a_to_b, overlay_b_to_a, navamsha_result,
        )

    with tab_overlay:
        _render_overlay(overlay_a_to_b, overlay_b_to_a, mutual_notes)

    with tab_drishti:
        _render_drishti(person_a, person_b, drishti_a_to_b, drishti_b_to_a)

    with tab_conj:
        _render_conjunctions(conjunctions)

    with tab_nakshatra:
        _render_nakshatra(person_a, person_b, nakshatra_result)

    with tab_ashtakoota:
        _render_ashtakoota(ashtakoota_result, kuja_comparison)

    with tab_significators:
        _render_significators(person_a, person_b, significators_result)

    with tab_navamsha:
        _render_navamsha(person_a, person_b, navamsha_result)

    with tab_scoring:
        _render_scoring(score_result)

    with tab_predictive:
        _render_predictive(
            person_a, person_b, ctx_a, ctx_b, natal_links,
            seventh_lord_a, seventh_lord_b, darakaraka_a, darakaraka_b, asc_lord_a, asc_lord_b, config,
        )

    with tab_timeline:
        _render_timeline(
            ctx_a, ctx_b, natal_links,
            seventh_lord_a, seventh_lord_b, darakaraka_a, darakaraka_b, asc_lord_a, asc_lord_b, config,
        )

    with tab_report:
        _render_report(
            person_a, person_b, ctx_a, ctx_b, relationship_type, config,
            overlay_a_to_b, overlay_b_to_a, mutual_notes, drishti_a_to_b, drishti_b_to_a, conjunctions,
            nakshatra_result, ashtakoota_result, kuja_comparison, significators_result,
            navamsha_result, score_result, relationship_profile,
        )


def _seventh_lord(asc_sign_idx: int) -> str:
    seventh_sign = RASHI[(asc_sign_idx + 6) % 12]
    return RASHI_LORD[seventh_sign]


def _varga_label(name: str, is_retrograde: bool) -> str:
    abbr = PLANET_ABBR.get(name, name[:2])
    if is_retrograde and name not in ("Rahu", "Ketu"):
        abbr += "R"
    return abbr


def _build_overlay_label_map(self_ctx, other_ctx, varga_func, other_label, show_self, show_other):
    """
    Gradi label_house_map za JEDAN dijamant (self_ctx-ov ascendent kao
    referenca): vlastiti planeti (obični tekst) + planeti druge osobe
    (u šiljastim zagradama s oznakom osobe) - razlikovanje TEKSTOM, ne
    samo bojom.
    """
    asc_idx = varga_func(self_ctx.ascendant_longitude)
    label_house_map = {}
    if show_self:
        for name in PLANET_ORDER:
            pos = self_ctx.positions[name]
            label = _varga_label(name, pos.is_retrograde)
            label_house_map[label] = whole_sign_house(varga_func(pos.longitude), asc_idx)
    if show_other:
        for name in PLANET_ORDER:
            pos = other_ctx.positions[name]
            label = f"⟨{other_label}:{_varga_label(name, pos.is_retrograde)}⟩"
            label_house_map[label] = whole_sign_house(varga_func(pos.longitude), asc_idx)
    return label_house_map


def _render_summary(person_a, person_b, ctx_a, ctx_b, mutual_notes, drishti_all, conjunctions,
                     overlay_a_to_b, overlay_b_to_a, navamsha_result):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(person_a.name)
        st.caption(f"{person_a.birth_date} {person_a.birth_time} · {person_a.birth_place}")
        st.write(f"Ascendent: {RASHI[ctx_a.ascendant_sign_index]}")
    with col2:
        st.subheader(person_b.name)
        st.caption(f"{person_b.birth_date} {person_b.birth_time} · {person_b.birth_place}")
        st.write(f"Ascendent: {RASHI[ctx_b.ascendant_sign_index]}")

    st.markdown("---")
    st.subheader("Grafički prikaz")
    col_varga, col_toggle_a, col_toggle_b = st.columns([1, 1, 1])
    with col_varga:
        varga_choice = st.radio("Karta", ["D1 (Rashi)", "D9 (Navamsha)"], key="synastry_chart_varga", horizontal=True)
    with col_toggle_a:
        show_a = st.checkbox(f"Prikaži {person_a.name}", value=True, key="synastry_chart_show_a")
    with col_toggle_b:
        show_b = st.checkbox(f"Prikaži {person_b.name}", value=True, key="synastry_chart_show_b")

    varga_func = d1_sign_index if varga_choice == "D1 (Rashi)" else d9_navamsha_sign_index
    varga_title = "D1" if varga_choice == "D1 (Rashi)" else "D9"

    col_chart_a, col_chart_b = st.columns(2)
    with col_chart_a:
        grouped_a = group_planets_by_house(
            _build_overlay_label_map(ctx_a, ctx_b, varga_func, "B", show_a, show_b)
        )
        svg_a = render_north_indian_svg(varga_func(ctx_a.ascendant_longitude), grouped_a, title=f"{person_a.name} ({varga_title})")
        st.components.v1.html(f'<div style="width:100%; max-width:520px">{svg_a}</div>', height=480)
        st.download_button(
            f"Preuzmi kartu {person_a.name} (.svg)", svg_a,
            file_name=f"{person_a.name}_{varga_title}_overlay.svg".replace(" ", "_"), mime="image/svg+xml",
            key="synastry_svg_download_a",
        )
    with col_chart_b:
        grouped_b = group_planets_by_house(
            _build_overlay_label_map(ctx_b, ctx_a, varga_func, "A", show_b, show_a)
        )
        svg_b = render_north_indian_svg(varga_func(ctx_b.ascendant_longitude), grouped_b, title=f"{person_b.name} ({varga_title})")
        st.components.v1.html(f'<div style="width:100%; max-width:520px">{svg_b}</div>', height=480)
        st.download_button(
            f"Preuzmi kartu {person_b.name} (.svg)", svg_b,
            file_name=f"{person_b.name}_{varga_title}_overlay.svg".replace(" ", "_"), mime="image/svg+xml",
            key="synastry_svg_download_b",
        )

    st.caption(
        "**Legenda:** obični tekst = vlastiti planet te osobe. `⟨X:Ve⟩` (šiljaste zagrade + oznaka osobe) = "
        "planet OSOBE X preklopljen u ovu kartu, prikazan na kući u koju pada. R = retrogradan. "
        "Uključi/isključi slojeve gornjim kućicama. Klikom na SVG nema interaktivnog isticanja (ograničenje "
        "trenutačnog prikaza) - koristi izbornik ispod za detalje o pojedinom planetu/točki."
    )

    _render_point_detail(person_a, person_b, ctx_a, ctx_b, drishti_all, conjunctions, overlay_a_to_b, overlay_b_to_a)

    st.markdown("---")
    st.subheader("Preliminarni istaknuti pokazatelji")
    st.caption(
        "Ovo je JEDNOSTAVNA, kvalitativna lista (ne puni sustav bodovanja - taj dolazi u kasnijoj fazi). "
        "Temelji se na egzaktnosti kontakta i uključenim planetima."
    )
    positive_keywords = {"Venera", "Jupiter", "Mjesec"}
    challenge_keywords = {"Saturn", "Mars", "Rahu", "Ketu"}

    strong_links = []
    for c in conjunctions:
        if c.is_exact:
            tag = "izazovan" if (positive_keywords.isdisjoint({c.person_a_object, c.person_b_object}) and
                                   not challenge_keywords.isdisjoint({c.person_a_object, c.person_b_object})) else "povezujući"
            strong_links.append((tag, c.short_interpretation))
    for d in drishti_all:
        if d.strength == 1.0 and d.house_distance == 7:
            tag = "izazovan" if d.from_planet in challenge_keywords else "povezujući"
            strong_links.append((tag, d.short_interpretation))

    connecting = [text for tag, text in strong_links if tag == "povezujući"][:5]
    challenging = [text for tag, text in strong_links if tag == "izazovan"][:5]

    col_pos, col_neg = st.columns(2)
    with col_pos:
        st.markdown("**Najjači povezujući pokazatelji**")
        if connecting:
            for t in connecting:
                st.write(f"- {t}")
        else:
            st.write("_Nema izrazito jakih egzaktnih kontakata u ovom izboru._")
    with col_neg:
        st.markdown("**Najveći izazovi**")
        if challenging:
            for t in challenging:
                st.write(f"- {t}")
        else:
            st.write("_Nema izrazito napetih egzaktnih kontakata u ovom izboru._")

    st.markdown("---")
    st.subheader("Ponovljeni (uzajamni) obrasci")
    if mutual_notes:
        for n in mutual_notes:
            st.write(f"- {n}")
    else:
        st.write("_Nije pronađen izravan uzajamni obrazac istog planeta u oba smjera._")


def _render_point_detail(person_a, person_b, ctx_a, ctx_b, drishti_all, conjunctions, overlay_a_to_b, overlay_b_to_a):
    """
    Praktična zamjena za hover-tooltip/klik-na-SVG isticanje (koje bez
    prilagođene Streamlit komponente s JS-om nije pouzdano izvedivo):
    korisnik odabere planet+osobu iz izbornika, a ispod se ispisuju SVE
    već izračunate činjenice o toj točki (kućni overlay, Graha Drishti,
    konjunkcije) - funkcionalno ekvivalentno "isticanju", samo odabirom
    umjesto klikom na kartu.
    """
    with st.expander("Detalji o pojedinom planetu/točki (zamjena za tooltip)"):
        options = [f"{p} (A)" for p in PLANET_ORDER] + [f"{p} (B)" for p in PLANET_ORDER]
        choice = st.selectbox("Odaberi planet i osobu", options, key="synastry_point_detail_select")
        planet_name, person_label = choice.rsplit(" (", 1)
        person_label = person_label.rstrip(")")

        own_ctx = ctx_a if person_label == "A" else ctx_b
        own_person = person_a if person_label == "A" else person_b
        pos = own_ctx.positions[planet_name]
        st.write(f"**{planet_name} ({own_person.name}):** {pos.sign}, {pos.degree_in_sign:.2f}°"
                 + (" (retrogradan)" if pos.is_retrograde and planet_name not in ("Rahu", "Ketu") else ""))

        overlay_rows = overlay_a_to_b if person_label == "A" else overlay_b_to_a
        own_row = next((r for r in overlay_rows if r.planet == planet_name), None)
        if own_row:
            st.write(f"- Pada u {own_row.whole_sign_house}. kuću druge osobe ({own_row.target_house_lord_relation}).")

        relevant_drishti = [c for c in drishti_all if
                             (c.from_planet == planet_name and c.source_person == person_label) or
                             (c.to_planet == planet_name and c.target_person == person_label)]
        if relevant_drishti:
            st.write("**Graha Drishti:**")
            for c in relevant_drishti:
                st.write(f"- {c.short_interpretation}")

        relevant_conj = [c for c in conjunctions if
                          (c.person_a_object == planet_name and person_label == "A") or
                          (c.person_b_object == planet_name and person_label == "B")]
        if relevant_conj:
            st.write("**Konjunkcije:**")
            for c in relevant_conj:
                st.write(f"- {c.short_interpretation}")

        if not own_row and not relevant_drishti and not relevant_conj:
            st.write("_Nema zabilježenih kontakata za ovu točku unutar trenutačnih postavki._")


def _render_overlay(overlay_a_to_b, overlay_b_to_a, mutual_notes):
    st.caption(
        "★ = kuća iz posebno naglašenog skupa (1,2,4,5,7,8,9,10,11,12). "
        "Bhava Chalit kuća je prikazana samo kad se razlikuje od Whole Sign kuće."
    )

    for title, rows in (
        ("Planeti osobe A u karti osobe B", overlay_a_to_b),
        ("Planeti osobe B u karti osobe A", overlay_b_to_a),
    ):
        st.subheader(title)
        table = [{
            "Planet": r.planet + (" ★" if r.is_significant_house else ""),
            "Znak": r.sign,
            "Kuća (Whole Sign)": r.whole_sign_house,
            "Kuća (Bhava Chalit)": str(r.bhava_chalit_house) if r.bhava_chalit_house else "-",
            "Nakshatra": r.nakshatra,
            "Pada": r.pada,
            "Dispozitor": r.sign_lord,
            "Dostojanstvo": r.dignity,
            "Vladar kuće": r.target_house_lord,
            "Odnos s vladarom kuće": r.target_house_lord_relation,
        } for r in rows]
        st.dataframe(table, use_container_width=True, hide_index=True, height=full_table_height(table))

    st.subheader("Uzajamni (ponavljajući) obrasci")
    if mutual_notes:
        for n in mutual_notes:
            st.write(f"- {n}")
    else:
        st.write("_Nije pronađen izravan uzajamni obrazac istog planeta u oba smjera._")


def _render_drishti(person_a, person_b, drishti_a_to_b, drishti_b_to_a):
    st.caption(
        "Klasični Parashari Graha Drishti (BPHS): svih 7 grahe baca puni aspekt na 7. kuću od "
        "sebe; Mars dodatno na 4./8., Jupiter na 5./9., Saturn na 3./10. Rahu/Ketu prema postavci "
        "u tabu 'Postavke' (core/aspects.py se NE mijenja - vidi core/synastry/graha_drishti.py)."
    )

    for title, contacts in (
        (f"{person_a.name} → {person_b.name}", drishti_a_to_b),
        (f"{person_b.name} → {person_a.name}", drishti_b_to_a),
    ):
        st.subheader(title)
        if not contacts:
            st.write("_Nema aktivnih Graha Drishti kontakata._")
            continue
        table = [{
            "Iz (planet)": c.from_planet,
            "U (planet/točka)": c.to_planet,
            "Udaljenost (kuća)": c.house_distance,
            "Snaga": c.strength_label,
            "Vladar kuća (izvor, vlastita karta)": ", ".join(f"{h}." for h in c.from_planet_houses_own_chart) or "-",
            "Kratko tumačenje": c.short_interpretation,
        } for c in contacts]
        st.dataframe(table, use_container_width=True, hide_index=True, height=full_table_height(table))
        with st.expander(f"Detaljna tumačenja ({title})"):
            for c in contacts:
                st.write(f"**{c.from_planet} → {c.to_planet}**")
                st.caption(c.detailed_interpretation)


def _render_conjunctions(conjunctions):
    st.caption(
        "Stupanjske konjunkcije (apsolutna dužina, orbisi iz taba 'Postavke') - odvojeni sloj "
        "od Graha Drishtija. Ispravno hvataju konjunkcije preko granice znaka."
    )
    if not conjunctions:
        st.write("_Nema konjunkcija unutar konfiguriranih orbisa._")
        return
    table = [{
        "Osoba A": c.person_a_object,
        "Osoba B": c.person_b_object,
        "Znak": c.sign,
        "Razmak (°)": c.degree_distance,
        "Egzaktna (≤1°)": "Da" if c.is_exact else "Ne",
        "Ista nakšatra": "Da" if c.same_nakshatra else "Ne",
        "Ista pada": "Da" if c.same_pada else "Ne",
        "Posebne oznake": ", ".join(c.special_flags) or "-",
    } for c in conjunctions]
    st.dataframe(table, use_container_width=True, hide_index=True, height=full_table_height(table))
    with st.expander("Detaljna tumačenja"):
        for c in conjunctions:
            st.write(f"**{c.person_a_object} (A) — {c.person_b_object} (B)**")
            st.caption(c.detailed_interpretation)


def _render_nakshatra(person_a, person_b, result):
    st.caption(
        "Usporedba nakšatre/pade/vladara/devate/Gane/Yonija/Nadija za Mjesec, Ascendent, Veneru, "
        "Mars, Sunce, vladara 7. kuće i Darakaraku obje osobe."
    )

    for person_label, person, profiles in ((person_a.name, person_a, result.profiles_a), (person_b.name, person_b, result.profiles_b)):
        st.subheader(person_label)
        table = [{
            "Točka": prof.point_label,
            "Planet": prof.planet_or_point,
            "Nakshatra": prof.nakshatra,
            "Pada": prof.pada,
            "Vladar": prof.nakshatra_lord,
            "Devata": prof.devata,
            "Gana": prof.gana,
            "Yoni": f"{prof.yoni} ({prof.yoni_gender})",
            "Nadi": prof.nadi,
            "D9 znak pade": prof.navamsha_sign,
            "Element pade": prof.pada_element,
        } for prof in profiles.values()]
        st.dataframe(table, use_container_width=True, hide_index=True, height=full_table_height(table))

    st.subheader("Unakrsne veze")
    if result.cross_links:
        for link in result.cross_links:
            st.write(f"- **{link.source_label} — {link.target_label}** ({link.relation_type}): {link.detail}")
    else:
        st.write("_Nema pronađenih izravnih veza (iste nakšatre ili vladara) unutar ovog izbora točaka._")

    st.subheader("Ponovljeni obrasci (ista nakšatra kroz više točaka)")
    if result.repeated_themes:
        for theme in result.repeated_themes:
            st.write(f"- **{theme.nakshatra}**: {', '.join(theme.points_involved)} - {theme.note}")
    else:
        st.write("_Nije pronađena nakšatra koja se ponavlja kroz više ključnih točaka._")

    st.subheader("Graf odnosa vladara nakšatri")
    st.caption(
        "Tablični prikaz bridova (A→B veze preko vladara nakšatre) - crtani dijagram dolazi u "
        "Fazi 3 (grafički prikaz)."
    )
    if result.lord_graph_edges:
        edge_table = [{"Iz": e[0], "U": e[1], "Vrsta": e[2]} for e in result.lord_graph_edges]
        st.dataframe(edge_table, use_container_width=True, hide_index=True, height=full_table_height(edge_table))
    else:
        st.write("_Nema pronađenih veza preko vladara nakšatri unutar ovog izbora točaka._")


def _render_ashtakoota(ashtakoota_result, kuja_comparison):
    st.subheader("Ashtakoota (Guna Milan) - Mjesečeva kompatibilnost")
    st.caption(
        f"Nakšatra Mjeseca: A = {ashtakoota_result.person_a_moon_nakshatra}, "
        f"B = {ashtakoota_result.person_b_moon_nakshatra}."
    )
    table = [{
        "Kuta": k.name, "Bodovi": k.points, "Maksimum": k.max_points,
        "Pravilo": k.rule_used, "Tumačenje": k.interpretation, "Ograničenje": k.limitation,
    } for k in ashtakoota_result.kutas]
    st.dataframe(table, use_container_width=True, hide_index=True, height=full_table_height(table))
    st.metric("Ukupno", f"{ashtakoota_result.total_points:.1f} / {ashtakoota_result.max_points:.0f}")
    st.warning(
        "36 bodova NIJE konačna presuda o odnosu - ovo je samo JEDAN tradicionalni sloj (temeljen "
        "isključivo na Mjesecu), koji treba promatrati zajedno s ostalim tabovima."
    )

    if ashtakoota_result.cancellations:
        st.subheader("Tradicionalne iznimke/poništenja")
        for c in ashtakoota_result.cancellations:
            st.write(f"- {c}")

    st.markdown("---")
    st.subheader("Kuja (Mangal) Dosha")
    st.caption(
        "Marsova afflikcija gledano od Ascendenta, Mjeseca i Venere - stupnjevana procjena "
        "(nema/blaga/umjerena/jaka), ne binarna oznaka. Kuće se mogu podesiti u tabu 'Postavke'."
    )
    for assessment in (kuja_comparison.person_a, kuja_comparison.person_b):
        st.write(f"**Osoba {assessment.person_label}: {assessment.severity}** (orijentacijski indeks: {assessment.severity_score:.0f}/100)")
        houses_str = ", ".join(f"{base}: {house}." for base, house in assessment.houses_involved.items())
        st.caption(f"Kuće Marsa (od Ascendenta/Mjeseca/Venere): {houses_str}")
        if assessment.reasons:
            for r in assessment.reasons:
                st.write(f"- {r}")
        if assessment.possible_cancellations:
            st.write("_Moguća poništenja:_")
            for c in assessment.possible_cancellations:
                st.write(f"  - {c}")
    st.info(kuja_comparison.balancing_note)


def _render_significators(person_a, person_b, result):
    st.caption(
        "Ključni signifikatori partnerstva: 7. kuća, Venera, Mars, Jupiter, Mjesec, "
        "Atmakaraka/Darakaraka, Arudha Lagna, Upapada Lagna (UL) i Darapada (A7)."
    )
    for label, person, profile in ((person_a.name, person_a, result.profile_a), (person_b.name, person_b, result.profile_b)):
        st.subheader(label)
        rows = [
            {"Signifikator": "7. kuća (znak)", "Vrijednost": profile.seventh_house_sign},
            {"Signifikator": "Planeti u 7. kući", "Vrijednost": ", ".join(profile.seventh_house_planets) or "-"},
            {"Signifikator": "Vladar 7. kuće", "Vrijednost": f"{profile.seventh_lord} ({profile.seventh_lord_sign}, {profile.seventh_lord_house}. kuća)"},
            {"Signifikator": "Venera", "Vrijednost": f"{profile.venus_sign}, {profile.venus_house}. kuća"},
            {"Signifikator": "Mars", "Vrijednost": f"{profile.mars_sign}, {profile.mars_house}. kuća"},
            {"Signifikator": "Jupiter", "Vrijednost": f"{profile.jupiter_sign}, {profile.jupiter_house}. kuća"},
            {"Signifikator": "Mjesec", "Vrijednost": f"{profile.moon_sign}, {profile.moon_house}. kuća"},
            {"Signifikator": "Atmakaraka (AK)", "Vrijednost": profile.atmakaraka_planet},
            {"Signifikator": "Darakaraka (DK)", "Vrijednost": profile.darakaraka_planet},
            {"Signifikator": "Arudha Lagna (AL)", "Vrijednost": profile.arudha_lagna_sign},
            {"Signifikator": "Upapada Lagna (UL)", "Vrijednost": f"{profile.upapada_lagna_sign}, {profile.upapada_house}. kuća"},
            {"Signifikator": "Vladar UL", "Vrijednost": profile.upapada_lord},
            {"Signifikator": "Planeti na UL", "Vrijednost": ", ".join(profile.upapada_planets) or "-"},
            {"Signifikator": "2. od UL", "Vrijednost": profile.second_from_upapada_sign},
            {"Signifikator": "8. od UL", "Vrijednost": profile.eighth_from_upapada_sign},
            {"Signifikator": "Darapada (A7)", "Vrijednost": f"{profile.darapada_sign}, {profile.darapada_house}. kuća"},
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True, height=full_table_height(rows))

    st.subheader("Unakrsne veze")
    if result.cross_notes:
        for note in result.cross_notes:
            st.write(f"- {note}")
    else:
        st.write("_Nema pronađenih posebnih unakrsnih veza unutar ovog izbora._")


def _render_navamsha(person_a, person_b, result):
    st.caption(
        "D9 (Navamsha) sinastrija - NIJE neovisna natalna karta, nego dodatni sloj koji dopunjuje D1. "
        "Ponovljeni obrasci (isti par planeta povezan i u D1 i u D9) posebno su označeni ispod jer "
        "predstavljaju jaču potvrdu nego izoliran nalaz u samo jednoj karti."
    )
    st.write(f"**Ascendent D9:** A = {result.ascendant_sign_a}, B = {result.ascendant_sign_b}")
    st.write(
        f"**7. kuća D9:** A = {result.seventh_sign_a} (vladar {result.seventh_lord_a}), "
        f"B = {result.seventh_sign_b} (vladar {result.seventh_lord_b})"
    )

    st.subheader("Ključne točke u D9")
    key_table = []
    for label, person, points in ((person_a.name, person_a, result.key_points_a), (person_b.name, person_b, result.key_points_b)):
        for point_name, sign in points.items():
            key_table.append({"Osoba": label, "Točka": point_name, "D9 znak": sign})
    st.dataframe(key_table, use_container_width=True, hide_index=True, height=full_table_height(key_table))

    for title, rows in (
        (f"Planeti osobe {person_a.name} u D9 kući osobe {person_b.name}", result.overlay_a_to_b),
        (f"Planeti osobe {person_b.name} u D9 kući osobe {person_a.name}", result.overlay_b_to_a),
    ):
        st.subheader(title)
        table = [{
            "Planet": r.planet + (" ★" if r.is_significant_house else ""),
            "D9 znak": r.varga_sign, "Kuća": r.house,
        } for r in rows]
        st.dataframe(table, use_container_width=True, hide_index=True, height=full_table_height(table))

    st.subheader("Graha Drishti u D9")
    for title, contacts in (
        (f"{person_a.name} → {person_b.name}", result.drishti_a_to_b),
        (f"{person_b.name} → {person_a.name}", result.drishti_b_to_a),
    ):
        if not contacts:
            continue
        st.write(f"**{title}**")
        table = [{"Iz": c.from_planet, "U": c.to_planet, "Kuća": c.house_distance, "Snaga": c.strength_label} for c in contacts]
        st.dataframe(table, use_container_width=True, hide_index=True, height=full_table_height(table))

    st.subheader("Isti D9 znak (varga-ekvivalent konjunkcije)")
    st.caption(
        "D9 stupnjevi nisu linearno usporedivi s D1 stupnjevima - umjesto orba, ovdje se koristi "
        "'isti D9 znak' kao ekvivalent konjunkcije."
    )
    if result.same_sign_contacts:
        table = [{"Osoba A": c.person_a_object, "Osoba B": c.person_b_object, "D9 znak": c.varga_sign} for c in result.same_sign_contacts]
        st.dataframe(table, use_container_width=True, hide_index=True, height=full_table_height(table))
    else:
        st.write("_Nema kontakata u istom D9 znaku unutar promatranih točaka._")

    st.subheader("Ponovljeni obrasci (D1 ↔ D9)")
    if result.repeated_pattern_notes:
        for note in result.repeated_pattern_notes:
            st.write(f"- {note}")
    else:
        st.write("_Nije pronađen par planeta povezan istovremeno u D1 i D9._")


def _render_scoring(result):
    st.caption(
        "Kategorijsko bodovanje (0-100, polazno 50) izvedeno iz već izračunatih kontakata "
        "(Graha Drishti, konjunkcije, kućni overlay, Ashtakoota, Kuja Dosha, nakšatre, D9 ponovljeni "
        "obrasci). Svaka kategorija je NEZAVISNA procjena - ne zbraja se u jedan 'ukupni' rezultat."
    )
    st.warning(
        "Ovo NIJE znanstvena vjerojatnost niti presuda o odnosu - riječ je o transparentnom, "
        "konfigurabilnom zbroju prepoznatih klasičnih pokazatelja (vidi core/synastry/scoring_config.py)."
    )

    chart_data = {category: result.categories[category].score for category in CATEGORY_NAMES}
    st.bar_chart(chart_data, horizontal=True, height=380, x_label="%")

    cols = st.columns(3)
    for i, category in enumerate(CATEGORY_NAMES):
        cat_score = result.categories[category]
        with cols[i % 3]:
            st.metric(category, f"{cat_score.score:.0f}%")

    if result.not_available:
        st.info(f"Nije dostupno (dolazi u Fazi 4): {', '.join(result.not_available)}")

    st.markdown("---")
    st.subheader("Detaljan raspis po kategoriji")
    category_choice = st.selectbox("Kategorija", CATEGORY_NAMES, key="synastry_scoring_category_select")
    cat_score = result.categories[category_choice]
    st.write(f"**{cat_score.category}: {cat_score.score:.0f}%**")
    st.caption(cat_score.method)
    if cat_score.factors:
        table = [{
            "Faktor": f.description, "Vrsta": f.polarity, "Težina": f.weight, "Doprinos": round(f.contribution, 1),
        } for f in cat_score.factors]
        st.dataframe(table, use_container_width=True, hide_index=True, height=full_table_height(table))
    else:
        st.write("_Nema pronađenih faktora za ovu kategoriju unutar trenutačnih postavki - rezultat je neutralan (50)._")
    if cat_score.excluded_duplicates:
        with st.expander("Isključeni duplikati (spriječeno dvostruko brojanje)"):
            for d in cat_score.excluded_duplicates:
                st.write(f"- {d}")


def _render_predictive(person_a, person_b, ctx_a, ctx_b, natal_links,
                        seventh_lord_a, seventh_lord_b, darakaraka_a, darakaraka_b, asc_lord_a, asc_lord_b, config):
    st.caption(
        "Prediktivna sinastrija za JEDAN odabrani datum: tranziti prema objema kartama, "
        "aktivacija natalne sinastrije tranzitom, dvostruki tranzit Jupitera/Saturna, "
        "Vimshottari Dasha aktivacije i Varshaphala/Mudda Dasha aktivacije."
    )
    target_date = st.date_input("Datum", value=date.today(), key="synastry_predictive_date")
    at_dt = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc).replace(hour=12)

    snapshot = compute_predictive_snapshot(
        ctx_a, ctx_b, at_dt, natal_links,
        seventh_lord_a, seventh_lord_b, darakaraka_a, darakaraka_b, asc_lord_a, asc_lord_b, config,
    )

    st.subheader("Tranziti prema objema kartama")
    for label, person, rows in ((person_a.name, person_a, snapshot.transits_a), (person_b.name, person_b, snapshot.transits_b)):
        st.write(f"**{label}**")
        table = [{
            "Planet": r.planet + (" 🐢" if r.is_slow else ""),
            "Znak": r.sign,
            "Kuća (od Asc)": r.house_from_ascendant,
            "Kuća (od Mjeseca)": r.house_from_moon,
            "Kuća (od UL)": r.house_from_upapada,
            "Nakshatra": r.nakshatra, "Pada": r.pada,
            "Dispozitor": r.dispositor,
            "Retrogradan": "Da" if r.is_retrograde else "Ne",
        } for r in rows.values()]
        st.dataframe(table, use_container_width=True, hide_index=True, height=full_table_height(table))
    st.caption("🐢 = spori tranzit (Saturn/Jupiter/Rahu/Ketu) - veća težina od brzih tranzita u aktivacijama ispod.")

    st.markdown("---")
    st.subheader("Aktivacija natalne sinastrije tranzitom")
    st.caption(
        "Prepoznavanje kad tranzit aktivira VEĆ POSTOJEĆU natalnu vezu (konjunkcija, Graha Drishti, "
        "isti znak/nakšatra, tranzit vladara nakšatre/dispozitora veze, aktivacija u D9)."
    )
    if snapshot.activations:
        table = [{
            "Tranzitni planet": a.transit_planet + (" 🐢" if a.is_slow_planet else ""),
            "Veza": f"{a.link.person_a_object} — {a.link.person_b_object}",
            "Vrste aktivacije": ", ".join(a.activation_types),
            "Jačina": a.strength,
        } for a in snapshot.activations[:30]]
        st.dataframe(table, use_container_width=True, hide_index=True, height=full_table_height(table))
        with st.expander(f"Detaljna tumačenja (prikazano {min(30, len(snapshot.activations))} od {len(snapshot.activations)})"):
            for a in snapshot.activations[:30]:
                st.write(f"- {a.interpretation}")
    else:
        st.write("_Nema aktivacija natalne sinastrije za ovaj datum unutar trenutačnih postavki._")

    st.markdown("---")
    st.subheader("Dvostruki tranzit Jupitera i Saturna")
    dt = snapshot.double_transit
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**{person_a.name}**")
        st.write(f"Jupiter aktivira: {', '.join(dt.jupiter_hits_a) or '-'}")
        st.write(f"Saturn aktivira: {', '.join(dt.saturn_hits_a) or '-'}")
    with col2:
        st.write(f"**{person_b.name}**")
        st.write(f"Jupiter aktivira: {', '.join(dt.jupiter_hits_b) or '-'}")
        st.write(f"Saturn aktivira: {', '.join(dt.saturn_hits_b) or '-'}")
    if dt.simultaneous_both_charts:
        st.success(dt.note)
    else:
        st.info(dt.note)

    st.markdown("---")
    st.subheader("Vimshottari Dasha aktivacije")
    dasha = snapshot.dasha_result
    for label, profile in ((person_a.name, dasha.profile_a), (person_b.name, dasha.profile_b)):
        st.write(
            f"**{label}:** Maha {profile.maha_lord} ({profile.maha_start} — {profile.maha_end}) → "
            f"Antar {profile.antar_lord} ({profile.antar_start} — {profile.antar_end}) → Pratyantar {profile.pratyantar_lord}"
        )
        st.caption(
            f"Maha vladar u vlastitoj karti: {profile.maha_lord_natal_sign}, {profile.maha_lord_natal_nakshatra}, "
            f"D9 {profile.maha_lord_d9_sign}, vlada kućama {', '.join(str(h) + '.' for h in profile.maha_houses_ruled) or '-'}."
        )
        st.caption(
            f"Odnos prema 7. kući: {profile.relation_to_seventh}. Odnos prema Veneri: {profile.relation_to_venus}. "
            f"Odnos prema Darakaraki: {profile.relation_to_darakaraka}. Odnos prema UL: {profile.relation_to_upapada}."
        )
    st.subheader("Uzajamne dasha aktivacije")
    if dasha.mutual_notes:
        for n in dasha.mutual_notes:
            st.write(f"- {n}")
    else:
        st.write("_Nema prepoznatih uzajamnih dasha aktivacija za ovaj par trenutačnih dasha vladara._")

    st.markdown("---")
    st.subheader("Varshaphala (solarni povratak) / Mudda Dasha aktivacije")
    st.warning(
        "Metoda: Tajika Ithasala/Isarapha (Varshaphala/Tajika sustav) - NE Parashari Graha Drishti. "
        "Ova dva sustava aspekata namjerno se ovdje NE miješaju (vidi core/synastry/varshaphala_activations.py)."
    )
    if not (person_a.time_confirmed and person_b.time_confirmed):
        st.info("Varshaphala zahtijeva potvrđeno vrijeme rođenja za smislen Varsha Lagna izračun kod obje osobe.")
    col_year_a, col_year_b = st.columns(2)
    with col_year_a:
        target_year_a = st.number_input(
            f"Godina solarnog povratka - {person_a.name}", min_value=1900, max_value=2100,
            value=target_date.year, step=1, key="synastry_varshaphala_year_a",
        )
    with col_year_b:
        target_year_b = st.number_input(
            f"Godina solarnog povratka - {person_b.name}", min_value=1900, max_value=2100,
            value=target_date.year, step=1, key="synastry_varshaphala_year_b",
        )

    varshaphala_result = compute_varshaphala_synastry(
        person_a, ctx_a, person_b, ctx_b, int(target_year_a), int(target_year_b), at_dt,
        seventh_lord_a, seventh_lord_b, natal_links,
    )

    col_vp_a, col_vp_b = st.columns(2)
    for col, label, profile in (
        (col_vp_a, person_a.name, varshaphala_result.profile_a),
        (col_vp_b, person_b.name, varshaphala_result.profile_b),
    ):
        with col:
            st.write(f"**{label} ({profile.target_year}.)**")
            st.write(f"Varsha Lagna: {profile.ascendant_sign}")
            st.write(f"Muntha: {profile.muntha_sign} (vladar {profile.muntha_lord})")
            st.write(f"Varsheshwara: {profile.varsheshwara_planet or '-'}")
            st.write(f"Godišnja 7. kuća: {profile.seventh_sign} (vladar {profile.seventh_lord})")
            st.write(f"Venera: {profile.venus_house}. kuća, Mjesec: {profile.moon_house}. kuća")
            st.write(f"Saturn: {profile.saturn_house}. kuća, Jupiter: {profile.jupiter_house}. kuća")
            st.write(f"Aktivni Mudda Dasha vladar: {profile.active_mudda_dasha_lord}")
            st.caption(
                f"Tajika Ithasala parova: {profile.tajika_ithasala_count}, "
                f"Isarapha parova: {profile.tajika_isarapha_count}."
            )

    st.subheader("Preklapanja s osjetljivim točkama")
    if varshaphala_result.b_planets_on_a_sensitive_points or varshaphala_result.a_planets_on_b_sensitive_points:
        for n in varshaphala_result.b_planets_on_a_sensitive_points + varshaphala_result.a_planets_on_b_sensitive_points:
            st.write(f"- {n}")
    else:
        st.write("_Nema natalnih planeta druge osobe na osjetljivim točkama (Varsha Lagna/Muntha/7. kuća/Varsha AL) ove godine._")

    st.subheader("Mudda Dasha aktivira natalnu sinastrijsku vezu")
    mudda_notes = varshaphala_result.mudda_dasha_activates_natal_link
    if mudda_notes:
        st.caption(
            "Kad je Mudda Dasha vladar planet koji sudjeluje u puno kontakata (npr. Venera), broj "
            "pogodaka lako naraste - svaki je zaseban par (smjer A→B i B→A se NE preklapaju, riječ "
            "je o dvije različite astronomske veze)."
        )
        for n in mudda_notes[:20]:
            st.write(f"- {n}")
        if len(mudda_notes) > 20:
            with st.expander(f"Prikaži svih {len(mudda_notes)} aktivacija"):
                for n in mudda_notes:
                    st.write(f"- {n}")
    else:
        st.write("_Trenutačni Mudda Dasha vladar niti jedne osobe ne odgovara nijednoj natalnoj sinastrijskoj vezi._")

    for n in varshaphala_result.notes:
        st.caption(n)


_TIMELINE_STEP_OPTIONS = {"Dnevno": 1, "Tjedno": 7, "Mjesečno": 30}
_TIMELINE_THEMES = [
    "Emocionalne teme", "Privlačnost", "Komunikacija", "Stabilnost", "Konflikt",
    "Susret/približavanje", "Formalizacija odnosa", "Udaljavanje/završavanje ciklusa",
]


def _render_timeline(ctx_a, ctx_b, natal_links,
                      seventh_lord_a, seventh_lord_b, darakaraka_a, darakaraka_b, asc_lord_a, asc_lord_b, config):
    st.caption(
        "Vremenska crta prikazuje ukupnu jačinu aktivacije natalne sinastrije kroz raspon datuma. "
        "Nazivi filtara predstavljaju astrološke TEME, ne siguran događaj."
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("Od datuma", value=date.today(), key="synastry_timeline_start")
    with col2:
        end_date = st.date_input("Do datuma", value=date.today() + timedelta(days=90), key="synastry_timeline_end")
    with col3:
        step_label = st.selectbox("Korak", list(_TIMELINE_STEP_OPTIONS.keys()), key="synastry_timeline_step")
    step_days = _TIMELINE_STEP_OPTIONS[step_label]

    if end_date < start_date:
        st.warning("'Do datuma' mora biti nakon 'Od datuma'.")
        return

    num_points = (end_date - start_date).days // step_days + 1
    if num_points > 800:
        st.warning(
            f"Odabrani raspon i korak daju {num_points} točaka - to može potrajati. "
            "Suzi raspon ili odaberi rjeđi korak, ili nastavi ako si siguran/na."
        )

    theme_filter = st.multiselect("Filtriraj po temi (prazno = sve)", _TIMELINE_THEMES, key="synastry_timeline_theme_filter")

    # VAŽNO: rezultat se sprema u session_state uz "otisak prsta" (fingerprint)
    # svih ulaza KOJI STVARNO MIJENJAJU izračun (osobe, raspon, korak,
    # postavke) - PROMJENA SAMOG FILTRA TEME NIJE dio otiska. Streamlit
    # st.button() vraća True samo na točnom reruna klika, pa bi bez ovog
    # keširanja svaka promjena filtra (drugi rerun) izgubila rezultat i
    # tražila ponovni klik - ovo je bio poznati nedostatak performansi
    # ranije faze, sada ispravljen.
    fingerprint = (
        ctx_a.person_name, ctx_b.person_name, start_date.isoformat(), end_date.isoformat(), step_days,
        tuple(sorted(config.settings_summary().items())),
    )
    compute_clicked = st.button("Izračunaj vremensku crtu", key="synastry_timeline_compute")
    cache = st.session_state.get("synastry_timeline_cache")

    if compute_clicked:
        progress_bar = st.progress(0.0)
        raw_points = compute_timeline(
            ctx_a, ctx_b, start_date, end_date, step_days, natal_links,
            seventh_lord_a, seventh_lord_b, darakaraka_a, darakaraka_b, asc_lord_a, asc_lord_b, config,
            progress_callback=progress_bar.progress,
        )
        progress_bar.progress(1.0)
        cache = {"fingerprint": fingerprint, "points": raw_points}
        st.session_state.synastry_timeline_cache = cache

    if not cache or cache["fingerprint"] != fingerprint:
        st.info(
            "Klikni 'Izračunaj vremensku crtu' da pokreneš izračun (nije automatski zbog trajanja za veće "
            "raspone). Nakon prvog izračuna, promjena filtra teme NE zahtijeva ponovni klik - samo promjena "
            "datuma/koraka/postavki to zahtijeva."
        )
        return

    points = cache["points"]
    if theme_filter:
        points = [p for p in points if any(t in p.themes for t in theme_filter)]

    if not points:
        st.write("_Nema točaka koje odgovaraju odabranom filteru._")
        return

    # ISPRAVAK: kad je filtar teme aktivan, jačina prikazana na grafu i u
    # tablici mora biti SAMO zbroj aktivacija KOJE PRIPADAJU odabranoj
    # temi/temama - prije se uvijek prikazivala UKUPNA dnevna jačina (svih
    # tema zajedno), pa je filtar mijenjao samo KOJI dani se prikazuju, ne
    # i same vrijednosti, zato je graf izgledao "isti" bez obzira na odabranu
    # temu. Graf se sad i prikazuje u postocima (100% = vrhunac unutar
    # trenutačnog raspona/filtra), umjesto sirovog, neomeđenog zbroja.
    def _relevant_strength(p):
        if not theme_filter:
            return p.total_strength
        return round(sum(s for _, s, themes in p.activation_strengths if any(t in theme_filter for t in themes)), 2)

    raw_values = {p.date_label: _relevant_strength(p) for p in points}
    max_val = max(raw_values.values()) if raw_values else 0.0
    chart_data = {
        label: round(100.0 * v / max_val, 1) if max_val > 0 else 0.0
        for label, v in raw_values.items()
    }
    st.line_chart(chart_data, y_label="Relativna jačina (%, 100% = vrhunac u odabranom rasponu/temi)")

    table = [{
        "Datum": p.date_label, "Jačina (odabrana tema)" if theme_filter else "Ukupna jačina": raw_values[p.date_label],
        "Aktivni spori tranziti": ", ".join(p.active_slow_transits) or "-",
        "Aktivni dasha vladari": ", ".join(p.active_dasha_lords) or "-",
        "Teme": ", ".join(p.themes) or "-",
    } for p in points]
    st.dataframe(table, use_container_width=True, hide_index=True, height=min(full_table_height(table), 600))
    st.download_button(
        "Preuzmi vremensku crtu (.csv)", build_csv_timeline(points),
        file_name="sinastrija_vremenska_crta.csv", mime="text/csv",
        key="synastry_timeline_csv_download",
    )

    peak = max(points, key=lambda p: raw_values[p.date_label])
    st.subheader(f"Vrhunac: {peak.date_label} (jačina {raw_values[peak.date_label]})")
    if peak.top_notes:
        for n in peak.top_notes:
            st.write(f"- {n}")
    else:
        st.write("_Nema zabilježenih aktivacija na dan vrhunca._")

    st.markdown("---")
    st.subheader("Mjesečevi (dnevni) okidači")
    st.caption(
        "Mjesec djeluje kao KRATKOTRAJNI OKIDAČ, ne kao samostalan dokaz velikog događaja - "
        "prikazani su samo dani unutar odabranog raspona koji imaju barem jednu zabilježenu "
        "Mjesečevu aktivaciju (aktivacija natalne veze, isti znak/nakšatra ključne točke, ili "
        "poklapanje s barem dva aktivna spora tranzita). Ovo se RAČUNA DAN PO DAN (Mjesec je brz) "
        "neovisno o gornjem koraku vremenske crte, pa za dulje raspone može potrajati."
    )
    total_range_days = (end_date - start_date).days
    run_moon_section = True
    if total_range_days > 180:
        run_moon_section = st.checkbox(
            f"Izračunaj Mjesečeve okidače za svih {total_range_days} dana (može potrajati)",
            value=False, key="synastry_moon_triggers_confirm",
        )
    if run_moon_section:
        moon_progress_bar = st.progress(0.0)
        moon_days = compute_moon_trigger_days_over_range(
            ctx_a, ctx_b, natal_links, start_date, end_date,
            seventh_lord_a, seventh_lord_b, darakaraka_a, darakaraka_b, config,
            progress_callback=moon_progress_bar.progress,
        )
        moon_progress_bar.progress(1.0)
        if moon_days:
            # NAPOMENA: namjerno JEDAN selectbox + prikaz jednog dana, umjesto
            # zasebnog st.expander po danu - Streamlit drži SADRŽAJ SVIH tabova
            # mountan u DOM-u i dok korisnik gleda drugi tab, pa bi npr. 90
            # zasebnih expandera nepotrebno napuhalo cijelu stranicu (usporilo
            # i taj i sve ostale tabove) za samo marginalnu korist naspram
            # jednog odabira dana.
            day_table = [{"Datum": d.date_label, "Broj bilježenih okidača": len(d.notes)} for d in moon_days]
            st.dataframe(day_table, use_container_width=True, hide_index=True, height=min(full_table_height(day_table), 300))
            day_by_label = {d.date_label: d for d in moon_days}
            chosen_day_label = st.selectbox(
                "Prikaži detalje za dan", list(day_by_label.keys()), key="synastry_moon_trigger_day_select",
            )
            chosen_day = day_by_label[chosen_day_label]
            st.write(f"**{chosen_day.date_label}**")
            for n in chosen_day.notes:
                st.write(f"- {n}")
        else:
            st.write("_Nema dana s Mjesečevom aktivacijom unutar odabranog raspona._")
    else:
        st.info("Označi kućicu iznad da pokreneš izračun Mjesečevih okidača za ovaj (dulji) raspon.")


def _render_report(person_a, person_b, ctx_a, ctx_b, relationship_type, config,
                    overlay_a_to_b, overlay_b_to_a, mutual_notes, drishti_a_to_b, drishti_b_to_a, conjunctions,
                    nakshatra_result=None, ashtakoota_result=None, kuja_comparison=None, significators_result=None,
                    navamsha_result=None, score_result=None, relationship_profile=None):
    report_text = build_basic_report(
        person_a.name, person_a.birth_date, person_b.name, person_b.birth_date,
        ctx_a, ctx_b, relationship_type, config,
        overlay_a_to_b, overlay_b_to_a, mutual_notes,
        drishti_a_to_b, drishti_b_to_a, conjunctions,
        nakshatra_result, ashtakoota_result, kuja_comparison, significators_result,
        navamsha_result, score_result, relationship_profile,
    )
    st.text_area("Osnovni tekstualni izvještaj", report_text, height=600)

    file_stem = f"sinastrija_{person_a.name}_{person_b.name}".replace(" ", "_")
    col_txt, col_pdf, col_json, col_csv = st.columns(4)
    with col_txt:
        st.download_button(
            "Preuzmi izvještaj (.txt)", report_text,
            file_name=f"{file_stem}.txt", key="synastry_export_txt",
        )
    with col_pdf:
        pdf_bytes = build_pdf_report(report_text, f"Sinastrija - {person_a.name} i {person_b.name}")
        st.download_button(
            "Preuzmi izvještaj (.pdf)", pdf_bytes,
            file_name=f"{file_stem}.pdf", mime="application/pdf", key="synastry_export_pdf",
        )
    with col_json:
        json_text = build_json_export(
            person_a, person_b, relationship_type, config,
            overlay_a_to_b, overlay_b_to_a, drishti_a_to_b, drishti_b_to_a, conjunctions,
            nakshatra_result, ashtakoota_result, kuja_comparison, significators_result,
            navamsha_result, score_result,
        )
        st.download_button(
            "Preuzmi podatke (.json)", json_text,
            file_name=f"{file_stem}.json", mime="application/json", key="synastry_export_json",
        )
    with col_csv:
        csv_text = build_csv_contacts(drishti_a_to_b, drishti_b_to_a, conjunctions)
        st.download_button(
            "Preuzmi kontakte (.csv)", csv_text,
            file_name=f"{file_stem}_kontakti.csv", mime="text/csv", key="synastry_export_csv",
        )

    st.caption(
        "JSON izvoz sadrži SVE strukturirane rezultate (postavke, ulaz, sve tablice kontakata, "
        "bodovanje) - pogodno za daljnju obradu ili arhiviranje. CSV izvoz kontakata sadrži Graha "
        "Drishti i konjunkcije u tabličnom obliku. Vremenska crta ima svoj CSV izvoz u tabu "
        "'Vremenska crta' (podaci ovise o odabranom rasponu datuma i nisu dio ovog izvještaja). "
        "PDF preoblikuje isti tekstualni izvještaj (isti sadržaj, ne duplicira izračune)."
    )


def _render_settings():
    st.caption(
        "Sve postavke ovdje su konfigurabilne i školski sporne točke - zadane vrijednosti su "
        "jasno navedene, promjena ovdje se odmah odražava na sve ostale tabove."
    )

    st.subheader("Rahu/Ketu Graha Drishti između karata")
    current_label = _NODE_MODE_LABELS[st.session_state.synastry_node_mode]
    chosen_label = st.radio(
        "Način tretiranja aspekata čvorova",
        list(_NODE_MODE_LABELS.values()),
        index=list(_NODE_MODE_LABELS.values()).index(current_label),
        key="synastry_node_mode_radio",
    )
    st.session_state.synastry_node_mode = _NODE_MODE_BY_LABEL[chosen_label]
    st.caption(
        "Zadano: 'Samo 7. aspekt' - najbliže izvornom BPHS-u (koji Rahu/Ketu uopće ne "
        "spominje u poglavlju o Drishtiju, ali svih 7 klasičnih grahe baca 7. aspekt pa se "
        "to smatra univerzalnim). Vidi core/synastry/config.py za puno obrazloženje."
    )

    st.subheader("Orbisi za konjunkcije (stupnjevi)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.number_input("Sunce / Mjesec", min_value=0.0, max_value=15.0, step=0.5, key="synastry_orb_luminaries")
        st.number_input("Ostali osobni planeti (Mars/Merkur/Venera)", min_value=0.0, max_value=15.0, step=0.5, key="synastry_orb_personal")
    with col2:
        st.number_input("Jupiter / Saturn", min_value=0.0, max_value=15.0, step=0.5, key="synastry_orb_jup_sat")
        st.number_input("Rahu / Ketu", min_value=0.0, max_value=15.0, step=0.5, key="synastry_orb_nodes")
    with col3:
        st.number_input("Osjetljive točke (Lagna/AL/UL/A7/BP)", min_value=0.0, max_value=15.0, step=0.5, key="synastry_orb_sensitive")

    st.subheader("Prikaz kuća")
    st.checkbox("Prikaži i Bhava Chalit kuću (uz Whole Sign)", key="synastry_bhava_chalit")

    st.markdown("---")
    st.subheader("Chara Karaka shema (Atmakaraka/Darakaraka)")
    karaka_labels = {"7_karaka": "7 Karaka (zadano, bez čvorova)", "8_karaka": "8 Karaka (uklj. Rahu)"}
    karaka_current = karaka_labels[st.session_state.synastry_karaka_scheme]
    karaka_chosen = st.radio(
        "Shema", list(karaka_labels.values()),
        index=list(karaka_labels.values()).index(karaka_current),
        key="synastry_karaka_scheme_radio",
    )
    st.session_state.synastry_karaka_scheme = {v: k for k, v in karaka_labels.items()}[karaka_chosen]
    st.caption("Vidi core/chara_karaka.py za puno obrazloženje razlike između shema.")

    st.markdown("---")
    st.subheader("Kuja (Mangal) Dosha - kuće koje se smatraju problematičnima")
    all_houses = list(range(1, 13))
    chosen_houses = st.multiselect(
        "Kuće (od Ascendenta/Mjeseca/Venere)", all_houses,
        default=sorted(st.session_state.synastry_kuja_houses),
        key="synastry_kuja_houses_select",
    )
    st.session_state.synastry_kuja_houses = set(chosen_houses)
    st.caption(
        "Zadano: 1, 2, 4, 7, 8, 12 (najšira, najčešće citirana verzija). Neke škole koriste samo "
        "2, 4, 7, 8 - suzi odabir ako želiš tu (tradicionalniju, užu) varijantu."
    )

    st.markdown("---")
    st.caption(
        "Zapadnjački stupanjski aspekti (sekstil/kvadrat/trigon/opozicija) kao dodatni, "
        "IZRIČITO opcionalni sloj NISU implementirani u ovoj fazi - konjunkcije (stupanjski "
        "orb) su već odvojeni sloj od klasičnog Graha Drishtija."
    )
