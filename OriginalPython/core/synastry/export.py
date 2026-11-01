"""
Izvoz sinastrijske analize (poglavlje 13 u specifikaciji): JSON, CSV
(kontakti i vremenska crta), PDF (iz već izgrađenog tekstualnog
izvještaja) i SVG karta (izravan download već generiranog SVG-a, bez
rasterizacije - vidi napomenu niže).

JSON izvoz sadrži SVE što specifikacija traži: verziju algoritma,
postavke izračuna, ayanamshu, vrstu čvorova, sustav kuća, datum izračuna,
ulazne podatke, rezultate i detalje bodovanja.

PDF: koristi core.synastry.report tekstualni izvještaj kao izvor (ne
duplicira sadržaj - samo ga preoblikuje u PDF). Koristi macOS sistemski
"Arial Unicode.ttf" font za ispravan prikaz hrvatskih dijakritika (č/ć/š/
ž/đ) - dosljedno s "za macOS" opsegom aplikacije. Ako font nije pronađen
(rijetko, npr. izmijenjena macOS instalacija), koristi se ugrađeni
Helvetica font BEZ ispravnih dijakritika kao rezerva - jasno označeno.

Slika karte: SVG (core.ui.north_indian_chart.render_north_indian_svg) je
već vektorska slika - izvoz je izravan download tog SVG-a, BEZ
rasterizacije u PNG (to bi zahtijevalo dodatnu ovisnost poput cairosvg,
izvan opsega ove aplikacije).
"""

import csv
import io
import json
import os
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from typing import Dict, List, Optional

from core.synastry import report as report_module
from core.synastry.models import (
    ConjunctionContact, GrahaDrishtiContact, TimelinePoint,
)

_UNICODE_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def _json_default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (frozenset, set)):
        return sorted(obj)
    if is_dataclass(obj):
        return asdict(obj)
    return str(obj)


def build_json_export(
    person_a, person_b, relationship_type: str, config,
    overlay_a_to_b, overlay_b_to_a,
    drishti_a_to_b: List[GrahaDrishtiContact], drishti_b_to_a: List[GrahaDrishtiContact],
    conjunctions: List[ConjunctionContact],
    nakshatra_result=None, ashtakoota_result=None, kuja_comparison=None,
    significators_result=None, navamsha_result=None, score_result=None,
) -> str:
    payload = {
        "algorithm_version": report_module.VERSION,
        "calculation_date_utc": datetime.now(timezone.utc).isoformat(),
        "settings": {
            "ayanamsha": "Lahiri",
            "node_type": "Mean Node",
            "house_system": "Whole Sign" + (" + Bhava Chalit (dodatni)" if config.use_bhava_chalit else ""),
            **config.settings_summary(),
        },
        "input": {
            "person_a": {
                "name": person_a.name, "birth_date": person_a.birth_date, "birth_time": person_a.birth_time,
                "birth_place": person_a.birth_place, "time_confirmed": person_a.time_confirmed,
            },
            "person_b": {
                "name": person_b.name, "birth_date": person_b.birth_date, "birth_time": person_b.birth_time,
                "birth_place": person_b.birth_place, "time_confirmed": person_b.time_confirmed,
            },
            "relationship_type": relationship_type,
        },
        "results": {
            "house_overlay_a_to_b": [asdict(r) for r in overlay_a_to_b],
            "house_overlay_b_to_a": [asdict(r) for r in overlay_b_to_a],
            "graha_drishti_a_to_b": [asdict(c) for c in drishti_a_to_b],
            "graha_drishti_b_to_a": [asdict(c) for c in drishti_b_to_a],
            "conjunctions": [asdict(c) for c in conjunctions],
        },
    }
    if nakshatra_result is not None:
        payload["results"]["nakshatra_synastry"] = asdict(nakshatra_result)
    if ashtakoota_result is not None:
        payload["results"]["ashtakoota"] = asdict(ashtakoota_result)
    if kuja_comparison is not None:
        payload["results"]["kuja_dosha"] = asdict(kuja_comparison)
    if significators_result is not None:
        payload["results"]["relationship_significators"] = asdict(significators_result)
    if navamsha_result is not None:
        payload["results"]["navamsha_synastry"] = asdict(navamsha_result)
    if score_result is not None:
        payload["scoring"] = {
            "categories": {cat: asdict(score) for cat, score in score_result.categories.items()},
            "not_available": score_result.not_available,
        }

    return json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default)


def build_csv_contacts(
    drishti_a_to_b: List[GrahaDrishtiContact], drishti_b_to_a: List[GrahaDrishtiContact],
    conjunctions: List[ConjunctionContact],
) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Vrsta", "Izvor (A)", "Cilj (B)", "Udaljenost/Razmak", "Snaga/Egzaktnost", "Kratko tumačenje"])
    for c in drishti_a_to_b + drishti_b_to_a:
        writer.writerow([
            "Graha Drishti", f"{c.from_planet} ({c.source_person})", f"{c.to_planet} ({c.target_person})",
            f"{c.house_distance}. kuća", c.strength_label, c.short_interpretation,
        ])
    for c in conjunctions:
        writer.writerow([
            "Konjunkcija", f"{c.person_a_object} (A)", f"{c.person_b_object} (B)",
            f"{c.degree_distance:.2f}°", "egzaktna" if c.is_exact else "unutar orba", c.short_interpretation,
        ])
    return buffer.getvalue()


def build_csv_timeline(points: List[TimelinePoint]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Datum", "Ukupna jačina", "Aktivni spori tranziti", "Aktivni dasha vladari", "Teme"])
    for p in points:
        writer.writerow([
            p.date_label, p.total_strength,
            ", ".join(p.active_slow_transits), ", ".join(p.active_dasha_lords), ", ".join(p.themes),
        ])
    return buffer.getvalue()


def _find_unicode_font() -> Optional[str]:
    for path in _UNICODE_FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def build_pdf_report(report_text: str, title: str) -> bytes:
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    # VAŽNO: multi_cell() u fpdf2 PO ZADANOM ne vraća kursor na lijevu
    # marginu (new_x zadano na XPos.RIGHT) - bez eksplicitnog new_x/new_y
    # svaki sljedeći poziv "nasljeđuje" X blizu desnog ruba stranice, dok
    # se dostupna širina ne istroši do nule i fpdf ne baci
    # "Not enough horizontal space to render a single character".
    # Zato SVAKI poziv niže eksplicitno navodi new_x=LMARGIN, new_y=NEXT.
    def _cell(h, text):
        pdf.multi_cell(0, h, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    font_path = _find_unicode_font()
    font_name = "AppFont" if font_path else "Helvetica"
    if font_path:
        pdf.add_font("AppFont", "", font_path)

    pdf.set_font(font_name, size=16)
    _cell(10, title)
    pdf.ln(2)
    if not font_path:
        pdf.set_font(font_name, size=8)
        pdf.set_text_color(150, 0, 0)
        _cell(5, "(Napomena: sistemski Unicode font nije pronađen - hrvatski dijakritici mogu biti netočno prikazani.)")
        pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    pdf.set_font(font_name, size=10)
    for raw_line in report_text.split("\n"):
        line = raw_line.strip()
        if line.startswith("### "):
            pdf.set_font_size(11)
            _cell(6, line[4:])
            pdf.set_font_size(10)
        elif line.startswith("## "):
            pdf.ln(1)
            pdf.set_font_size(13)
            _cell(7, line[3:])
            pdf.set_font_size(10)
        elif line.startswith("# "):
            pdf.set_font_size(15)
            _cell(8, line[2:])
            pdf.set_font_size(10)
        elif line == "":
            pdf.ln(3)
        else:
            _cell(5, line.lstrip("-").strip() if line.startswith("- ") else line)

    return bytes(pdf.output())
