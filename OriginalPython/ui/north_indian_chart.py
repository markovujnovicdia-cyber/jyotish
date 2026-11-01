from ui.colors import label_color
"""
Generator sjevernoindijskog (North Indian) dijamant prikaza karte kao SVG.

Geometrija: vanjski kvadrat + obje pune dijagonale (kut-do-kuta kroz
centar) + unutarnji romb (spaja polovišta stranica). Te tri linije
zajedno prirodno tvore točno 12 polja, u klasičnom North Indian
rasporedu (1. kuća gore u sredini, redom u smjeru suprotnom od kazaljke
na satu).

Karta je namjerno horizontalno rastegnuta (STRETCH_X > 1) - isti
dijamantni oblik polja, samo šira nego viša, da stane više teksta po
kući bez mijenjanja klasične topologije/oblika polja.

Dizajn je jednobojan (jedna "tintna" boja za linije i tekst, bez
šarenih ispuna po kućama) - čisto, tiskano izdanje bez šarenila.
"""

from typing import Dict, List, Optional, Tuple

Point = Tuple[float, float]

STRETCH_X = 1.55  # horizontalno rastezanje - isti oblik, šira karta

_BASE_HOUSE_POLYGONS: Dict[int, List[Point]] = {
    1: [(200, 0), (300, 100), (200, 200), (100, 100)],
    2: [(0, 0), (200, 0), (100, 100)],
    3: [(0, 0), (100, 100), (0, 200)],
    4: [(0, 200), (100, 100), (200, 200), (100, 300)],
    5: [(0, 200), (100, 300), (0, 400)],
    6: [(0, 400), (100, 300), (200, 400)],
    7: [(200, 400), (100, 300), (200, 200), (300, 300)],
    8: [(200, 400), (300, 300), (400, 400)],
    9: [(400, 400), (300, 300), (400, 200)],
    10: [(400, 200), (300, 300), (200, 200), (300, 100)],
    11: [(400, 200), (300, 100), (400, 0)],
    12: [(400, 0), (300, 100), (200, 0)],
}

_COLOR_INK = "#24364b"
_COLOR_BG = "#eaf1fb"
_COLOR_MUTED = "#526174"

_CANVAS_W = int(400 * STRETCH_X)
_CANVAS_H = 452

_CHAR_WIDTH_FACTOR = 0.80         # regular težina, Georgia serif - namjerno konzervativno
_CHAR_WIDTH_FACTOR_BOLD = 1.02    # bold težina je šira - planetske oznake su bold
_VERTICAL_MARGIN_FRAC = 0.22   # rub koji se ne koristi, gore/dolje unutar poligona
_HORIZONTAL_MARGIN_FRAC = 0.30  # rub koji se ne koristi, lijevo/desno na danoj visini
_MIN_SCALE = 0.4  # nikad ne smanjuj font ispod 40% osnovne veličine


def _stretch(point: Point) -> Point:
    x, y = point
    return (x * STRETCH_X, y)


def _centroid(points: List[Point]) -> Point:
    x = sum(p[0] for p in points) / len(points)
    y = sum(p[1] for p in points) / len(points)
    return (x, y)


def _polygon_points_attr(points: List[Point]) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def _polygon_y_extent(points: List[Point]) -> Tuple[float, float]:
    ys = [p[1] for p in points]
    return min(ys), max(ys)


def _polygon_width_at_y(points: List[Point], y: float) -> float:
    """Vodoravna širina poligona na zadanoj visini y (presjek s bridovima)."""
    n = len(points)
    xs = []
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        if y1 == y2:
            continue
        lo, hi = (y1, y2) if y1 < y2 else (y2, y1)
        if lo <= y <= hi:
            t = (y - y1) / (y2 - y1)
            xs.append(x1 + t * (x2 - x1))
    if len(xs) < 2:
        return 0.0
    return max(xs) - min(xs)


def _build_house_lines(house_num: int, sign_index: int, labels: List[str],
                        extra_info: Optional[str]) -> List[Tuple[str, float, bool]]:
    """
    Vraća popis (tekst, osnovni_font_size, je_li_bold) odozgo prema
    dolje za jednu kuću, bez pozicija - koristi se i za mjerenje i za crtanje.
    is_bold mora odgovarati STVARNOJ font-weight koja se koristi pri crtanju
    (bold tekst je širi, pa utječe na provjeru staje li u kuću).

    Zaglavlje prikazuje SAMO redni broj znaka (1-12) - broj kuće se ne
    ispisuje jer je već jasan iz same pozicije polja u dijamantu.
    """
    lines: List[Tuple[str, float, bool]] = []
    header = str(sign_index + 1)
    lines.append((header, 12.0, False))
    if house_num == 1:
        lines.append(("Lagna", 12.0, True))
    for label in labels:
        lines.append((label, 11.5, True))
    if extra_info:
        lines.append((extra_info, 9.5, False))
    return lines


def _block_start_y(points: List[Point], cy: float, total_height: float) -> float:
    """
    Početni y (gornji rub bloka teksta) za zadanu kuću, tako da cijeli blok
    ostane unutar STVARNIH granica poligona (y_min..y_max, umanjeno za
    marginu), a ne samo simetrično oko centroida.

    Za trokutaste kuće (2,3,5,6,8,9,11,12) centroid NIJE na vertikalnoj
    sredini oblika (bliži je bazi trokuta), pa bi centriranje čisto oko
    centroida moglo gurnuti tekst preko ruba karte na užoj strani. Zato se
    blok centrira oko centroida kad ima mjesta, a inače prislanja uz
    dostupnu granicu (top/bottom) da ostane unutar poligona.
    """
    y_min, y_max = _polygon_y_extent(points)
    margin = (y_max - y_min) * _VERTICAL_MARGIN_FRAC / 2.0
    top_bound = y_min + margin
    bottom_bound = y_max - margin
    ideal_start = cy - total_height / 2.0
    return max(top_bound, min(ideal_start, bottom_bound - total_height))


def _fits_at_scale(points: List[Point], cy: float, lines: List[Tuple[str, float, bool]],
                    scale: float, line_gap: float = 1.3) -> bool:
    y_min, y_max = _polygon_y_extent(points)
    avail_height = (y_max - y_min) * (1.0 - _VERTICAL_MARGIN_FRAC)
    total_height = sum(font * scale * line_gap for _, font, _ in lines)
    if total_height > avail_height:
        return False

    y_cursor = _block_start_y(points, cy, total_height)
    for text, font, is_bold in lines:
        step = font * scale * line_gap
        y_cursor += step
        char_factor = _CHAR_WIDTH_FACTOR_BOLD if is_bold else _CHAR_WIDTH_FACTOR
        width_needed = len(text) * (font * scale) * char_factor
        width_avail = _polygon_width_at_y(points, y_cursor) * (1.0 - _HORIZONTAL_MARGIN_FRAC)
        if width_needed > width_avail:
            return False
    return True


def _best_scale(points: List[Point], cy: float, lines: List[Tuple[str, float, bool]]) -> float:
    for scale in (1.0, 0.9, 0.8, 0.7, 0.6, 0.5, _MIN_SCALE):
        if _fits_at_scale(points, cy, lines, scale):
            return scale
    return 0.0  # ni minimalna velicina ne stane - signal pozivatelju da smanji SADRZAJ, ne samo font


def _fit_house_content(points: List[Point], cy: float, house_num: int, sign_index: int,
                        labels: List[str], extra_info: Optional[str]) -> Tuple[List[Tuple[str, float, bool]], float]:
    """
    Pokušava smjestiti sav sadržaj smanjujući font; ako ni to ne uspije,
    najprije izbacuje najmanje bitan redak (snaga/protok), pa zatim
    skraćuje popis planeta (uz "+N još" naznaku) dok ne stane pri
    najmanjoj dopuštenoj veličini fonta.
    """
    lines = _build_house_lines(house_num, sign_index, labels, extra_info)
    scale = _best_scale(points, cy, lines)
    if scale > 0:
        return lines, scale

    # 1. korak: izbaci "snaga/protok" redak (najmanje bitan za čitljivost karte)
    lines = _build_house_lines(house_num, sign_index, labels, None)
    scale = _best_scale(points, cy, lines)
    if scale > 0:
        return lines, scale

    # 2. korak: skrati popis planeta, dodaj "+N još"
    for keep in range(len(labels) - 1, 0, -1):
        truncated = labels[:keep] + [f"+{len(labels) - keep} još"]
        lines = _build_house_lines(house_num, sign_index, truncated, None)
        scale = _best_scale(points, cy, lines)
        if scale > 0:
            return lines, scale

    # krajnja mjera: samo broj znaka (i "Lagna" ako je 1. kuća), pri minimalnoj velicini
    lines = _build_house_lines(house_num, sign_index, [], None)
    return lines, _MIN_SCALE


def render_north_indian_svg(
    ascendant_sign_index: int,
    planets_by_house: Dict[int, List[str]],
    title: str = "",
    house_extra_info: Optional[Dict[int, str]] = None,
) -> str:
    """
    ascendant_sign_index: 0-11 (0 = Ovan), znak koji je u 1. kući
    planets_by_house: {broj_kuce (1-12): [već formatirane oznake za prikaz]}
    house_extra_info: {broj_kuce: kratki tekst} - opcionalno, npr. "S:65 P:3/4"
        (snaga/protok), ispisuje se sitno na dnu ćelije ako je zadano.

    Sav tekst se GEOMETRIJSKI provjerava protiv stvarnog oblika poligona te
    kuće (širina na svakoj visini, ne samo pravokutni okvir) - ako sadržaj
    ne stane pri punoj veličini fonta, veličina se smanjuje (do 45% osnovne)
    dok sve ne stane unutar granica kuće.
    """
    house_polygons = {h: [_stretch(p) for p in pts] for h, pts in _BASE_HOUSE_POLYGONS.items()}

    svg_parts = [
        f'<svg viewBox="0 0 {_CANVAS_W} {_CANVAS_H}" width="100%" style="max-width:100%;height:auto;" '
        'xmlns="http://www.w3.org/2000/svg" '
        'font-family="Georgia, \'Times New Roman\', serif">',
        f'<rect x="0" y="0" width="{_CANVAS_W}" height="400" fill="{_COLOR_BG}" rx="6"/>',
    ]

    # Blago različita polja olakšavaju praćenje kuća; Lagna je istaknuta.
    for house, polygon in house_polygons.items():
        background = "#d7e6fa" if house == 1 else ("#eaf1fb" if house % 2 else "#f5f0e5")
        svg_parts.append(
            f'<polygon points="{_polygon_points_attr(polygon)}" fill="{background}"/>'
        )

    outer_sq = [(0, 0), (400, 0), (400, 400), (0, 400)]
    outer_sq_s = [_stretch(p) for p in outer_sq]
    diamond = [(200, 0), (400, 200), (200, 400), (0, 200)]
    diamond_s = [_stretch(p) for p in diamond]

    svg_parts.append(
        f'<rect x="1" y="1" width="{_CANVAS_W - 2}" height="398" fill="none" '
        f'stroke="{_COLOR_INK}" stroke-width="2.5" rx="6"/>'
    )
    svg_parts.append(
        f'<line x1="{outer_sq_s[0][0]:.1f}" y1="{outer_sq_s[0][1]:.1f}" '
        f'x2="{outer_sq_s[2][0]:.1f}" y2="{outer_sq_s[2][1]:.1f}" '
        f'stroke="{_COLOR_INK}" stroke-width="1.2"/>'
    )
    svg_parts.append(
        f'<line x1="{outer_sq_s[1][0]:.1f}" y1="{outer_sq_s[1][1]:.1f}" '
        f'x2="{outer_sq_s[3][0]:.1f}" y2="{outer_sq_s[3][1]:.1f}" '
        f'stroke="{_COLOR_INK}" stroke-width="1.2"/>'
    )
    svg_parts.append(
        f'<polygon points="{_polygon_points_attr(diamond_s)}" fill="none" '
        f'stroke="{_COLOR_INK}" stroke-width="1.2"/>'
    )

    if title:
        svg_parts.append(
            f'<text x="{_CANVAS_W / 2:.0f}" y="428" text-anchor="middle" font-size="16" '
            f'fill="{_COLOR_INK}" font-weight="bold">{title}</text>'
        )

    for house_num in range(1, 13):
        sign_index = (ascendant_sign_index + house_num - 1) % 12
        points = house_polygons[house_num]
        cx, cy = _centroid(points)
        labels = planets_by_house.get(house_num, [])
        extra = house_extra_info.get(house_num) if house_extra_info else None

        lines, scale = _fit_house_content(points, cy, house_num, sign_index, labels, extra)
        line_gap = 1.3

        total_height = sum(font * scale * line_gap for _, font, _ in lines)
        y_cursor = _block_start_y(points, cy, total_height)

        for idx, (text, font, is_planet) in enumerate(lines):
            y_cursor += font * scale * line_gap
            if idx == 0:
                # prvi redak je uvijek zaglavlje (broj znaka) - vidi _build_house_lines
                weight, color, opacity = "400", _COLOR_INK, ' opacity="0.6"'
            elif text == "Lagna":
                weight, color, opacity = "700", "#7445a4", ''
            elif is_planet:
                weight, color, opacity = "700", label_color(text) or _COLOR_INK, ''
            else:
                weight, color, opacity = "400", _COLOR_MUTED, ''
            font_style = ' font-style="italic"' if text == "Lagna" else ''
            svg_parts.append(
                f'<text x="{cx:.1f}" y="{y_cursor:.1f}" text-anchor="middle" '
                f'dominant-baseline="middle" font-size="{font * scale:.1f}" '
                f'font-weight="{weight}"{font_style} fill="{color}"{opacity}>{text}</text>'
            )

    svg_parts.append("</svg>")
    return "".join(svg_parts)


def group_planets_by_house(planet_house_map: Dict[str, int]) -> Dict[int, List[str]]:
    """
    planet_house_map: {naziv_planeta: broj_kuce}
    Vraća: {broj_kuce: [nazivi_planeta]}
    """
    grouped: Dict[int, List[str]] = {}
    for planet, house in planet_house_map.items():
        grouped.setdefault(house, []).append(planet)
    return grouped
