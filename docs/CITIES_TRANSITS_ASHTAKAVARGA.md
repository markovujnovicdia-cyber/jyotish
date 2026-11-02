# Offline cities, transit comparison and Ashtakavarga

## Birthplace selection

The person editor offers **Pronađi grad**. Selecting a city fills latitude,
longitude and its IANA timezone while preserving the entered **local** birth
clock. The existing DST-gap/fold checks then resolve that clock in the selected
zone. Birthplace labels are saved with the person. Existing people without the
new optional `birthPlace` JSON key still load, and their coordinates/timezone
are not changed by catalog updates.

The bundled GeoNames catalog contains **36,895 places**: all 34,006 records in
`cities15000`, plus 2,889 smaller places from `cities500` in HR/BA/RS/SI/ME/MK/XK.
It includes Petrinja, Dugo Selo and Đakovo. Other villages and small towns may be
absent; manual name/coordinate/timezone entry remains available. Search matches
names/aliases without accents, Croatian Đ/D/DJ forms, and country/subdivision
context. Country and administrative codes distinguish namesakes. Search and its
initial decode/index run in a background task; no network service is called.

GeoNames dataset coordinates/timezones are retained. A timezone newer than the
OS's IANA database is not silently replaced: the picker reports that selection
as unsupported and retains the rest of the catalog. Place coordinates describe
the city, so the existing manual fields can refine a hospital/address position.

Provenance, checksums and attribution are bundled in
`Packages/JyotishCore/Sources/JyotishCore/Resources/Cities/SOURCE.json` and
`NOTICE.txt`. Data is GeoNames **CC BY 4.0**, acquired through a SHA-256 verified
`geonamescache 3.0.2` package. Its package MIT notice is preserved as well. App
About/Licenses shows this attribution. Build the data reproducibly with
`scripts/build_city_catalog.py`; see that script's arguments for the verified
source wheel.

## Transit comparison

**Tranziti** draws natal and transit positions in the same North Indian chart:
**N** labels are natal; **T** labels are transit. The frame can be changed from
natal lagna to natal Moon. This changes house numbering, not zodiac longitudes.
The table includes all nine planets, both positions, retrograde status and
houses from both natal references. The existing Python highlight list is an
optional table filter. No predicted events or interpretive text is generated.

`Transits.swift` ports `OriginalPython/core/transits.py`. The transit ascendant
is not substituted for the natal reference. The selected instant continues to
be a UTC `Date` displayed in the person's chosen IANA timezone.

## Ashtakavarga

The **Ashtakavarga** screen computes the unreduced natal D1 tables:

- Seven Bhinna (BAV) rows, each with twelve zodiac-sign values.
- Sarva (SAV), the seven-row sum, with total **337**.
- Eight contributors per BAV: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn
  and Lagna. Rahu/Ketu are excluded.
- The existing Kakshya order and activation predicates are ported in the core.
  They are tested but not shown as an interpretation or a new prediction view.

The bar view can select SAV or any BAV row. Each sign also identifies its natal
house. A horizontally scrollable full table preserves all 84 BAV values, SAV
values and row sums. BAV has a maximum of eight per sign; SAV's theoretical
maximum is 56. No Trikona/Ekadhipatya reductions or changed source tables are
introduced.

## Validation

The unchanged Python modules generated independent fixtures:

- Ashtakavarga: 64 full BAV/SAV cases, 43,008 contributor/activation checks and
  125 Kakshya degree references. Integer values must match exactly.
- Transits: 65 cases covering real Swiss positions, signed references and exact
  sign boundaries; all nine rows/house references/flags are compared.
- City tests: real regional and world records, aliases/diacritics/prefixes,
  duplicate-name context, historical UTC conversion and bad-resource handling.
- App model checks cover city persistence and old JSON without birthplace,
  plus all six calculation modes through the real app's Foundation source.

Regenerate/check the new numerical fixtures from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 /workspace/.venvs/jyotish/bin/python scripts/generate_ashtakavarga_fixtures.py
PYTHONDONTWRITEBYTECODE=1 /workspace/.venvs/jyotish/bin/python scripts/generate_transit_fixtures.py --check
bash scripts/test-core.sh
bash scripts/test-core.sh -c release
```

New hosted XCTest and XCUITest cases cover the complete city-selection → person
save → transit comparison → Ashtakavarga flow. They are prepared for Xcode; they
have **not** executed in this Linux workspace. Swift frontend syntax checks and
static project validation do not substitute for Apple SDK typechecking or a
simulator test. Previous app versions were confirmed working by the user; that
confirmation does not establish validation of these new UI changes.

Executed on 2026-11-02: all **51 XCTest tests passed in Debug and Release** on
Linux Swift 6.0.3. Both new numerical parity suites and six city tests executed;
there were no failures. The actual app Foundation calculation/persistence bridge
was rebuilt and exercised for all six modes using the temporary Combine shim.
Old-record migration and city-profile reload passed. All eight SwiftUI source
files and both iOS test files passed frontend syntax parsing; the 62-object
Xcode project passed static validation. Hosted iOS tests and UI tests remain
unexecuted here.

Initial catalog loading/indexing is performed once per app process, off the UI
thread, with a progress indicator. The full aliases are retained; first opening
can take several seconds. Subsequent searches reuse the in-memory index.
