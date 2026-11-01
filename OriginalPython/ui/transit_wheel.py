from ui.colors import ABBR_COLORS, SAHAM_COLOR
"""
Kružni "kotač" tranzita s dva prstena:
- unutarnji prsten: natalni planeti + AL/BP/GK/Md + Sahami, na TOČNOJ
  natalnoj poziciji
- vanjski prsten: tranzitni planeti, na TOČNOJ tranzitnoj poziciji

Referentna točka je natalni Ascendent - uvijek na vrhu (0°), stupnjevi
rastu suprotno od kazaljke na satu (isti smjer kao dijamant karta).

Dvije razine podjele oko kotača:
- 12 znakova (deblje, sivo-tamne linije + naziv znaka)
- 27 nakshatri (tanje, svjetlije linije + skraćeni naziv), još dalje van

ISPRAVAK 2 (točnost pozicije): raniji pokušaj čitljivosti dopuštao je i
SITAN KUTNI pomak (jitter) točke radi razmicanja gusto zbijenih planeta -
to je bilo POGREŠNO, jer je značilo da nacrtana pozicija više NIJE bila
stvarni stupanj planeta (izgledalo je kao greška u prikazu, i JEST bila
netočnost). Sada se točka NIKAD ne pomiče kutno - SAMO radijalno (bliže/
dalje od centra unutar istog prstena), a i to samo kad je nužno da se
izbjegne preklapanje s drugom točkom. Kutni položaj je UVIJEK matematički
točan.

Svaka planeta je SAMO SLOVO/OZNAKA (bez posebne točke-kruga) ispisana
IZRAVNO na svojoj stvarnoj poziciji - dovoljno velika da se jasno vidi
gdje točno stoji. Koristi se pravi test preklapanja (bounding-box
kolizija): za svaku oznaku isprobavaju se kandidatske udaljenosti od
centra (SAMO radijalno, kut nikad - vidi ISPRAVAK 2 gore) dok se ne
pronađe mjesto koje se NE preklapa s bilo kojom već postavljenom oznakom
(na oba prstena). Oznake s VIŠE istovremenih dodira (konjunkcija/aspekt)
postavljaju se PRVE (najveća sloboda rasporeda za ono što je vizualno
najvažnije), i one su i VEĆE.

Veličina/isticanje oznake ovisi o BROJU dodira (natal_hit_counts/
transit_hit_counts, izračunato u ui/pages_chart.py iz konjunkcije unutar
ORB_DEGREES() i posebnog punog aspekta - core/aspects.py, Gochara princip:
tranzitni planet aktivira natalnu točku i aspektom, ne samo konjunkcijom):
0 dodira = normalna veličina/boja; 1+ dodira = zlatna boja, veličina RASTE
s brojem dodira (do gornje granice).

Svih 9 grahe ima SVOJU boju (ne samo 6) - Mjesec/Rahu/Ketu su ranije bili
crni kao i AL/BP/GK/Md, što je otežavalo razlikovanje; sad su AL/BP/GK/Md
(izračunate točke, ne fizički planeti) jedini koji ostaju neutralno crni.
"""

import math
from html import escape
from typing import Dict, List, Optional, Tuple

from core.constants import NAKSHATRA_ABBR

_COLOR_BG = "#eaf1fb"
_COLOR_HIT = "#b8860b"         # zlatna - aktivan utjecaj (konjunkcija ili puni aspekt)
_COLOR_SIGN_LINE = "#333333"
_COLOR_SIGN_TEXT = "#242424"
_COLOR_NAK_LINE = "#b0a692"
_COLOR_NAK_TEXT = "#6b6152"
_COLOR_ASC = "#1a1a1a"
_COLOR_CIRCLE = "#4d4d4d"

# Boja po planetu (ista boja bez obzira je li na natalnom ili tranzitnom
# prstenu - identitet planeta, ne prsten, određuje boju). Samo AL/BP/GK/Md
# (izračunate točke, ne fizički planeti) ostaju neutralno crni.
_COLOR_BLACK = "#1a1a1a"
_COLOR_SAHAM = SAHAM_COLOR  # ljubičasta - Sahami (osjetljive točke)
_SAHAM_LABELS = {"PuS", "ViS", "YaS", "VvS", "PtS"}
_PLANET_ABBR_COLOR = ABBR_COLORS


def _color_for_label(label: str) -> str:
    """Skida eventualni 'R' (retrogradan) sufiks pa traži boju po planetu;
    Sahami su ljubičasti; AL/BP/GK/Md (izračunate točke) ostaju crne."""
    if label.endswith("S"):
        return _COLOR_SAHAM
    base = label[:-1] if label.endswith("R") and label[:-1] in _PLANET_ABBR_COLOR else label
    return _PLANET_ABBR_COLOR.get(base, _COLOR_BLACK)

_CENTER = (570, 570)
_R_INNER = 125
_R_NATAL = 190
_R_MID = 280
_R_TRANSIT = 330
_R_OUTER = 440          # granica znakova (glavni krug)
_R_SIGN_LABEL = 458
_R_NAK_TICK_IN = 468    # nakshatra oznake počinju odmah iza naziva znaka
_R_NAK_TICK_OUT = 482
_R_NAK_LABEL = 498
_R_ASC_LABEL = 522

ORB_DEGREES = 3.0  # dopušteno odstupanje za konjunkciju ("dodir")

# --- Veličina/font po broju dodira (konjunkcija + puni aspekt, zbrojeno) ---
# Nema više posebne točke-kruga - samo slovo/oznaka na stvarnoj poziciji,
# pa font mora biti dovoljno velik da se jasno vidi i čita.
_FONT_BASE = 26.0
_FONT_HIT_BASE = 27.0
_FONT_HIT_STEP = 1.6
_MAX_EXTRA_HITS = 3         # zasićenje - 4+ dodira izgleda isto kao točno 4

# --- Traženje slobodnog mjesta (kolizijski test, BEZ pomaka kuta - vidi
# ISPRAVAK 2 na vrhu; oznaka se pomiče SAMO radijalno od centra) ---
_RADIUS_SEARCH_STEP = 11.0
_RADIUS_SEARCH_TRIES = 19
_CHAR_WIDTH_FACTOR = 0.66   # aproksimacija širine znaka (Georgia, bold) u jedinicama font-size
_BOX_PAD = 2.0


def _point(radius: float, angle_deg: float) -> Tuple[float, float]:
    """angle_deg: 0° = vrh, raste suprotno od kazaljke na satu."""
    rad = math.radians(angle_deg)
    return (
        _CENTER[0] + radius * math.sin(rad),
        _CENTER[1] - radius * math.cos(rad),
    )


def _screen_angle(longitude: float, ascendant_longitude: float) -> float:
    rel = (longitude - ascendant_longitude) % 360.0
    return (-rel) % 360.0


def angular_distance(lon_a: float, lon_b: float) -> float:
    d = abs(lon_a - lon_b) % 360.0
    return min(d, 360.0 - d)


_Box = Tuple[float, float, float, float]  # (xmin, ymin, xmax, ymax)


def _text_box(cx: float, cy: float, text: str, font_size: float) -> _Box:
    w = len(text) * font_size * _CHAR_WIDTH_FACTOR + 3.0
    h = font_size * 1.3
    return (cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0)


def _overlap_severity(box: _Box, placed: List[_Box], pad: float = _BOX_PAD) -> float:
    """Zbroj površina preklapanja sa svime već postavljenim (svaki okvir
    napuhan za 'pad' - mali razmak između susjeda, ne samo "ne dodiruju
    se") - 0.0 znači savršeno slobodno mjesto. Koristi se SAMO kao
    "najmanje loša" rezerva ako baš NIJEDAN kandidat nije savršeno
    slobodan (fizički nemoguća gustoća) - bira se onaj s NAJMANJE
    preklapanja, ne prvi isprobani."""
    total = 0.0
    bx0, by0, bx1, by1 = box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad
    for ox0, oy0, ox1, oy1 in placed:
        ix = max(0.0, min(bx1, ox1) - max(bx0, ox0))
        iy = max(0.0, min(by1, oy1) - max(by0, oy0))
        total += ix * iy
    return total


def _find_free_text_position(true_angle: float, base_radius: float, label: str,
                              font_size: float, placed: List[_Box]) -> Tuple[Tuple[float, float], _Box]:
    """Traži SAMO radijalni pomak (0, +1, -1, +2, -2, ...) od base_radius -
    KUT ostaje UVIJEK true_angle (matematički točan stupanj, nikad
    pomaknut - vidi ISPRAVAK 2 na vrhu datoteke), dok oznaka ne prestane
    presijecati već postavljene oznake. Ako NIJEDAN radijalni pomak nije
    savršeno slobodan, vraća onaj s najmanje preklapanja (a ne prvi
    isprobani)."""
    best_pos = None
    best_box = None
    best_severity = None
    for tier in range(_RADIUS_SEARCH_TRIES):
        magnitude = (tier + 1) // 2
        sign = 1.0 if tier % 2 == 1 else -1.0
        offset = 0.0 if tier == 0 else sign * magnitude * _RADIUS_SEARCH_STEP
        radius = base_radius + offset
        if base_radius == _R_NATAL and not 155 <= radius <= 258:
            continue
        if base_radius == _R_TRANSIT and not 295 <= radius <= 428:
            continue
        p = _point(radius, true_angle)
        box = _text_box(p[0], p[1], label, font_size)
        severity = _overlap_severity(box, placed)
        if severity == 0.0:
            return p, box
        if best_severity is None or severity < best_severity:
            best_pos, best_box, best_severity = p, box, severity
    return best_pos, best_box


def render_transit_wheel_svg(
    natal_labels: Dict[str, float],
    transit_labels: Dict[str, float],
    ascendant_longitude: float,
    title: str = "",
    center_lines: Optional[list] = None,
    natal_hit_counts: Optional[Dict[str, int]] = None,
    transit_hit_counts: Optional[Dict[str, int]] = None,
) -> str:
    """
    natal_labels / transit_labels: {već_formatirana_oznaka: apsolutna_dužina}
    natal_hit_counts / transit_hit_counts: {oznaka: broj_dodira} (konjunkcija
        + poseban puni aspekt) - vidi core/aspects.py i napomenu na vrhu ove
        datoteke. Izostavljena oznaka = 0 dodira (normalna veličina/boja).
    center_lines: kratke tekstualne linije (npr. datum i dasha) koje se
        ispisuju UNUTAR praznog središta kotača (radijus _R_INNER).
    """
    natal_hit_counts = natal_hit_counts or {}
    transit_hit_counts = transit_hit_counts or {}

    cx, cy = _CENTER
    canvas_w, canvas_h = 1140, 1180
    svg_parts = [
        f'<svg viewBox="0 0 {canvas_w} {canvas_h}" width="100%" style="max-width:100%;height:auto;" '
        'xmlns="http://www.w3.org/2000/svg" '
        'font-family="Georgia, \'Times New Roman\', serif">',
        f'<rect x="0" y="0" width="{canvas_w}" height="{canvas_h}" fill="{_COLOR_BG}" rx="8"/>',
    ]

    for r, opacity, width in [(_R_OUTER, 0.95, 2.5), (_R_MID, 0.55, 1.3), (_R_INNER, 0.55, 1.3)]:
        svg_parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
            f'stroke="{_COLOR_CIRCLE}" stroke-width="{width}" opacity="{opacity}"/>'
        )

    svg_parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{_R_MID}" fill="#f5f0e5" stroke="{_COLOR_CIRCLE}" stroke-width="1.3"/>'
    )
    svg_parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{_R_INNER}" fill="#d7e6fa" stroke="{_COLOR_CIRCLE}" stroke-width="1.3"/>'
    )

    ascendant_sign_index = int(ascendant_longitude % 360.0 // 30)

    for i in range(12):
        sign_index = (ascendant_sign_index + i) % 12
        boundary_abs_deg = sign_index * 30
        boundary_angle = _screen_angle(boundary_abs_deg, ascendant_longitude)

        p1 = _point(_R_INNER, boundary_angle)
        p2 = _point(_R_OUTER, boundary_angle)
        svg_parts.append(
            f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" '
            f'stroke="{_COLOR_SIGN_LINE}" stroke-width="1.5" opacity="0.6"/>'
        )

        center_abs_deg = boundary_abs_deg + 15
        label_angle = _screen_angle(center_abs_deg, ascendant_longitude)
        lp = _point(_R_SIGN_LABEL, label_angle)
        svg_parts.append(
            f'<text x="{lp[0]:.1f}" y="{lp[1]:.1f}" text-anchor="middle" '
            f'dominant-baseline="middle" font-size="19" font-weight="700" fill="{_COLOR_SIGN_TEXT}">'
            f'{sign_index + 1}</text>'
        )

    for i in range(27):
        nak_start_abs_deg = i * (360.0 / 27.0)
        boundary_angle = _screen_angle(nak_start_abs_deg, ascendant_longitude)

        p1 = _point(_R_NAK_TICK_IN, boundary_angle)
        p2 = _point(_R_NAK_TICK_OUT, boundary_angle)
        svg_parts.append(
            f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" '
            f'stroke="{_COLOR_NAK_LINE}" stroke-width="1.2"/>'
        )

        nak_center_abs_deg = nak_start_abs_deg + (360.0 / 54.0)
        label_angle = _screen_angle(nak_center_abs_deg, ascendant_longitude)
        lp = _point(_R_NAK_LABEL, label_angle)
        svg_parts.append(
            f'<text x="{lp[0]:.1f}" y="{lp[1]:.1f}" text-anchor="middle" '
            f'dominant-baseline="middle" font-size="13" fill="{_COLOR_NAK_TEXT}">'
            f'{NAKSHATRA_ABBR[i]}</text>'
        )

    asc_p1 = _point(_R_INNER, 0)
    asc_p2 = _point(_R_OUTER, 0)
    svg_parts.append(
        f'<line x1="{asc_p1[0]:.1f}" y1="{asc_p1[1]:.1f}" x2="{asc_p2[0]:.1f}" y2="{asc_p2[1]:.1f}" '
        f'stroke="{_COLOR_ASC}" stroke-width="3.5"/>'
    )
    asc_label = _point(_R_ASC_LABEL, 0)
    svg_parts.append(
        f'<text x="{asc_label[0]:.1f}" y="{asc_label[1]:.1f}" text-anchor="middle" '
        f'dominant-baseline="middle" font-size="18" fill="{_COLOR_ASC}" font-weight="bold">ASC ▲</text>'
    )

    # Skupi obje razine (natalnu i tranzitnu) u JEDAN popis, poredan tako da
    # točke/oznake s NAJVIŠE dodira biraju mjesto PRVE (najveća sloboda
    # rasporeda za ono što je vizualno najvažnije), sve u ZAJEDNIČKI
    # kolizijski prostor (placed_boxes) - garantira da se ništa ne preklapa
    # ni unutar ni između prstenova. KUT (true_angle) se NIKAD ne mijenja -
    # samo se traži druga udaljenost od centra (vidi ISPRAVAK 2 na vrhu).
    entries = []
    for label, lon in natal_labels.items():
        entries.append((label, _screen_angle(lon, ascendant_longitude), _R_NATAL, natal_hit_counts.get(label, 0)))
    for label, lon in transit_labels.items():
        entries.append((label, _screen_angle(lon, ascendant_longitude), _R_TRANSIT, transit_hit_counts.get(label, 0)))
    entries.sort(key=lambda e: -e[3])

    placed_boxes: List[_Box] = [(cx - 110, cy - 112, cx + 110, cy + 112)] if center_lines else []
    for label, true_angle, base_radius, hit_count in entries:
        if hit_count <= 0:
            color = _color_for_label(label)
            font_size = _FONT_BASE
            font_weight = "700"
        else:
            extra = min(hit_count - 1, _MAX_EXTRA_HITS)
            color = _color_for_label(label)
            font_size = _FONT_HIT_BASE + extra * _FONT_HIT_STEP
            font_weight = "700"

        label_pos, label_box = _find_free_text_position(true_angle, base_radius, label, font_size, placed_boxes)
        placed_boxes.append(label_box)
        marker_radius = 265 if base_radius == _R_NATAL else 435
        marker = _point(marker_radius, true_angle)
        svg_parts.append(f'<line x1="{marker[0]:.2f}" y1="{marker[1]:.2f}" x2="{label_pos[0]:.2f}" y2="{label_pos[1]:.2f}" stroke="{color}" stroke-width="1" opacity=".45"/>')
        svg_parts.append(f'<circle cx="{marker[0]:.2f}" cy="{marker[1]:.2f}" r="3.5" fill="{color}"/>')
        if hit_count:
            svg_parts.append(f'<rect x="{label_box[0]-3:.2f}" y="{label_box[1]-2:.2f}" width="{label_box[2]-label_box[0]+6:.2f}" height="{label_box[3]-label_box[1]+4:.2f}" rx="5" fill="#fff0ba"/>')
        svg_parts.append(f'<text x="{label_pos[0]:.1f}" y="{label_pos[1]:.1f}" text-anchor="middle" dominant-baseline="middle" font-size="{font_size:.1f}" font-weight="700" fill="{color}"><title>{escape(label)} · {"natalni" if base_radius == _R_NATAL else "tranzitni"} · {hit_count} dodira</title>{escape(label)}</text>')

    legend_y1 = canvas_h - 70
    legend_y2 = canvas_h - 48
    legend_y3 = canvas_h - 26
    swatches = [
        ("Su", "Sunce"), ("Ma", "Mars"), ("Ve", "Venera"), ("Sa", "Saturn"),
        ("Ju", "Jupiter"), ("Me", "Merkur"), ("Mj", "Mjesec"), ("Ra", "Rahu"), ("Ke", "Ketu"),
    ]
    x = 24
    for abbr, name in swatches:
        color = _PLANET_ABBR_COLOR[abbr]
        svg_parts.append(
            f'<circle cx="{x}" cy="{legend_y1}" r="5.5" fill="{color}"/>'
            f'<text x="{x + 11}" y="{legend_y1}" font-size="13" fill="{_COLOR_SIGN_TEXT}" '
            f'dominant-baseline="middle">{name}</text>'
        )
        x += 110
    svg_parts.append(
        f'<circle cx="24" cy="{legend_y2}" r="5.5" fill="{_COLOR_BLACK}"/>'
        f'<text x="35" y="{legend_y2}" font-size="13" fill="{_COLOR_SIGN_TEXT}" dominant-baseline="middle">'
        f'AL/BP/GK/Md (izračunate točke) = crno</text>'
        f'<circle cx="380" cy="{legend_y2}" r="5.5" fill="{_COLOR_SAHAM}"/>'
        f'<text x="391" y="{legend_y2}" font-size="13" fill="{_COLOR_SIGN_TEXT}" dominant-baseline="middle">'
        f'Sahami = ljubičasta</text>'
    )
    svg_parts.append(
        f'<circle cx="24" cy="{legend_y3}" r="8" fill="{_COLOR_HIT}"/>'
        f'<text x="38" y="{legend_y3}" font-size="13" fill="{_COLOR_SIGN_TEXT}" dominant-baseline="middle">'
        f'žuta podloga = aktivan dodir · unutra natalno / izvana tranzitno</text>'
    )

    if center_lines:
        n = len(center_lines)
        line_height = 34
        start_y = cy - (n - 1) * line_height / 2.0
        for i, line in enumerate(center_lines):
            svg_parts.append(
                f'<text x="{cx}" y="{start_y + i * line_height:.1f}" text-anchor="middle" '
                f'dominant-baseline="middle" font-size="{32 if i == 0 else 30}" font-weight="800" '
                f'fill="#172b4d" font-family="Arial, sans-serif">{escape(str(line))}</text>'
            )
    elif title:
        svg_parts.append(
            f'<text x="{cx}" y="{canvas_h - 10}" text-anchor="middle" font-size="19" '
            f'fill="{_COLOR_SIGN_TEXT}" font-weight="bold">{escape(str(title))}</text>'
        )

    svg_parts.append("</svg>")
    return "".join(svg_parts)
