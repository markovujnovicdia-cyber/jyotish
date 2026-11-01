"""
Mjesečne i dnevne aktivacije (3.6 u specifikaciji) - Mjesec kao
KRATKOTRAJNI OKIDAČ, NE kao samostalan dokaz velikog događaja.

Ponovno koristi core.synastry.transit_activations.compute_link_activations
(za "Mjesec prelazi preko natalne sinastrijske veze" i za prepoznavanje
kad su spori tranziti aktivni istog dana) - ne duplicira geometriju
aspekta/konjunkcije. Preostale provjere (isti znak, ulazak u UL/A7, ulazak
u nakšatru ključne točke) su izravne, jednostavne usporedbe znaka/nakšatre.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Callable, List, Optional

from core.nakshatra import get_nakshatra
from core.ephemeris import get_planet_positions
from core.time_utils import utc_to_julian_day
from core.natal import NatalContext
from core.synastry.config import SynastryConfig, SLOW_TRANSIT_PLANETS
from core.synastry.transit_activations import compute_link_activations
from core.synastry.models import NatalSynastryLink, MoonTriggerDay


def _combine_utc(d) -> datetime:
    return datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc).replace(hour=12)


def compute_moon_daily_highlights(
    ctx_a: NatalContext, ctx_b: NatalContext, natal_links: List[NatalSynastryLink],
    target_date: date,
    seventh_lord_a: str, seventh_lord_b: str, darakaraka_a: str, darakaraka_b: str,
    config: SynastryConfig,
) -> MoonTriggerDay:
    at_dt = _combine_utc(target_date)
    jd_ut = utc_to_julian_day(at_dt)
    transit_positions = get_planet_positions(jd_ut)
    moon_sign_idx = transit_positions["Mjesec"].sign_index
    moon_nak = get_nakshatra(transit_positions["Mjesec"].longitude)

    notes: List[str] = []

    # a) Mjesec prelazi preko natalne sinastrijske veze (samo Mjesec kao tranzitni planet).
    # Mjesec je brz i ostaje u istom znaku ~2-3 dana, pa "isti znak" aktivacije lako
    # pogode DESETKE pohranjenih veza istog dana (svaka veza koja uključuje BILO KOJI
    # planet u tom znaku) - prikazuju se samo NAJJAČE (top 8) da izvještaj ostane čitljiv,
    # uz napomenu o ukupnom broju (isti obrazac kao u "Aktivacija natalne sinastrije
    # tranzitom" tabu prediktivne sinastrije).
    moon_only = {"Mjesec": transit_positions["Mjesec"]}
    moon_link_activations = sorted(
        compute_link_activations(natal_links, moon_only, config), key=lambda a: a.strength, reverse=True,
    )
    _MOON_LINK_NOTE_CAP = 8
    for act in moon_link_activations[:_MOON_LINK_NOTE_CAP]:
        notes.append(
            f"Tranzitni Mjesec prelazi preko natalne veze {act.link.person_a_object} — "
            f"{act.link.person_b_object} ({', '.join(act.activation_types)})."
        )
    if len(moon_link_activations) > _MOON_LINK_NOTE_CAP:
        notes.append(
            f"... i još {len(moon_link_activations) - _MOON_LINK_NOTE_CAP} sličnih natalnih veza "
            f"aktiviranih tranzitnim Mjesecom istog dana (prikazano {_MOON_LINK_NOTE_CAP} najjačih)."
        )

    # b) Mjesec preko Venere/Marsa/Mjeseca/vladara 7. (bilo koje osobe) - isti znak
    key_planet_checks = [
        ("Venera (A)", ctx_a.positions["Venera"].sign_index), ("Venera (B)", ctx_b.positions["Venera"].sign_index),
        ("Mars (A)", ctx_a.positions["Mars"].sign_index), ("Mars (B)", ctx_b.positions["Mars"].sign_index),
        ("Mjesec (A)", ctx_a.positions["Mjesec"].sign_index), ("Mjesec (B)", ctx_b.positions["Mjesec"].sign_index),
        (f"vladar 7. osobe A ({seventh_lord_a})", ctx_a.positions[seventh_lord_a].sign_index),
        (f"vladar 7. osobe B ({seventh_lord_b})", ctx_b.positions[seventh_lord_b].sign_index),
    ]
    for label, sign_idx in key_planet_checks:
        if moon_sign_idx == sign_idx:
            notes.append(f"Tranzitni Mjesec prelazi preko znaka {label}.")

    # c) Mjesec ulazi u UL ili A7 (bilo koje osobe)
    ul_a7_checks = [
        ("UL osobe A", ctx_a.special_points["UL_sign_index"]), ("A7 osobe A", ctx_a.special_points["A7_sign_index"]),
        ("UL osobe B", ctx_b.special_points["UL_sign_index"]), ("A7 osobe B", ctx_b.special_points["A7_sign_index"]),
    ]
    for label, sign_idx in ul_a7_checks:
        if moon_sign_idx == sign_idx:
            notes.append(f"Tranzitni Mjesec ulazi u {label}.")

    # d) Mjesec ulazi u nakšatru ključne sinastrijske točke (Ascendent/Darakaraka obje osobe)
    key_nak_checks = [
        ("Ascendenta osobe A", get_nakshatra(ctx_a.ascendant_longitude).index),
        ("Ascendenta osobe B", get_nakshatra(ctx_b.ascendant_longitude).index),
        ("Darakarake osobe A", get_nakshatra(ctx_a.positions[darakaraka_a].longitude).index),
        ("Darakarake osobe B", get_nakshatra(ctx_b.positions[darakaraka_b].longitude).index),
    ]
    for label, nak_idx in key_nak_checks:
        if moon_nak.index == nak_idx:
            notes.append(f"Tranzitni Mjesec ulazi u nakšatru {label}.")

    # e) Mjesec povezuje DVA spora tranzitna pokazatelja aktivna istog dana
    all_activations = compute_link_activations(natal_links, transit_positions, config)
    active_slow = sorted({a.transit_planet for a in all_activations if a.transit_planet in SLOW_TRANSIT_PLANETS})
    moon_active = any(a.transit_planet == "Mjesec" for a in all_activations)
    if moon_active and len(active_slow) >= 2:
        notes.append(
            f"Tranzitni Mjesec aktivan je ISTOG dana kad su aktivna barem dva spora tranzita "
            f"({', '.join(active_slow)}) - Mjesec ovdje djeluje kao kratkotrajni okidač koji "
            f"povezuje sporije pokazatelje."
        )

    return MoonTriggerDay(date_label=target_date.isoformat(), notes=notes)


def compute_moon_trigger_days_over_range(
    ctx_a: NatalContext, ctx_b: NatalContext, natal_links: List[NatalSynastryLink],
    start_date: date, end_date: date,
    seventh_lord_a: str, seventh_lord_b: str, darakaraka_a: str, darakaraka_b: str,
    config: SynastryConfig,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> List[MoonTriggerDay]:
    """Vraća SAMO dane koji imaju barem jednu bilježenu Mjesečevu aktivaciju (prazni dani se preskaču)."""
    days: List[MoonTriggerDay] = []
    current = start_date
    total_days = max((end_date - start_date).days, 1)
    while current <= end_date:
        day_result = compute_moon_daily_highlights(
            ctx_a, ctx_b, natal_links, current,
            seventh_lord_a, seventh_lord_b, darakaraka_a, darakaraka_b, config,
        )
        if day_result.notes:
            days.append(day_result)
        if progress_callback:
            progress_callback(min(1.0, (current - start_date).days / total_days))
        current = current + timedelta(days=1)
    return days
