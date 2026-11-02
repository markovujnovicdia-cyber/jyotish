#!/usr/bin/env python3
"""Build the offline GeoNames catalog from a checksum-verified source wheel.

Usage: python3 scripts/build_city_catalog.py /path/to/geonamescache-3.0.2.whl
No package installation, application database or network request is involved.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import zipfile

VERSION = "3.0.2"
WHEEL_URL = "https://files.pythonhosted.org/packages/48/c2/52f1b29de8839b4b55cd2641dfd722a6a94953d74fa82514e26084a92318/geonamescache-3.0.2-py3-none-any.whl"
WHEEL_SHA256 = "b830e8942f2d58c7e68782dcf4dff2ffe8c4104a35ee881ed1ad4023cefcdba4"
REGIONAL_COUNTRIES = {"HR", "BA", "RS", "SI", "ME", "MK", "XK"}
DESTINATION = Path(__file__).resolve().parents[1] / "Packages/JyotishCore/Sources/JyotishCore/Resources/Cities"


def build(wheel: Path) -> None:
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    if digest != WHEEL_SHA256:
        raise ValueError("Source wheel SHA-256 does not match the pinned PyPI artifact")
    with zipfile.ZipFile(wheel) as archive:
        world_bytes = archive.read("geonamescache/data/cities15000.json")
        regional_bytes = archive.read("geonamescache/data/cities500.json")
        world = json.loads(world_bytes)
        selected = dict(world)
        selected.update({key: city for key, city in json.loads(regional_bytes).items()
                         if city["countrycode"] in REGIONAL_COUNTRIES})
        package_license = archive.read(f"geonamescache-{VERSION}.dist-info/licenses/LICENSE").decode()

    cities = []
    for raw in sorted(selected.values(), key=lambda city: city["geonameid"]):
        latitude, longitude = float(raw["latitude"]), float(raw["longitude"])
        if not math.isfinite(latitude) or not -90 < latitude < 90:
            raise ValueError(f"Invalid latitude for {raw['geonameid']}")
        if not math.isfinite(longitude) or not -180 <= longitude <= 180 or not raw["timezone"]:
            raise ValueError(f"Invalid longitude/timezone for {raw['geonameid']}")
        cities.append({"id": raw["geonameid"], "name": raw["name"],
                       "countryCode": raw["countrycode"], "admin1": raw["admin1code"],
                       "latitude": latitude, "longitude": longitude,
                       "timeZone": raw["timezone"], "population": raw["population"],
                       "aliases": sorted(set(raw["alternatenames"]) - {raw["name"]})})

    DESTINATION.mkdir(parents=True, exist_ok=True)
    output = json.dumps(cities, ensure_ascii=False, separators=(",", ":")) + "\n"
    (DESTINATION / "cities.json").write_text(output, encoding="utf-8")
    metadata = {"source": "GeoNames via geonamescache", "package_version": VERSION,
                "source_wheel_url": WHEEL_URL, "source_wheel_sha256": WHEEL_SHA256,
                "upstream_data_sha256": {"cities15000.json": hashlib.sha256(world_bytes).hexdigest(),
                                         "cities500.json": hashlib.sha256(regional_bytes).hexdigest()},
                "catalog_sha256": hashlib.sha256(output.encode()).hexdigest(),
                "world_cities": len(world), "regional_additions": len(cities) - len(world),
                "total_cities": len(cities), "country_codes": len({c["countryCode"] for c in cities}),
                "regional_country_codes": sorted(REGIONAL_COUNTRIES),
                "selection": "All world cities15000 plus cities500 for the listed regional countries; aliases retained and sorted.",
                "modifications": "Filtered, deduplicated by GeoNames ID, renamed JSON fields and compacted; coordinates/timezones unmodified.",
                "data_license": "Creative Commons Attribution 4.0 (GeoNames)",
                "attribution_url": "https://www.geonames.org/", "license_url": "https://creativecommons.org/licenses/by/4.0/"}
    (DESTINATION / "SOURCE.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    notice = """GeoNames offline city data

Contains geographical information from GeoNames (https://www.geonames.org/).
GeoNames data is available under Creative Commons Attribution 4.0:
https://creativecommons.org/licenses/by/4.0/

The data was obtained through geonamescache 3.0.2, pinned by the source wheel
SHA-256 in SOURCE.json. The catalog includes all cities15000 records and smaller
cities500 records from HR, BA, RS, SI, ME, MK and XK. Filtering, field renaming,
deduplication and JSON compaction were performed for this application; original
coordinates, time-zone identifiers and place names were retained.

This is an offline gazetteer, not an exhaustive address or village database.
Coordinates identify the locality, not a particular hospital or street. Its IANA
time-zone identifier is applied to the historical birth date using the device's
time-zone database. Manual coordinates and time-zone entry remain available.

Source package license (no package runtime is embedded):

""" + package_license
    (DESTINATION / "NOTICE.txt").write_text(notice, encoding="utf-8")
    print(f"Built {len(cities)} cities ({len(world)} world + {len(cities)-len(world)} regional), {len(output.encode())} bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    build(parser.parse_args().wheel)
