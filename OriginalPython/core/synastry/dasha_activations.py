"""
Vimshottari Dasha aktivacije u sinastriji (3.4 u specifikaciji).

Koristi ISKLJUČIVO core.dasha.get_current_dasha_5_levels (Maha/Antar/
Pratyantar/Sookshma/Prana - već implementirano u natalnoj karti) i
core.houses.houses_ruled_by_planet (dodano u Fazi 2) - ne duplicira
izračun dasha perioda.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List

from core.constants import RASHI
from core.houses import houses_ruled_by_planet
from core.nakshatra import get_nakshatra
from core.varga import d9_navamsha_sign_index
from core.dasha import get_current_dasha_5_levels
from core.planet_strength import NATURAL_FRIENDS
from core.natal import NatalContext
from core.synastry.models import DashaProfile, DashaMutualActivationResult


def _relation_text(maha_lord: str, target: str, target_label: str) -> str:
    if maha_lord == target:
        return f"izravna (Maha Dasha vladar JEST {target_label})"
    if target in NATURAL_FRIENDS.get(maha_lord, set()):
        return f"prirodno prijateljska s {target_label} ({target})"
    if maha_lord in NATURAL_FRIENDS.get(target, set()):
        return f"prirodno prijateljska s {target_label} ({target})"
    return f"bez izravne prirodne veze s {target_label} ({target})"


def build_dasha_profile(
    ctx: NatalContext, person_label: str, birth_dt_utc: datetime, at_dt_utc: datetime,
    seventh_lord: str, darakaraka: str,
) -> DashaProfile:
    moon_lon = ctx.positions["Mjesec"].longitude
    maha, antar, pratyantar, sookshma, prana = get_current_dasha_5_levels(moon_lon, birth_dt_utc, at_dt_utc)

    maha_lord = maha.lord
    maha_lord_pos = ctx.positions[maha_lord]
    ul_lord = RASHI[ctx.special_points["UL_sign_index"]]
    from core.constants import RASHI_LORD
    ul_lord_planet = RASHI_LORD[ul_lord]

    return DashaProfile(
        person_label=person_label,
        maha_lord=maha_lord, antar_lord=antar.lord, pratyantar_lord=pratyantar.lord,
        maha_start=maha.start.date().isoformat(), maha_end=maha.end.date().isoformat(),
        antar_start=antar.start.date().isoformat(), antar_end=antar.end.date().isoformat(),
        maha_houses_ruled=houses_ruled_by_planet(maha_lord, ctx.ascendant_sign_index),
        maha_lord_natal_sign=maha_lord_pos.sign,
        maha_lord_natal_nakshatra=get_nakshatra(maha_lord_pos.longitude).name,
        maha_lord_d9_sign=RASHI[d9_navamsha_sign_index(maha_lord_pos.longitude)],
        relation_to_seventh=_relation_text(maha_lord, seventh_lord, "vladara 7. kuće"),
        relation_to_venus=_relation_text(maha_lord, "Venera", "Venere"),
        relation_to_darakaraka=_relation_text(maha_lord, darakaraka, "Darakarake"),
        relation_to_upapada=_relation_text(maha_lord, ul_lord_planet, "vladara UL"),
    )


def find_dasha_mutual_activations(
    profile_a: DashaProfile, profile_b: DashaProfile,
    asc_lord_a: str, seventh_lord_a: str, darakaraka_a: str,
    asc_lord_b: str, seventh_lord_b: str, darakaraka_b: str,
) -> List[str]:
    notes: List[str] = []

    if profile_a.maha_lord == profile_b.maha_lord:
        notes.append(f"Oboje su trenutno u Maha Dashi ISTOG planeta ({profile_a.maha_lord}) - snažno dijeljeno razdoblje.")
    elif profile_b.maha_lord in NATURAL_FRIENDS.get(profile_a.maha_lord, set()) or profile_a.maha_lord in NATURAL_FRIENDS.get(profile_b.maha_lord, set()):
        notes.append(f"Maha Dasha vladari ({profile_a.maha_lord} kod A, {profile_b.maha_lord} kod B) su prirodni prijatelji.")

    cross_checks = [
        (profile_a.maha_lord, seventh_lord_b, "A", "B", "vladar 7. kuće"),
        (profile_a.maha_lord, darakaraka_b, "A", "B", "Darakaraka"),
        (profile_a.maha_lord, asc_lord_b, "A", "B", "vladar Ascendenta"),
        (profile_b.maha_lord, seventh_lord_a, "B", "A", "vladar 7. kuće"),
        (profile_b.maha_lord, darakaraka_a, "B", "A", "Darakaraka"),
        (profile_b.maha_lord, asc_lord_a, "B", "A", "vladar Ascendenta"),
    ]
    for maha_lord, target_planet, source_label, target_label, role in cross_checks:
        if maha_lord == target_planet:
            notes.append(
                f"Maha Dasha osobe {source_label} ({maha_lord}) je BAŠ {role} osobe {target_label} - "
                f"aktivira temu partnerstva/identiteta kod {target_label}."
            )

    return notes


def compute_dasha_mutual_activation(
    ctx_a: NatalContext, ctx_b: NatalContext, birth_dt_a: datetime, birth_dt_b: datetime, at_dt_utc: datetime,
    asc_lord_a: str, seventh_lord_a: str, darakaraka_a: str,
    asc_lord_b: str, seventh_lord_b: str, darakaraka_b: str,
) -> DashaMutualActivationResult:
    profile_a = build_dasha_profile(ctx_a, "A", birth_dt_a, at_dt_utc, seventh_lord_a, darakaraka_a)
    profile_b = build_dasha_profile(ctx_b, "B", birth_dt_b, at_dt_utc, seventh_lord_b, darakaraka_b)
    mutual_notes = find_dasha_mutual_activations(
        profile_a, profile_b, asc_lord_a, seventh_lord_a, darakaraka_a, asc_lord_b, seventh_lord_b, darakaraka_b,
    )
    return DashaMutualActivationResult(profile_a=profile_a, profile_b=profile_b, mutual_notes=mutual_notes)
