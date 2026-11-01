"""
Sjevernoindijski raspored kuća (1. kuća gore, 2. lijevo od nje, itd. -
isti smjer i susjedstva kao klasični dijamant), ali nacrtan PRAVOKUTNIM
ćelijama umjesto trokutastih/dijamantnih polja - da stane više podataka
po kući (planeti, snaga, protok).

Geometrija: 4x4 mreža, 12 ćelija na OBODU (rubu), sredina (2x2) prazna/
za naslov - kao "prsten" oko centra, ali pravokutan umjesto rombovid.
Raspored po obodu ide suprotno od kazaljke na satu počevši od 1. kuće
(gore), tako da je 2. kuća odmah lijevo od 1., a 12. odmah desno -
identično sjevernoindijskoj topologiji, samo bez dijagonala.
"""

from typing import Dict

_COLOR_INK = "#2b2b2b"
_COLOR_BG = "#eaf1fb"
_COLOR_LAGNA_BG = "#d7e6fa"
_COLOR_MUTED = "#526174"
_COLOR_CENTER_BG = "#f5f0e5"

_CELL_W = 158
_CELL_H = 112
_MARGIN = 12

_HOUSE_POS = {
    1: (0, 2),
    2: (0, 1),
    3: (0, 0),
    4: (1, 0),
    5: (2, 0),
    6: (3, 0),
    7: (3, 1),
    8: (3, 2),
    9: (3, 3),
    10: (2, 3),
    11: (1, 3),
    12: (0, 3),
}


def render_rect_chart_svg(
    ascendant_sign_index: int,
    house_data: Dict[int, Dict],
    title: str = "",
) -> str:
    """
    house_data: {broj_kuce (1-12): {
        "sign_index": int,
        "planet_lines": [str, ...],
        "strength": Optional[float],
        "argala_active": Optional[int],
    }}
    """
    grid_w = _CELL_W * 4
    grid_h = _CELL_H * 4
    total_w = _MARGIN * 2 + grid_w
    total_h = _MARGIN * 2 + grid_h + 36

    svg_parts = [
        f'<svg viewBox="0 0 {total_w} {total_h}" width="100%" style="max-width:100%;height:auto;" '
        'xmlns="http://www.w3.org/2000/svg" '
        'font-family="Georgia, \'Times New Roman\', serif">',
        f'<rect x="0" y="0" width="{total_w}" height="{total_h}" fill="{_COLOR_BG}" rx="6"/>',
    ]

    center_x = _MARGIN + _CELL_W
    center_y = _MARGIN + _CELL_H
    svg_parts.append(
        f'<rect x="{center_x}" y="{center_y}" width="{_CELL_W * 2}" height="{_CELL_H * 2}" '
        f'fill="{_COLOR_CENTER_BG}" stroke="{_COLOR_INK}" stroke-width="1.3"/>'
    )
    if title:
        svg_parts.append(
            f'<text x="{center_x + _CELL_W:.0f}" y="{center_y + _CELL_H:.0f}" text-anchor="middle" '
            f'dominant-baseline="middle" font-size="16" font-weight="bold" fill="{_COLOR_INK}">{title}</text>'
        )

    for house_num, (row, col) in _HOUSE_POS.items():
        x = _MARGIN + col * _CELL_W
        y = _MARGIN + row * _CELL_H

        data = house_data.get(house_num, {})
        sign_index = data.get("sign_index", (ascendant_sign_index + house_num - 1) % 12)
        planet_lines = data.get("planet_lines", [])
        strength = data.get("strength")
        argala_active = data.get("argala_active")

        fill = _COLOR_LAGNA_BG if house_num == 1 else _COLOR_BG
        svg_parts.append(
            f'<rect x="{x}" y="{y}" width="{_CELL_W}" height="{_CELL_H}" '
            f'fill="{fill}" stroke="{_COLOR_INK}" stroke-width="1.3"/>'
        )

        header_y = y + 15
        svg_parts.append(
            f'<text x="{x + 6}" y="{header_y}" font-size="11" font-weight="700" '
            f'fill="{_COLOR_INK}">H{house_num}</text>'
        )
        svg_parts.append(
            f'<text x="{x + _CELL_W - 6}" y="{header_y}" text-anchor="end" font-size="11" '
            f'fill="{_COLOR_MUTED}">znak {sign_index + 1}</text>'
        )
        if house_num == 1:
            svg_parts.append(
                f'<text x="{x + _CELL_W / 2:.0f}" y="{y + _CELL_H - 4}" text-anchor="middle" '
                f'font-size="10" font-weight="700" font-style="italic" fill="{_COLOR_INK}" opacity="0.7">Lagna</text>'
            )

        line_y = y + 30
        max_lines = 4
        for line in planet_lines[:max_lines]:
            svg_parts.append(
                f'<text x="{x + 6}" y="{line_y}" font-size="10.5" font-weight="600" '
                f'fill="{_COLOR_INK}">{line}</text>'
            )
            line_y += 13
        if len(planet_lines) > max_lines:
            svg_parts.append(
                f'<text x="{x + 6}" y="{line_y}" font-size="9.5" fill="{_COLOR_MUTED}">'
                f'+{len(planet_lines) - max_lines} još</text>'
            )

        footer_y = y + _CELL_H - 5
        if strength is not None:
            svg_parts.append(
                f'<text x="{x + 6}" y="{footer_y}" font-size="9.5" fill="{_COLOR_MUTED}">'
                f'snaga {strength:.0f}</text>'
            )
        if argala_active is not None:
            svg_parts.append(
                f'<text x="{x + _CELL_W - 6}" y="{footer_y}" text-anchor="end" font-size="9.5" '
                f'fill="{_COLOR_MUTED}">protok {argala_active}/4</text>'
            )

    svg_parts.append("</svg>")
    return "".join(svg_parts)
