#!/usr/bin/env python3
"""Regenerate native Ashtakavarga expectations from unmodified Python formulas.

Only synthetic positions/birth inputs are used, never the uploaded persons DB.
Run with the project's Python environment and PYTHONDONTWRITEBYTECODE=1.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "OriginalPython"))

import swisseph as swe
from core.ashtakavarga import (
    ASHTAKAVARGA_PLANETS, KAKSHYA_ORDER, TOTAL_BINDUS,
    compute_bhinnashtakavarga, compute_sarvashtakavarga,
    get_kakshya_lord, is_kakshya_activated,
)
from core.ephemeris import get_ascendant, get_planet_positions


def expected_case(label: str, sources: dict[str, int]) -> dict:
    return {
        "label": label,
        "sourceSigns": sources,
        "bhinna": {planet: compute_bhinnashtakavarga(planet, sources)
                   for planet in ASHTAKAVARGA_PLANETS},
        "sarva": compute_sarvashtakavarga(sources),
        "activated": {
            planet: [[is_kakshya_activated(planet, sign, lord, sources)
                      for lord in KAKSHYA_ORDER] for sign in range(12)]
            for planet in ASHTAKAVARGA_PLANETS
        },
    }


def main() -> None:
    rng = random.Random(20261102)
    source_names = ASHTAKAVARGA_PLANETS + ["Lagna"]
    cases = [expected_case(f"aligned-{sign}", {source: sign for source in source_names})
             for sign in range(12)]
    cases.extend(expected_case(f"seeded-{i}", {source: rng.randrange(12) for source in source_names})
                 for i in range(48))

    swe.set_ephe_path(str(ROOT / "Packages/JyotishCore/Sources/JyotishCore/Resources/Ephemeris"))
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    for label, utc, latitude, longitude in [
        ("europe", "1985-11-04T00:15:00+00:00", 45.45, 16.3667),
        ("southern", "2000-01-01T12:00:00+00:00", -33.8688, 151.2093),
        ("south-asia", "1992-06-15T05:30:00+00:00", 28.6139, 77.2090),
        ("western", "1977-03-20T20:00:00+00:00", 40.7128, -74.0060),
    ]:
        date = datetime.fromisoformat(utc)
        jd = swe.julday(date.year, date.month, date.day,
                        date.hour + date.minute / 60 + date.second / 3600)
        positions = get_planet_positions(jd)
        ascendant = get_ascendant(jd, latitude, longitude)
        sources = {planet: positions[planet].sign_index for planet in ASHTAKAVARGA_PLANETS}
        sources["Lagna"] = int(ascendant // 30)
        case = expected_case(label, sources)
        case["chartInput"] = {"unix": date.timestamp(), "latitude": latitude, "longitude": longitude}
        cases.append(case)

    degrees = sorted(set([0.0, 30.0] + [
        value for boundary in [3.75 * i for i in range(9)]
        for value in [boundary - 1e-10, boundary, boundary + 1e-10] if 0 <= value <= 30
    ] + [rng.random() * 30 for _ in range(100)]))
    source = ROOT / "OriginalPython/core/ashtakavarga.py"
    payload = {
        "metadata": {
            "oracle": "OriginalPython/core/ashtakavarga.py",
            "oracleSHA256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "seed": 20261102,
            "planetOrder": ASHTAKAVARGA_PLANETS,
            "kakshyaOrder": KAKSHYA_ORDER,
            "totalBindus": TOTAL_BINDUS,
            "reductions": False,
        },
        "cases": cases,
        "kakshya": [{"degree": degree, "lord": get_kakshya_lord(degree)} for degree in degrees],
    }
    output = ROOT / "Packages/JyotishCore/Tests/JyotishCoreTests/Fixtures/AshtakavargaReference.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"Wrote {len(cases)} complete BAV/SAV references, "
          f"{len(cases) * 7 * 12 * 8} Kakshya activations and {len(degrees)} degree references.")


if __name__ == "__main__":
    main()
