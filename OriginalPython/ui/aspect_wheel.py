"""
Kružni prikaz Graha Drishti (planetarnih aspekata) - vidi core/aspects.py
za formulu. Planeti su raspoređeni po kotaču na svojim STVARNIM stupnjevima
(kao orijentir/pozicija), a LINIJE između njih pokazuju stvarne aktivne
aspekte iz core.aspects.compute_graha_drishti - deblja i tamnija linija =
jači aspekt (puni 100% je najdeblji, 1/4 je najtanja i isprekidana).

Dva načina rada:
- render_self_aspect_wheel_svg: aspekti UNUTAR jedne karte (natalni planeti
  međusobno, ili Varsha planeti međusobno) - jedan prsten, linije su
  tetive (chords) unutar kruga.
- render_gochara_aspect_wheel_svg: aspekti TRANZITNIH planeta NA NATALNE
  planete/Lagnu (Gochara) - dva prstena (natal unutra, tranzit vani),
  linije idu od vanjskog prstena prema unutarnjem.
"""

import math
from typing import Dict, List, Tuple

from core.aspects import AspectRelation

_COLOR_BG = "#fffcf6"
_COLOR_NATAL = "#2c3e6b"
_COLOR_TRANSIT = "#b5482e"
_COLOR_SIGN_LINE = "#4a4a4a"
_COLOR_SIGN_TEXT = "#3a3a3a"
_COLOR_CIRCLE = "#6b6b6b"
_COLOR_ASC = "#1a1a1a"
_COLOR_ASPECT = "#8a2d2d"

# stil linije po snazi aspekta: (širina, opacity, dasharray|None)
_STRENGTH_STYLE = {
    1.0: (2.6, 0.85, None),
    0.75: (1.8, 0.65, None),
    0.5: (1.2, 0.5, "5,3"),
    0.25: (0.9, 0.38, "2,3"),
}
_STRENGTH_ORDER = [1.0, 0.75, 0.5, 0.25]
_STRENGTH_NAME = {1.0: "puni (100%)", 0.75: "3/4 (75%)", 0.5: "1/2 (50%)", 0.25: "1/4 (25%)"}


def _point(cx: float, cy: float, radius: float, angle_deg: float) -> Tuple[float, float]:
    """angle_deg: 0° = vrh, raste suprotno od kazaljke na satu."""
    rad = math.radians(angle_deg)
    return (cx + radius * math.sin(rad), cy - radius * math.cos(rad))


def _screen_angle(longitude: float, ascendant_longitude: float) -> float:
    rel = (longitude - ascendant_longitude) % 360.0
    return (-rel) % 360.0


def _zodiac_ring_svg(cx: float, cy: float, ascendant_longitude: float,
                      r_inner: float, r_outer: float, r_label: float) -> List[str]:
    parts = [
        f'<circle cx="{cx}" cy="{cy}" r="{r_outer}" fill="none" '
        f'stroke="{_COLOR_CIRCLE}" stroke-width="2" opacity="0.9"/>'
    ]
    asc_sign_index = int(ascendant_longitude % 360.0 // 30)
    for i in range(12):
        sign_index = (asc_sign_index + i) % 12
        boundary_angle = _screen_angle(sign_index * 30, ascendant_longitude)
        p1 = _point(cx, cy, r_inner, boundary_angle)
        p2 = _point(cx, cy, r_outer, boundary_angle)
        parts.append(
            f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" '
            f'stroke="{_COLOR_SIGN_LINE}" stroke-width="1.2" opacity="0.5"/>'
        )
        label_angle = _screen_angle(sign_index * 30 + 15, ascendant_longitude)
        lp = _point(cx, cy, r_label, label_angle)
        parts.append(
            f'<text x="{lp[0]:.1f}" y="{lp[1]:.1f}" text-anchor="middle" dominant-baseline="middle" '
            f'font-size="12" font-weight="700" fill="{_COLOR_SIGN_TEXT}">{sign_index + 1}</text>'
        )
    asc_p1 = _point(cx, cy, r_inner, 0)
    asc_p2 = _point(cx, cy, r_outer, 0)
    parts.append(
        f'<line x1="{asc_p1[0]:.1f}" y1="{asc_p1[1]:.1f}" x2="{asc_p2[0]:.1f}" y2="{asc_p2[1]:.1f}" '
        f'stroke="{_COLOR_ASC}" stroke-width="2.5"/>'
    )
    return parts


def _legend_svg(cx: float, y: float) -> List[str]:
    parts = []
    x = cx - 190
    for strength in _STRENGTH_ORDER:
        width, opacity, dash = _STRENGTH_STYLE[strength]
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(
            f'<line x1="{x}" y1="{y}" x2="{x + 22}" y2="{y}" stroke="{_COLOR_ASPECT}" '
            f'stroke-width="{width}" opacity="{opacity}"{dash_attr}/>'
            f'<text x="{x + 27}" y="{y}" font-size="9.5" fill="{_COLOR_SIGN_TEXT}" '
            f'dominant-baseline="middle">{_STRENGTH_NAME[strength]}</text>'
        )
        x += 100
    return parts


def render_self_aspect_wheel_svg(
    planet_longitudes: Dict[str, float],
    ascendant_longitude: float,
    relations: List[AspectRelation],
    title: str = "",
) -> str:
    """
    planet_longitudes: {naziv_planeta: apsolutna_dužina} - SVI planeti koje
        treba prikazati na kotaču (uklj. Rahu/Ketu ako se žele vidjeti kao
        pozicije, iako ne primaju/bacaju aspekt - vidi core/aspects.py).
    relations: rezultat core.aspects.compute_graha_drishti(sign_index_map)
        pozvanog BEZ drugog argumenta (aspekti unutar iste karte).
    """
    cx, cy = 250, 250
    canvas_w, canvas_h = 500, 560
    r_planets = 150
    r_inner = 168
    r_outer = 205
    r_label = 220

    svg_parts = [
        f'<svg viewBox="0 0 {canvas_w} {canvas_h}" width="100%" style="max-width:100%;height:auto;" '
        'xmlns="http://www.w3.org/2000/svg" '
        'font-family="Georgia, \'Times New Roman\', serif">',
        f'<rect x="0" y="0" width="{canvas_w}" height="{canvas_h}" fill="{_COLOR_BG}" rx="8"/>',
    ]
    svg_parts.extend(_zodiac_ring_svg(cx, cy, ascendant_longitude, r_inner, r_outer, r_label))

    angles = {
        name: _screen_angle(lon, ascendant_longitude)
        for name, lon in planet_longitudes.items()
    }

    # linije prvo (ispod točkica planeta), slabije snage prve da jače ostanu vidljivije na vrhu
    drawn_pairs = set()
    for strength in sorted(_STRENGTH_ORDER, reverse=True):
        width, opacity, dash = _STRENGTH_STYLE[strength]
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        for rel in relations:
            if rel.strength != strength:
                continue
            pair_key = frozenset((rel.from_planet, rel.to_planet))
            if pair_key in drawn_pairs:
                continue  # aspekti su gotovo uvijek uzajamni na istoj karti - crtaj jednom
            if rel.from_planet not in angles or rel.to_planet not in angles:
                continue
            drawn_pairs.add(pair_key)
            p1 = _point(cx, cy, r_planets, angles[rel.from_planet])
            p2 = _point(cx, cy, r_planets, angles[rel.to_planet])
            svg_parts.append(
                f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" '
                f'stroke="{_COLOR_ASPECT}" stroke-width="{width}" opacity="{opacity}"{dash_attr}/>'
            )

    for name, lon in planet_longitudes.items():
        angle = angles[name]
        p = _point(cx, cy, r_planets, angle)
        svg_parts.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="3" fill="{_COLOR_NATAL}"/>')
        label_p = _point(cx, cy, r_planets - 18, angle)
        svg_parts.append(
            f'<text x="{label_p[0]:.1f}" y="{label_p[1]:.1f}" text-anchor="middle" '
            f'dominant-baseline="middle" font-size="11" font-weight="700" '
            f'fill="{_COLOR_NATAL}">{name}</text>'
        )

    svg_parts.extend(_legend_svg(cx, canvas_h - 40))
    if title:
        svg_parts.append(
            f'<text x="{cx}" y="{canvas_h - 12}" text-anchor="middle" font-size="14" '
            f'fill="{_COLOR_SIGN_TEXT}" font-weight="bold">{title}</text>'
        )

    svg_parts.append("</svg>")
    return "".join(svg_parts)


def render_gochara_aspect_wheel_svg(
    natal_longitudes: Dict[str, float],
    transit_longitudes: Dict[str, float],
    natal_ascendant_longitude: float,
    relations: List[AspectRelation],
    title: str = "",
) -> str:
    """
    natal_longitudes: {naziv_planeta: apsolutna_dužina} - natalni planeti
        (unutarnji prsten). "Lagna" se posebno postavlja na ASC (0°),
        NIJE potrebno ručno dodavati u ovaj dict.
    transit_longitudes: {naziv_planeta: apsolutna_dužina} - tranzitni
        planeti (vanjski prsten).
    relations: rezultat core.aspects.compute_graha_drishti(transit_sign_map,
        natal_sign_map) - from_planet je uvijek TRANZITNI planet,
        to_planet je natalni planet ILI "Lagna".
    """
    cx, cy = 260, 260
    canvas_w, canvas_h = 520, 580
    r_natal = 90
    r_transit = 150
    r_inner = 168
    r_outer = 205
    r_label = 220

    svg_parts = [
        f'<svg viewBox="0 0 {canvas_w} {canvas_h}" width="100%" style="max-width:100%;height:auto;" '
        'xmlns="http://www.w3.org/2000/svg" '
        'font-family="Georgia, \'Times New Roman\', serif">',
        f'<rect x="0" y="0" width="{canvas_w}" height="{canvas_h}" fill="{_COLOR_BG}" rx="8"/>',
    ]
    svg_parts.extend(_zodiac_ring_svg(cx, cy, natal_ascendant_longitude, r_inner, r_outer, r_label))

    natal_angles = {
        name: _screen_angle(lon, natal_ascendant_longitude) for name, lon in natal_longitudes.items()
    }
    natal_angles["Lagna"] = 0.0
    transit_angles = {
        name: _screen_angle(lon, natal_ascendant_longitude) for name, lon in transit_longitudes.items()
    }

    for strength in sorted(_STRENGTH_ORDER, reverse=True):
        width, opacity, dash = _STRENGTH_STYLE[strength]
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        for rel in relations:
            if rel.strength != strength:
                continue
            if rel.from_planet not in transit_angles or rel.to_planet not in natal_angles:
                continue
            p1 = _point(cx, cy, r_transit, transit_angles[rel.from_planet])
            p2 = _point(cx, cy, r_natal, natal_angles[rel.to_planet])
            svg_parts.append(
                f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" '
                f'stroke="{_COLOR_ASPECT}" stroke-width="{width}" opacity="{opacity}"{dash_attr}/>'
            )

    for name, angle in natal_angles.items():
        p = _point(cx, cy, r_natal, angle)
        svg_parts.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="3" fill="{_COLOR_NATAL}"/>')
        label_p = _point(cx, cy, r_natal - 16, angle)
        svg_parts.append(
            f'<text x="{label_p[0]:.1f}" y="{label_p[1]:.1f}" text-anchor="middle" '
            f'dominant-baseline="middle" font-size="10" font-weight="700" '
            f'fill="{_COLOR_NATAL}">{name}</text>'
        )
    for name, angle in transit_angles.items():
        p = _point(cx, cy, r_transit, angle)
        svg_parts.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="3" fill="{_COLOR_TRANSIT}"/>')
        label_p = _point(cx, cy, r_transit + 14, angle)
        svg_parts.append(
            f'<text x="{label_p[0]:.1f}" y="{label_p[1]:.1f}" text-anchor="middle" '
            f'dominant-baseline="middle" font-size="10" font-weight="700" '
            f'fill="{_COLOR_TRANSIT}">{name}</text>'
        )

    legend_y = canvas_h - 56
    svg_parts.append(
        f'<line x1="{cx - 130}" y1="{legend_y}" x2="{cx - 105}" y2="{legend_y}" '
        f'stroke="{_COLOR_NATAL}" stroke-width="3"/>'
        f'<text x="{cx - 100}" y="{legend_y}" font-size="11" fill="{_COLOR_SIGN_TEXT}" '
        f'dominant-baseline="middle">natal (+ Lagna)</text>'
        f'<line x1="{cx + 20}" y1="{legend_y}" x2="{cx + 45}" y2="{legend_y}" '
        f'stroke="{_COLOR_TRANSIT}" stroke-width="3"/>'
        f'<text x="{cx + 50}" y="{legend_y}" font-size="11" fill="{_COLOR_SIGN_TEXT}" '
        f'dominant-baseline="middle">tranzit</text>'
    )
    svg_parts.extend(_legend_svg(cx, canvas_h - 30))
    if title:
        svg_parts.append(
            f'<text x="{cx}" y="{canvas_h - 8}" text-anchor="middle" font-size="13" '
            f'fill="{_COLOR_SIGN_TEXT}" font-weight="bold">{title}</text>'
        )

    svg_parts.append("</svg>")
    return "".join(svg_parts)
