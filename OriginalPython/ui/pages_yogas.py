"""
Streamlit UI za Yoga Engine (core/yoga_engine/) - nova kartica "Yoge" u
natalnoj analizi (zahtjev #24). Čisto prezentacijski sloj - sva logika
detekcije yoga je u core/yoga_engine/, ovaj modul samo prikazuje već
izračunate core.yoga_engine.models.YogaResult objekte.
"""

import streamlit as st
from ui.colors import colored_dataframe
from ui.yoga_meanings import meaning_for, interpretation_note

from core.yoga_engine.context import ChartContext
from core.yoga_engine.registry import YOGA_REGISTRY, PENDING_REVIEW, run_all_yogas
from core.yoga_engine.models import YogaStatus
from ui.df_utils import full_table_height

_FILTERS = {
    "Sve": None,
    "Maha Purusha": lambda r: r.category == "Pancha Mahapurusha Yoga",
    "Raja": lambda r: r.category == "Raja Yoga",
    "Dhana": lambda r: r.category == "Dhana Yoga",
    "Chandra": lambda r: r.category == "Chandra Yoga",
    "Surya": lambda r: r.category == "Surya Yoga",
    "Nabhasa": lambda r: r.category.startswith("Nabhasa"),
    "Parivartana": lambda r: r.category == "Parivartana Yoga",
    "Viparita": lambda r: r.category == "Viparita Raja Yoga",
    "Neecha Bhanga": lambda r: r.category == "Neecha Bhanga",
    "Povoljne": lambda r: r.favorable is True,
    "Nepovoljne": lambda r: r.favorable is False,
    "Ostale": lambda r: r.category == "Ostale klasične yoge",
}

_STATUS_ICON = {
    YogaStatus.VERY_STRONG.value: "🟢🟢",
    YogaStatus.STRONG.value: "🟢",
    YogaStatus.MEDIUM.value: "🟡",
    YogaStatus.WEAK.value: "🟠",
    YogaStatus.HEAVILY_AFFLICTED.value: "🔴",
    YogaStatus.CANCELLED.value: "⚫",
}


def render_yogas_tab(chart: ChartContext) -> None:
    st.subheader("Yoge")
    st.caption("Yoge su tradicionalni astrološki obrasci. Opis pokazuje njihov potencijal; izražavanje ovisi o cijeloj karti, snazi planeta i razdobljima daša. Kuće se ovdje računaju iz D1 po znakovima (Whole Sign).")

    debug_mode = st.checkbox(
        "Yoga Debug način (prikaži i yoge koje NISU pronađene, s potpunim tehničkim tragom)",
        value=False,
    )

    all_results = run_all_yogas(chart)
    present_results = [r for r in all_results if r.present]

    n_active = sum(1 for r in present_results if r.status != YogaStatus.CANCELLED.value)
    n_weak = sum(1 for r in present_results if r.status in (YogaStatus.WEAK.value, YogaStatus.HEAVILY_AFFLICTED.value))
    n_cancelled = sum(1 for r in all_results if r.status == YogaStatus.CANCELLED.value)
    st.markdown(f"**Pronađeno: {n_active} aktivnih / {n_weak} oslabljenih / {n_cancelled} poništenih yoga**")

    filter_label = st.radio("Filter", list(_FILTERS.keys()), horizontal=True)
    filter_fn = _FILTERS[filter_label]

    shown = all_results if debug_mode else present_results
    if filter_fn:
        shown = [r for r in shown if filter_fn(r)]
    shown = sorted(shown, key=lambda r: (-r.present, -r.strength))

    if not shown:
        st.info("Nijedna yoga u ovom filteru nije pronađena u ovoj karti." if not debug_mode else "Nema rezultata za ovaj filter.")
    for r in shown:
        icon = _STATUS_ICON.get(r.status, "⚪" if r.present else "⬜")
        header = f"{icon} {r.name}" if r.present else f"⬜ {r.name} — nije prisutna"
        st.markdown(f"**{header}**")
        st.caption(meaning_for(r.id))
        with st.expander(f"Uvjeti i snaga · {r.name}", expanded=False):
            st.markdown(f"**Što znači:** {meaning_for(r.id)}")
            st.caption(interpretation_note(r))
            definition = YOGA_REGISTRY.get(r.id)
            if definition:
                st.markdown(f"**Kako nastaje:** {definition.definition.hr_description}")
            cols = st.columns(3)
            cols[0].markdown(f"**Status:** {r.status}")
            cols[1].markdown(f"**Kategorija:** {r.category}")
            cols[2].markdown(f"**Referenca:** {r.reference}")
            if r.planets:
                st.markdown(f"**Planeti:** {', '.join(r.planets)}")
            if r.houses:
                st.markdown(f"**Kuće:** {', '.join(f'{h}.' for h in r.houses)}")
            if r.present:
                st.markdown(f"**Snaga:** {r.strength:.0f}/100")
            if r.reasons:
                st.markdown("**Uvjet(i):**")
                for reason in r.reasons:
                    st.markdown(f"- {reason}")
            if r.weakening_factors:
                st.markdown("**Slabi:**")
                for w in r.weakening_factors:
                    st.markdown(f"- {w}")
            if r.cancellation_factors:
                st.markdown("**Poništenje:**")
                for c in r.cancellation_factors:
                    st.markdown(f"- {c}")
            source_line = f"**Izvor:** {r.source}"
            if r.variant:
                source_line += f" ({r.variant})"
            st.markdown(source_line)
            if r.requires_source_review:
                st.warning(f"Ova varijanta zahtijeva dodatnu provjeru izvora: {r.review_note}")
            with st.expander("Zašto je ova yoga pronađena?" if r.present else "Zašto NIJE pronađena?"):
                st.code("\n".join(r.debug_log) or "(nema tehničkog traga)", language="text")

    with st.expander("Katalog svih yoga (implementirane i neimplementirane)"):
        st.caption(
            "Interna tablica (zahtjev #29) - implementirane yoge dolaze iz core.yoga_engine.registry.YOGA_REGISTRY, "
            "neimplementirane (namjerno preskočene zbog nesigurne/spornе klasične formulacije) iz PENDING_REVIEW."
        )
        rows = []
        for entry in YOGA_REGISTRY.values():
            d = entry.definition
            rows.append({
                "Yoga": d.hr_name, "Kategorija": d.category, "Izvor": d.source,
                "Značenje": meaning_for(d.id), "Implementirano": "DA", "Verzija pravila": d.rule_version, "Napomena": d.review_note,
            })
        for d in PENDING_REVIEW:
            rows.append({
                "Yoga": d.hr_name, "Kategorija": d.category, "Izvor": d.source,
                "Implementirano": "NE (source review)", "Verzija pravila": "-", "Napomena": d.review_note,
            })
        colored_dataframe(rows, use_container_width=True, hide_index=True, height=full_table_height(rows))
