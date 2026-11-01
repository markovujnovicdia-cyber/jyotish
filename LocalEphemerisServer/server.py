"""Local-only Swiss Ephemeris JSON bridge for the SwiftUI client.
Run on your own trusted network; no authentication or TLS is provided.
"""
import json
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1] / 'OriginalPython'
sys.path.insert(0, str(ROOT))
from core.ephemeris import get_ascendant, get_planet_positions
from core.houses import whole_sign_house
from core.constants import RASHI
import swisseph as swe

NAKSHATRAS = ('Ashwini Bharani Krittika Rohini Mrigashira Ardra Punarvasu Pushya Ashlesha Magha '
              'Purva_Phalguni Uttara_Phalguni Hasta Chitra Swati Vishakha Anuradha Jyeshtha Mula '
              'Purva_Ashadha Uttara_Ashadha Shravana Dhanishtha Shatabhisha Purva_Bhadrapada '
              'Uttara_Bhadrapada Revati').split()

def chart(payload):
    dt = datetime.fromisoformat(payload['utc'].replace('Z', '+00:00')).astimezone(timezone.utc)
    lat, lon = float(payload['latitude']), float(payload['longitude'])
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError('Koordinate izvan dopuštenog raspona')
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60 + (dt.second + dt.microsecond/1e6)/3600)
    asc = get_ascendant(jd, lat, lon)
    asc_sign = int(asc // 30)
    def info(name, longitude, retro=False):
        sign_idx = int(longitude // 30)
        nak_idx = min(26, int(longitude / (360/27)))
        pada = min(4, int((longitude - nak_idx*(360/27)) / (360/108)) + 1)
        return dict(name=name, longitude=longitude, sign=RASHI[sign_idx], degree=longitude%30,
                    house=whole_sign_house(sign_idx, asc_sign), nakshatra=NAKSHATRAS[nak_idx].replace('_',' '),
                    pada=pada, retrograde=retro)
    planets = [info(name, p.longitude, p.is_retrograde) for name,p in get_planet_positions(jd).items()]
    return dict(julianDay=jd, ayanamsha='Lahiri', nodeType='Mean Rahu', ascendant=info('Lagna',asc), planets=planets)

def varshaphala(payload):
    """Annual solar-return calculation with all values from the shared Python core.

    The request's ``utc`` represents the *birth instant in UTC*; year is the
    calendar year in which the requested return begins. No interpretations.
    """
    from core.varshaphala import compute_varshaphala, get_varshaphala_period_info
    from core.sahams import compute_sahams
    dt = datetime.fromisoformat(payload['utc'].replace('Z', '+00:00')).astimezone(timezone.utc)
    lat, lon = float(payload['latitude']), float(payload['longitude'])
    year = int(payload['year'])
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError('Koordinate izvan dopuštenog raspona')
    if not 1800 <= year <= 2200 or year < dt.year:
        raise ValueError('Godina Varshaphale mora biti između godine rođenja i 2200.')
    natal_jd = swe.julday(dt.year, dt.month, dt.day,
                          dt.hour + dt.minute/60 + (dt.second + dt.microsecond/1e6)/3600)
    natal_asc = get_ascendant(natal_jd, lat, lon)
    natal_positions = get_planet_positions(natal_jd)
    result = compute_varshaphala(
        natal_positions['Sunce'].longitude, natal_asc,
        dt.year, dt.month, dt.day, year, lat, lon,
        natal_positions['Mjesec'].longitude, dt)
    period_info = get_varshaphala_period_info(
        natal_positions['Sunce'].longitude, dt.year, dt.month, dt.day, year)
    full_sahams = compute_sahams(result.ascendant_longitude,
                                  result.planet_positions, result.is_day_birth)

    def planet(name, pos):
        return dict(name=name, longitude=pos.longitude, sign=pos.sign,
                    degree=pos.degree_in_sign, retrograde=pos.is_retrograde)

    def relation(r):
        return dict(planetA=r.planet_a, planetB=r.planet_b,
                    aspect=r.aspect, orbDifference=r.orb_diff,
                    combinedOrb=r.combined_orb, applying=r.is_applying)

    def candidate(c):
        return dict(role=c.role, planet=c.planet, strength=c.strength_score,
                    aspectsAscendant=c.aspects_varsha_lagna, components=c.bala_detail)

    return dict(
        year=year,
        solarReturnUTC=result.return_datetime_utc.isoformat(),
        nextSolarReturnUTC=period_info.end_datetime_utc.isoformat(),
        completedYears=period_info.completed_years_at_start,
        lifeYear=period_info.life_year_number,
        ayanamsha='Lahiri',
        annualAscendantLongitude=result.ascendant_longitude,
        annualAscendantSign=result.ascendant_sign,
        natalAscendantLongitude=natal_asc,
        munthaSign=result.muntha_sign,
        isDayReturn=result.is_day_birth,
        planets=[planet(name, pos) for name, pos in result.planet_positions.items()],
        sahams=[dict(name=name, longitude=longitude) for name, longitude in full_sahams.items()],
        ithasala=[relation(r) for r in result.ithasala_pairs],
        isarapha=[relation(r) for r in result.isarapha_pairs],
        # Kamboola requires a selected Lagnesha/Karyesha pair; global
        # moon Ithasala alone is not sufficient, so no false positives.
        varsheshwara=dict(winner=(candidate(result.varsheshwara['winner'])
                                 if result.varsheshwara['winner'] else None),
                            candidates=[candidate(c) for c in result.varsheshwara['candidates']]),
        muddaDasha=[dict(lord=d.lord, startUTC=d.start.isoformat(), endUTC=d.end.isoformat())
                    for d in result.mudda_dasha],
        calculationConvention='Sahams: fixed Vivaha/Putra, +30° arc; '
                              'Mudda: 360 parts scaled to next solar return',
    )


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        endpoint = urlparse(self.path).path
        if endpoint not in ('/chart', '/varshaphala'):
            self.send_error(404); return
        try:
            length = int(self.headers.get('Content-Length','0'))
            if length > 4096: raise ValueError('Prevelik zahtjev')
            payload = json.loads(self.rfile.read(length))
            result = chart(payload) if endpoint == '/chart' else varshaphala(payload)
            status = 200
        except (ValueError, KeyError, TypeError, json.JSONDecodeError, swe.Error) as exc:
            result = {'error':str(exc)}; status = 400
        body = json.dumps(result, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers(); self.wfile.write(body)

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    print(f'Jyotish local service: http://{args.host}:{args.port}')
    ThreadingHTTPServer((args.host,args.port),Handler).serve_forever()
