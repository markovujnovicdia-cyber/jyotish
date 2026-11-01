"""
Prediktivna sinastrija - glavni ulaz (Faza 4): kombinira tranzite prema
objema natalnim kartama, aktivaciju natalne sinastrije tranzitom (core/
synastry/transit_activations.py), dvostruki tranzit Jupitera i Saturna, i
Vimshottari Dasha aktivacije (core/synastry/dasha_activations.py) u jedan
"snapshot" za odabrani datum, te vremensku crtu (niz snapshotova kroz
raspon datuma).

Ponovno koristi core.transits.compute_transits (natalni izračun, ne
duplicira geometriju) i samo dodaje polja specifična za sinastriju (kuća
od Upapade, dispozitor).

NAPOMENA O OPSEGU (Faza 4, dosljedno redoslijedu iz specifikacije):
Varshaphala/Mudda Dasha aktivacije, fina mjesečna/dnevna analiza (Mjesec
kao kratkotrajni okidač preko konkretnih dana), naprednо keširanje/
optimizacija i PDF/JSON/CSV izvoz planirani su za Fazu 5 - OVDJE se
tranziti računaju izravno (swisseph poziv po datumu), bez dodatnog
keširanja - za razumne raspone (do ~2 godine dnevno) to je dovoljno brzo;
UI prikazuje traku napretka (st.progress) za veće raspone.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional

from core.constants import RASHI_LORD
from core.houses import whole_sign_house
from core.nakshatra import get_nakshatra
from core.ephemeris import get_planet_positions
from core.transits import compute_transits
from core.time_utils import utc_to_julian_day
from core.natal import NatalContext
from core.synastry.config import SynastryConfig, PREDICTIVE_ACTIVATION_HOUSES, SLOW_TRANSIT_PLANETS
from core.synastry.transit_activations import compute_link_activations
from core.synastry.dasha_activations import compute_dasha_mutual_activation
from core.synastry.models import (
    PersonTransitRow, DoubleTransitResult, PredictiveSnapshot, TimelinePoint,
    NatalSynastryLink,
)


def build_transit_rows(ctx: NatalContext, jd_ut: float) -> Dict[str, PersonTransitRow]:
    raw = compute_transits(jd_ut, ctx.ascendant_longitude, ctx.positions["Mjesec"].longitude)
    ul_sign_idx = ctx.special_points["UL_sign_index"]
    rows = {}
    for name, r in raw.items():
        nak = get_nakshatra(r.longitude)
        house_from_ul = whole_sign_house(int(r.longitude % 360.0 // 30), ul_sign_idx)
        rows[name] = PersonTransitRow(
            planet=name, sign=r.sign, longitude=r.longitude,
            house_from_ascendant=r.house_from_ascendant, house_from_moon=r.house_from_moon,
            house_from_upapada=house_from_ul,
            nakshatra=nak.name, pada=nak.pada,
            dispositor=RASHI_LORD[r.sign],
            is_retrograde=r.is_retrograde,
            is_slow=name in SLOW_TRANSIT_PLANETS,
        )
    return rows


def compute_double_transit(
    ctx_a: NatalContext, ctx_b: NatalContext,
    transit_rows_a: Dict[str, PersonTransitRow], transit_rows_b: Dict[str, PersonTransitRow],
    seventh_lord_a: str, seventh_lord_b: str, darakaraka_a: str, darakaraka_b: str,
) -> DoubleTransitResult:
    def _hits(ctx: NatalContext, rows: Dict[str, PersonTransitRow], planet: str, seventh_lord: str, darakaraka: str) -> List[str]:
        row = rows[planet]
        hits = []
        if row.house_from_ascendant in PREDICTIVE_ACTIVATION_HOUSES:
            hits.append(f"{row.house_from_ascendant}. kuća")
        key_signs = {
            "Venera": ctx.positions["Venera"].sign_index,
            "Mjesec": ctx.positions["Mjesec"].sign_index,
            "Darakaraka": ctx.positions[darakaraka].sign_index,
            "Vladar 7.": ctx.positions[seventh_lord].sign_index,
            "UL": ctx.special_points["UL_sign_index"],
            "A7": ctx.special_points["A7_sign_index"],
        }
        transit_sign_idx = int(row.longitude % 360.0 // 30)
        for label, sign_idx in key_signs.items():
            if transit_sign_idx == sign_idx:
                hits.append(label)
        return hits

    jup_hits_a = _hits(ctx_a, transit_rows_a, "Jupiter", seventh_lord_a, darakaraka_a)
    sat_hits_a = _hits(ctx_a, transit_rows_a, "Saturn", seventh_lord_a, darakaraka_a)
    jup_hits_b = _hits(ctx_b, transit_rows_b, "Jupiter", seventh_lord_b, darakaraka_b)
    sat_hits_b = _hits(ctx_b, transit_rows_b, "Saturn", seventh_lord_b, darakaraka_b)

    both_a = bool(jup_hits_a) and bool(sat_hits_a)
    both_b = bool(jup_hits_b) and bool(sat_hits_b)
    simultaneous = both_a and both_b

    if simultaneous:
        note = (
            "Jupiter I Saturn ISTODOBNO aktiviraju partnerske pokazatelje u OBJE karte - "
            "naglašeno razdoblje za temu odnosa kod oboje istovremeno."
        )
    elif both_a or both_b:
        who = "osobe A" if both_a else "osobe B"
        note = f"Jupiter i Saturn istodobno aktiviraju partnerske pokazatelje kod {who} (ne kod obje osobe)."
    else:
        note = "Nema istodobne Jupiter+Saturn aktivacije partnerskih pokazatelja unutar promatranog skupa."

    return DoubleTransitResult(
        jupiter_hits_a=jup_hits_a, saturn_hits_a=sat_hits_a,
        jupiter_hits_b=jup_hits_b, saturn_hits_b=sat_hits_b,
        simultaneous_both_charts=simultaneous, note=note,
    )


def compute_predictive_snapshot(
    ctx_a: NatalContext, ctx_b: NatalContext,
    at_dt_utc: datetime,
    natal_links: List[NatalSynastryLink],
    seventh_lord_a: str, seventh_lord_b: str,
    darakaraka_a: str, darakaraka_b: str,
    asc_lord_a: str, asc_lord_b: str,
    config: SynastryConfig,
) -> PredictiveSnapshot:
    """
    NAPOMENA: lokacija (lat/lon) NIJE parametar ovdje - tranzitne dužine
    planeta su geocentrične i ne ovise o mjestu promatranja; lokacija bi
    bila potrebna samo za izračun TRANZITNOG ascendenta (zaseban koncept,
    nije ovdje implementiran), ne za položaje planeta korištene u ovoj
    analizi (koje se uspoređuju s NATALNIM ascendentom svake osobe).
    """
    jd_ut = utc_to_julian_day(at_dt_utc)
    transit_positions = get_planet_positions(jd_ut)

    transits_a = build_transit_rows(ctx_a, jd_ut)
    transits_b = build_transit_rows(ctx_b, jd_ut)

    activations = compute_link_activations(natal_links, transit_positions, config)
    double_transit = compute_double_transit(
        ctx_a, ctx_b, transits_a, transits_b, seventh_lord_a, seventh_lord_b, darakaraka_a, darakaraka_b,
    )
    dasha_result = compute_dasha_mutual_activation(
        ctx_a, ctx_b, ctx_a.utc_dt, ctx_b.utc_dt, at_dt_utc,
        asc_lord_a, seventh_lord_a, darakaraka_a, asc_lord_b, seventh_lord_b, darakaraka_b,
    )

    return PredictiveSnapshot(
        date_label=at_dt_utc.date().isoformat(),
        transits_a=transits_a, transits_b=transits_b,
        activations=activations, double_transit=double_transit, dasha_result=dasha_result,
    )


_THEME_KEYWORDS = {
    "Emocionalne teme": {"Mjesec"},
    "Privlačnost": {"Venera", "Mars"},
    "Komunikacija": {"Merkur"},
    "Stabilnost": {"Saturn"},
    "Konflikt": {"Mars", "Saturn", "Rahu", "Ketu"},
    "Susret/približavanje": {"Venera", "Jupiter"},
    "Formalizacija odnosa": {"Saturn", "Jupiter"},
    "Udaljavanje/završavanje ciklusa": {"Saturn", "Ketu"},
}


def _themes_for_planet(planet: str) -> List[str]:
    return [theme for theme, planets in _THEME_KEYWORDS.items() if planet in planets]


def compute_timeline(
    ctx_a: NatalContext, ctx_b: NatalContext,
    start_date, end_date, step_days: int,
    natal_links: List[NatalSynastryLink],
    seventh_lord_a: str, seventh_lord_b: str,
    darakaraka_a: str, darakaraka_b: str,
    asc_lord_a: str, asc_lord_b: str,
    config: SynastryConfig,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> List[TimelinePoint]:
    """
    step_days: 1 (dnevno), 7 (tjedno) ili ~30 (mjesečno). Nazivi tema NE
    impliciraju siguran događaj (spec: "predstavljaju astrološke teme").
    """
    points: List[TimelinePoint] = []
    current = start_date
    total_days = max((end_date - start_date).days, 1)

    while current <= end_date:
        at_dt = _combine_utc(current)
        jd_ut = utc_to_julian_day(at_dt)
        transit_positions = get_planet_positions(jd_ut)
        activations = compute_link_activations(natal_links, transit_positions, config)

        total_strength = sum(a.strength for a in activations)
        active_slow = sorted({a.transit_planet for a in activations if a.is_slow_planet})

        from core.dasha import get_current_dasha_5_levels
        maha_a, *_ = get_current_dasha_5_levels(ctx_a.positions["Mjesec"].longitude, ctx_a.utc_dt, at_dt)
        maha_b, *_ = get_current_dasha_5_levels(ctx_b.positions["Mjesec"].longitude, ctx_b.utc_dt, at_dt)
        active_dasha_lords = sorted({maha_a.lord, maha_b.lord})

        themes = sorted({t for a in activations for t in _themes_for_planet(a.transit_planet)})
        top_notes = [a.interpretation for a in activations[:3]]
        activation_strengths = [
            (a.transit_planet, a.strength, _themes_for_planet(a.transit_planet)) for a in activations
        ]

        points.append(TimelinePoint(
            date_label=current.isoformat(), total_strength=round(total_strength, 2),
            active_slow_transits=active_slow, active_dasha_lords=active_dasha_lords,
            themes=themes, top_notes=top_notes, activation_strengths=activation_strengths,
        ))

        if progress_callback:
            progress_callback(min(1.0, (current - start_date).days / total_days))

        current = current + timedelta(days=step_days)

    return points


def _combine_utc(d) -> datetime:
    return datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc).replace(hour=12)
