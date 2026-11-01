#!/usr/bin/env python3
"""Generate the native oracle from unmodified OriginalPython modules.

Uses synthetic birth inputs, never the uploaded persons database.  Pin the same
Swiss Ephemeris C version and bundled data in both runtimes.  The original
Moshier fallback is sampled separately to quantify the backend change.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "OriginalPython"))
import swisseph as swe
from core.constants import RASHI, RASHI_LORD, SWE_PLANET_CODES
from core.dasha import get_current_dasha_5_levels, get_mahadasha_sequence
from core.ephemeris import SIDEREAL_FLAG, get_ascendant, get_planet_positions
from core.masa_pravesha import compute_masa_pravesha_sequence, _find_sun_longitude_jd
from core.nakshatra import get_nakshatra
from core.natal import compute_special_points
from core.sahams import compute_sahams
from core.special_points import compute_gulika_from_birth_data
from core.tajika import TAJIKA_PLANETS
from core.varga import d1_sign_index, d7_saptamsha_sign_index, d9_navamsha_sign_index, d10_dashamsha_sign_index, d12_dvadashamsha_sign_index
from core.varshaphala import compute_varshaphala, find_solar_return_jd
from core.varsheshwara import _DIGNITY_KSHETRA_POINTS, _kshetra_relationship, _hadda_lord, _drekkana_lord, _relationship_points
from core.planet_strength import compute_uchcha_bala

DATA = ROOT / "Packages/JyotishCore/Sources/JyotishCore/Resources/Ephemeris"
OUT = ROOT / "Packages/JyotishCore/Tests/JyotishCoreTests/Fixtures/PythonParity.json"
VARGAS = {"1": d1_sign_index, "7": d7_saptamsha_sign_index, "9": d9_navamsha_sign_index, "10": d10_dashamsha_sign_index, "12": d12_dvadashamsha_sign_index}
INPUTS = [
    ("europe", "1985-11-04T00:15:00+00:00", 45.45, 16.3667, "Europe/Zagreb", [2025, 2026]),
    ("southern", "2000-01-01T12:00:00+00:00", -33.8688, 151.2093, "Australia/Sydney", [2026]),
    ("south_asia", "1992-06-15T05:30:00+00:00", 28.6139, 77.2090, "Asia/Kolkata", [2025]),
    ("western", "1977-03-20T20:00:00+00:00", 40.7128, -74.0060, "America/New_York", [2026]),
]


def jd(dt):
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60 + (dt.second + dt.microsecond / 1e6) / 3600)


def period(p):
    return {"lord": p.lord, "start": p.start.timestamp(), "end": p.end.timestamp()}


def positions(positions, at_jd):
    result = []
    for name, p in positions.items():
        speed = swe.calc_ut(at_jd, SWE_PLANET_CODES["Rahu" if name == "Ketu" else name], SIDEREAL_FLAG)[0][3]
        nak = get_nakshatra(p.longitude)
        result.append({"name": name, "longitude": p.longitude, "speed": speed, "retrograde": p.is_retrograde,
                       "signIndex": p.sign_index, "degree": p.degree_in_sign,
                       "nakshatra": {"name": nak.name, "index": nak.index, "pada": nak.pada, "lord": nak.lord, "fractionElapsed": nak.fraction_elapsed},
                       "vargas": {key: fn(p.longitude) for key, fn in VARGAS.items()}})
    return result


def chart(at_jd, lat, lon, ps=None, asc=None):
    ps = ps if ps is not None else get_planet_positions(at_jd)
    asc = asc if asc is not None else get_ascendant(at_jd, lat, lon)
    return {"julianDay": at_jd, "ascendant": asc, "positions": positions(ps, at_jd),
            "ascendantVargas": {key: fn(asc) for key, fn in VARGAS.items()}}


def gulika(at_jd, local_date, lat, lon):
    try:
        g = compute_gulika_from_birth_data(at_jd, local_date, lat, lon)
        return {"longitude": g.longitude, "mandiLongitude": g.mandi_longitude, "mandiGhatikas": g.mandi_ghatikas,
                "isDayBirth": g.is_day_birth, "segmentNumber": g.segment_number, "weekdayForLord": g.weekday_for_lord,
                "periodStart": g.period_start.timestamp()}
    except Exception as exc:
        return {"error": type(exc).__name__}


def relation(r):
    return {"planetA": r.planet_a, "planetB": r.planet_b, "faster": r.faster, "slower": r.slower,
            "aspect": r.aspect, "orbDifference": r.orb_diff, "combinedOrb": r.combined_orb,
            "withinOrb": r.within_orb, "isApplying": r.is_applying, "isExact": r.is_exact,
            "isSeparating": r.is_separating, "relativeSpeed": r.relative_speed}


def candidate(c, ps):
    p = ps[c.planet]
    bala = {"kshetra": _DIGNITY_KSHETRA_POINTS[_kshetra_relationship(c.planet, p.sign_index)],
            "uchcha": compute_uchcha_bala(c.planet, p.longitude) / 3,
            "hadda": _relationship_points(c.planet, _hadda_lord(p.sign_index, p.degree_in_sign), 15),
            "drekkana": _relationship_points(c.planet, _drekkana_lord(p.sign_index, p.degree_in_sign), 10),
            "navamsa": _relationship_points(c.planet, RASHI_LORD[RASHI[d9_navamsha_sign_index(p.longitude)]], 5)}
    return {"role": c.role, "planet": c.planet, "strengthScore": c.strength_score,
            "aspectsAscendant": c.aspects_varsha_lagna, "bala": bala}


def annual(birth, local_birth, natal, lat, lon, year):
    ps = get_planet_positions(natal["julianDay"])
    result = compute_varshaphala(ps["Sunce"].longitude, natal["ascendant"], local_birth.year, local_birth.month,
                                 local_birth.day, year, lat, lon, ps["Mjesec"].longitude, birth)
    at_jd = find_solar_return_jd(ps["Sunce"].longitude, year, local_birth.month, local_birth.day)
    next_jd = find_solar_return_jd(ps["Sunce"].longitude, year + 1, local_birth.month, local_birth.day)
    winner = result.varsheshwara["winner"]
    out = {"year": year, "chart": chart(at_jd, lat, lon, result.planet_positions, result.ascendant_longitude),
           "returnTime": result.return_datetime_utc.timestamp(), "nextJulianDay": next_jd,
           "completedYears": year - local_birth.year, "munthaSignIndex": RASHI.index(result.muntha_sign),
           "isDay": result.is_day_birth, "sahams": compute_sahams(result.ascendant_longitude, result.planet_positions, result.is_day_birth),
           "arudhaSign": RASHI.index(result.arudha_lagna_sign), "bhriguBinduLongitude": result.bhrigu_bindu_longitude,
           "gulika": gulika(at_jd, result.return_datetime_utc.strftime("%Y-%m-%d"), lat, lon),
           "mudda": [period(p) for p in result.mudda_dasha],
           "candidates": [candidate(c, result.planet_positions) for c in result.varsheshwara["candidates"]],
           "winnerRole": winner.role if winner else None,
           "ithasala": [relation(r) for r in result.ithasala_pairs], "isarapha": [relation(r) for r in result.isarapha_pairs]}
    monthly = compute_masa_pravesha_sequence(ps["Sunce"].longitude, at_jd, lat, lon)
    out["masa"] = []
    for i, m in enumerate(monthly):
        target = (ps["Sunce"].longitude + i * 30) % 360
        mjd = at_jd if i == 0 else _find_sun_longitude_jd(target, at_jd + i * (365.2425 / 12))
        out["masa"].append({"monthNumber": m.month_number, "chart": chart(mjd, lat, lon, m.planet_positions, m.ascendant_longitude),
                            "returnTimeMinute": m.datetime_utc.timestamp(), "arudhaSign": m.arudha_lagna_sign_index,
                            "bhriguBinduLongitude": m.bhrigu_bindu_longitude,
                            "gulika": gulika(mjd, m.datetime_utc.strftime("%Y-%m-%d"), lat, lon)})
    return out


def main():
    swe.set_ephe_path(str(DATA))
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    cases = []
    max_arcseconds = {name: 0.0 for name in SWE_PLANET_CODES}
    max_speed = {name: 0.0 for name in SWE_PLANET_CODES}
    for identifier, iso, lat, lon, zone, years in INPUTS:
        birth = datetime.fromisoformat(iso)
        local_birth = birth.astimezone(ZoneInfo(zone))
        person = SimpleNamespace(birth_date=local_birth.strftime("%Y-%m-%d"), latitude=lat, longitude=lon)
        natal = chart(jd(birth), lat, lon)
        ps = get_planet_positions(natal["julianDay"])
        sp = compute_special_points(person, natal["julianDay"], natal["ascendant"], int(natal["ascendant"] // 30), ps)
        natal["special"] = {"arudhaSign": sp["AL_sign_index"], "upapadaSign": sp["UL_sign_index"], "darapadaSign": sp["A7_sign_index"],
                             "bhriguBinduLongitude": sp["BP_longitude"], "gulika": gulika(natal["julianDay"], person.birth_date, lat, lon)}
        at = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
        cases.append({"id": identifier, "utc": birth.timestamp(), "latitude": lat, "longitude": lon, "timeZone": zone,
                      "localDate": person.birth_date, "natal": natal, "dashaAt": at.timestamp(),
                      "mahadashas": [period(p) for p in get_mahadasha_sequence(ps["Mjesec"].longitude, birth)],
                      "currentDasha": [period(p) for p in get_current_dasha_5_levels(ps["Mjesec"].longitude, birth, at)],
                      "annual": [annual(birth, local_birth, natal, lat, lon, y) for y in years]})
        # Quantify the original no-data backend separately; do not confuse this
        # expected ephemeris difference with Swift/Python formula disagreement.
        for c in [natal] + [a["chart"] for a in cases[-1]["annual"]]:
            for name, code in SWE_PLANET_CODES.items():
                no_data = swe.calc_ut(c["julianDay"], code, swe.FLG_SIDEREAL | swe.FLG_MOSEPH | swe.FLG_SPEED)[0]
                bundled = swe.calc_ut(c["julianDay"], code, SIDEREAL_FLAG)[0]
                delta = abs((no_data[0] - bundled[0] + 180) % 360 - 180) * 3600
                max_arcseconds[name] = max(max_arcseconds[name], delta)
                max_speed[name] = max(max_speed[name], abs(no_data[3] - bundled[3]))
    metadata = {"generator": "scripts/generate_parity_fixtures.py", "swissephVersion": swe.version,
                "reference": "Unmodified OriginalPython modules with bundled Swiss files and Lahiri; synthetic inputs only",
                "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DATA.glob("*.se1"))},
                "originalMoshierDifferenceMaxArcseconds": max_arcseconds,
                "originalMoshierDifferenceMaxSpeedDegreesPerDay": max_speed,
                "counts": {"birthCases": len(cases), "annualCases": sum(len(c["annual"]) for c in cases),
                           "monthlyCases": sum(len(a["masa"]) for c in cases for a in c["annual"])}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"metadata": metadata, "cases": cases}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
