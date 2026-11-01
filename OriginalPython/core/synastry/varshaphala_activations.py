"""
Varshaphala i Mudda Dasha aktivacije u sinastriji (3.5 u specifikaciji).

Ponovno koristi core.varshaphala.compute_varshaphala (solarni povratak,
Muntha, Varsheshwara, Mudda Dasha, Tajika Ithasala/Isarapha - sve već
implementirano) i core.dasha.find_current_period - ne duplicira nijedan
izračun.

VAŽNO (spec 3.5: "Nemoj miješati Parashari Graha Drishti i Tajika
aspekte"): ovaj modul NE računa Parashari Graha Drishti za godišnju kartu
- Tajika Ithasala/Isarapha parovi (već izračunati u core/varshaphala.py)
su JEDINA aspektna metoda ovdje, i eksplicitno su tako označeni u
rezultatu (tajika_ithasala_count/tajika_isarapha_count) i u UI-u/izvještaju.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple

from core.constants import RASHI, RASHI_LORD, PLANET_ORDER
from core.houses import whole_sign_house
from core.dasha import find_current_period
from core.varshaphala import compute_varshaphala, VarshaphalaResult
from core.natal import NatalContext
from core.synastry.config import PREDICTIVE_ACTIVATION_HOUSES
from core.synastry.models import VarshaphalaProfile, VarshaphalaSynastryResult, NatalSynastryLink


def build_varshaphala_profile(
    person, ctx: NatalContext, person_label: str, target_year: int, at_dt_utc: datetime, seventh_lord: str,
) -> Tuple[VarshaphalaProfile, VarshaphalaResult]:
    birth_year, birth_month, birth_day = (int(x) for x in person.birth_date.split("-"))
    result = compute_varshaphala(
        ctx.positions["Sunce"].longitude, ctx.ascendant_longitude,
        birth_year, birth_month, birth_day, target_year,
        person.latitude, person.longitude,
        ctx.positions["Mjesec"].longitude, ctx.utc_dt,
    )

    asc_sign_idx = int(result.ascendant_longitude % 360.0 // 30)
    muntha_lord = RASHI_LORD[result.muntha_sign]
    seventh_sign_idx = (asc_sign_idx + 6) % 12
    varsha_seventh_lord = RASHI_LORD[RASHI[seventh_sign_idx]]

    venus_house = whole_sign_house(result.planet_positions["Venera"].sign_index, asc_sign_idx)
    moon_house = whole_sign_house(result.planet_positions["Mjesec"].sign_index, asc_sign_idx)
    saturn_house = whole_sign_house(result.planet_positions["Saturn"].sign_index, asc_sign_idx)
    jupiter_house = whole_sign_house(result.planet_positions["Jupiter"].sign_index, asc_sign_idx)

    # Odabrana buduća/prošla karta nije nužno aktivna na datum promatranja.
    # U tom slučaju ne smije se izmišljati aktivna Mudda daša.
    active_mudda = next((d for d in result.mudda_dasha
                         if d.start <= at_dt_utc < d.end), None)
    winner = result.varsheshwara.get("winner") if result.varsheshwara else None
    varsheshwara_planet = winner.planet if winner else None

    profile = VarshaphalaProfile(
        person_label=person_label, target_year=target_year,
        ascendant_sign=result.ascendant_sign,
        muntha_sign=result.muntha_sign, muntha_lord=muntha_lord,
        varsheshwara_planet=varsheshwara_planet,
        seventh_sign=RASHI[seventh_sign_idx], seventh_lord=varsha_seventh_lord,
        venus_house=venus_house, moon_house=moon_house,
        saturn_house=saturn_house, jupiter_house=jupiter_house,
        active_mudda_dasha_lord=active_mudda.lord if active_mudda else None,
        tajika_ithasala_count=len(result.ithasala_pairs),
        tajika_isarapha_count=len(result.isarapha_pairs),
    )
    return profile, result


def _sensitive_signs(profile: VarshaphalaProfile, result: VarshaphalaResult) -> Dict[str, int]:
    return {
        "Varsha Lagna": int(result.ascendant_longitude % 360.0 // 30),
        "Muntha": RASHI.index(profile.muntha_sign),
        "godišnja 7. kuća": RASHI.index(profile.seventh_sign),
        "Varsha Arudha Lagna": RASHI.index(result.arudha_lagna_sign),
    }


def _planets_on_sensitive_points(ctx_other: NatalContext, sensitive: Dict[str, int], other_label: str) -> List[str]:
    hits = []
    for label, sign_idx in sensitive.items():
        for planet in PLANET_ORDER:
            if ctx_other.positions[planet].sign_index == sign_idx:
                hits.append(f"{planet} ({other_label}) na {label} ({RASHI[sign_idx]})")
    return hits


def compute_varshaphala_synastry(
    person_a, ctx_a: NatalContext, person_b, ctx_b: NatalContext,
    target_year_a: int, target_year_b: int, at_dt_utc: datetime,
    seventh_lord_a: str, seventh_lord_b: str,
    natal_links: List[NatalSynastryLink],
) -> VarshaphalaSynastryResult:
    profile_a, result_a = build_varshaphala_profile(person_a, ctx_a, "A", target_year_a, at_dt_utc, seventh_lord_a)
    profile_b, result_b = build_varshaphala_profile(person_b, ctx_b, "B", target_year_b, at_dt_utc, seventh_lord_b)

    sensitive_a = _sensitive_signs(profile_a, result_a)
    sensitive_b = _sensitive_signs(profile_b, result_b)
    b_on_a = _planets_on_sensitive_points(ctx_b, sensitive_a, "B")
    a_on_b = _planets_on_sensitive_points(ctx_a, sensitive_b, "A")

    mudda_activates: List[str] = []
    seen = set()
    for label, lord in (("A", profile_a.active_mudda_dasha_lord), ("B", profile_b.active_mudda_dasha_lord)):
        if lord is None:
            continue
        for link in natal_links:
            a_planet = link.person_a_object.split(" (")[0]
            b_planet = link.person_b_object.split(" (")[0]
            if lord in (a_planet, b_planet):
                key = (label, link.link_id)
                if key in seen:
                    continue
                seen.add(key)
                mudda_activates.append(
                    f"Mudda Dasha osobe {label} ({lord}) aktivira natalnu vezu {link.person_a_object} — {link.person_b_object}."
                )

    a_relevant = profile_a.venus_house in PREDICTIVE_ACTIVATION_HOUSES or profile_a.moon_house in PREDICTIVE_ACTIVATION_HOUSES
    b_relevant = profile_b.venus_house in PREDICTIVE_ACTIVATION_HOUSES or profile_b.moon_house in PREDICTIVE_ACTIVATION_HOUSES
    simultaneous = a_relevant and b_relevant

    notes = [
        "Metoda: Tajika Ithasala/Isarapha (core.varshaphala/tajika.py) - NE Parashari Graha Drishti. "
        "Broj Tajika Ithasala/Isarapha parova prikazan je odvojeno po osobi u profilu.",
    ]
    if simultaneous:
        notes.append(
            "Venera i/ili Mjesec su u partnerski relevantnoj kući (1,5,7,8,9,11) godišnje karte KOD OBOJE "
            "istovremeno - naglašeno razdoblje za temu odnosa u objema godišnjim kartama."
        )
    else:
        notes.append("Nema istodobne partnerski relevantne aktivacije Venere/Mjeseca u objema godišnjim kartama.")

    return VarshaphalaSynastryResult(
        profile_a=profile_a, profile_b=profile_b,
        b_planets_on_a_sensitive_points=b_on_a, a_planets_on_b_sensitive_points=a_on_b,
        mudda_dasha_activates_natal_link=mudda_activates,
        simultaneous_annual_activation=simultaneous,
        notes=notes,
    )
