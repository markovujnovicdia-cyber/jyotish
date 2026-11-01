"""Shared, readable colors for charts, periods and tables."""
from html import escape
import re

PLANET_COLORS = {
    "Sunce": "#9c341c", "Mjesec": "#087885", "Mars": "#bc3030",
    "Merkur": "#267344", "Jupiter": "#995800", "Venera": "#a62d73",
    "Saturn": "#285cad", "Rahu": "#795133", "Ketu": "#536278",
}
ABBR_COLORS = dict(zip(["Su", "Mj", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"], PLANET_COLORS.values()))
SAHAM_COLOR = "#7445a4"
SECTION_COLORS = {"D1":"#285cad", "Tranziti":"#087885", "Varshaphala":"#995800",
    "Masa Pravesha":"#267344", "Sahame":SAHAM_COLOR, "Tajika":"#9c341c",
    "Varge":"#285cad", "Daše":"#a62d73", "Yoge":"#267344",
    "Tumačenje":"#536278", "Osobe":"#536278"}

def label_color(value):
    text = str(value).strip()
    if 'Saham' in text or 'Sahama' in text:
        return SAHAM_COLOR
    for name, color in PLANET_COLORS.items():
        if re.search(r'(?<!\w)' + re.escape(name) + r'(?!\w)', text):
            return color
    token = text.split()[0].rstrip('R,;') if text else ''
    if token.endswith('S') and len(token) <= 4:
        return SAHAM_COLOR
    return ABBR_COLORS.get(token)

def colored_dataframe(data, **kwargs):
    import pandas as pd
    import streamlit as st
    frame = data.copy() if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    if frame.empty:
        return st.dataframe(frame, **kwargs)
    def style_row(row):
        color = next((c for v in row for c in [label_color(v)] if c), None)
        background = ('#' + ''.join(f'{round(int(color[i:i+2],16)*0.09+255*0.91):02x}' for i in (1,3,5))) if color else ('#eef3f9' if frame.index.get_loc(row.name) % 2 == 0 else '#ffffff')
        return [f'background-color: {background}; color: {label_color(v) or "#243248"};' +
                ('font-weight: 700;' if label_color(v) else '') for v in row]
    return st.dataframe(frame.style.apply(style_row, axis=1), **kwargs)

def color_legend():
    import streamlit as st
    chips = ''.join(f'<span style="display:inline-block;margin:0 12px 4px 0;color:{color};font-weight:600">● {escape(name)}</span>'
                    for name,color in list(PLANET_COLORS.items()) + [('Sahame',SAHAM_COLOR)])
    st.markdown(f'<div style="font-size:.78rem;padding:6px 0">{chips}</div>', unsafe_allow_html=True)
