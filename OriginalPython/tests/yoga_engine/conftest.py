"""
Helper za brzu izgradnju core.yoga_engine.context.ChartContext u testovima,
bez swisseph poziva - isti obrazac kao tests/conftest.py::make_natal_context
(koji ovo dosad nije trebao jer je pisan prije Yoga Engine-a).
"""

from typing import Dict, Optional

from core.constants import PLANET_ORDER
from core.natal import compute_special_points
from core.yoga_engine.context import ChartContext
from tests.conftest import make_planet_position


class _FakePerson:
    birth_date = "2000-01-01"
    latitude = 0.0
    longitude = 0.0


def make_chart(
    ascendant_longitude: float,
    planet_longitudes: Dict[str, float],
    retrograde: Optional[Dict[str, bool]] = None,
    default_longitude: float = 65.0,
    **kwargs,
) -> ChartContext:
    """
    default_longitude=65.0 (Blizanci) je namjerno "neutralna" pozicija za
    planete koje test ne navede eksplicitno - izvan tipičnih posebnih kuća
    kad je ascendent blizu 0°, isto načelo kao u tests/conftest.py.
    """
    retro = retrograde or {}
    positions = {
        p: make_planet_position(planet_longitudes.get(p, default_longitude), retro.get(p, False))
        for p in PLANET_ORDER
    }
    asc_sign_idx = int(ascendant_longitude % 360.0 // 30)
    special_points = compute_special_points(
        _FakePerson(), jd_ut=2451544.5, asc_lon=ascendant_longitude,
        asc_sign_idx=asc_sign_idx, positions=positions,
    )
    return ChartContext(
        ascendant_longitude=ascendant_longitude,
        ascendant_sign_index=asc_sign_idx,
        positions=positions,
        special_points=special_points,
        **kwargs,
    )
