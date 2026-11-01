"""
Privatna lokalna Jyotish aplikacija.

Pokretanje: streamlit run app.py
Otvara se na http://localhost:8501, isključivo lokalno - bez hostinga,
bez prijave, bez slanja podataka na server (osim geokodiranja grada
prilikom unosa nove osobe).
"""

import streamlit as st
from ui.colors import SECTION_COLORS, color_legend

from db.database import init_db
from ui import pages_persons, pages_chart

st.set_page_config(page_title="Jyotish", page_icon="✨", layout="wide")

st.markdown("""<style>
.block-container {padding-top:3.5rem;padding-bottom:1rem;max-width:1600px;}
[data-testid="stVerticalBlock"] {gap:.45rem;}
h1,h2,h3 {padding-top:.2rem !important;padding-bottom:.3rem !important;}
[data-testid="stSidebar"] {min-width:220px;max-width:250px;}
[data-testid="stAppViewContainer"] {background:#f6f8fc;}
[data-testid="stSidebar"] {background:#eaf0fa;border-right:1px solid #ccd8e9;}
h1,h2,h3 {color:#264d80;}
[data-testid="stExpander"] {background:#fff;border:1px solid #d3deed;border-radius:10px;}
[data-testid="stMetric"] {background:#edf3fd;border-left:4px solid #285cad;padding:10px;border-radius:8px;}
[data-testid="stForm"] {background:#fff;border:1px solid #d3deed;border-radius:10px;}
button[kind="secondary"] {border-color:#becde2;background:#fff;color:#264d80;}
[role="radiogroup"] {background:#eaf0fa;border-radius:8px;padding:6px 10px;}
[data-baseweb="tab"] {color:#536278;}
[data-baseweb="tab"][aria-selected="true"] {color:#285cad;background:#e0eafb;border-radius:8px 8px 0 0;}
</style>""", unsafe_allow_html=True)
init_db()

st.sidebar.title("✨ Jyotish")
page = st.sidebar.selectbox(
    "Prikaz",
    ["D1", "Tranziti", "Varshaphala", "Masa Pravesha", "Sahame", "Tajika", "Varge", "Daše", "Yoge", "Osobe"],
    key="main_navigation",
)
accent = SECTION_COLORS[page]
st.markdown(f'<div style="border-left:5px solid {accent};background:{accent}12;padding:7px 12px;border-radius:6px;color:{accent};font-weight:700">{page}</div>', unsafe_allow_html=True)
color_legend()
if page == "Osobe":
    pages_persons.render()
else:
    pages_chart.render(page)
st.sidebar.caption("Lokalna aplikacija · Jyotish 01.10.2026 / boje i preglednost")
