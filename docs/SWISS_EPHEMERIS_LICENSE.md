# Swiss Ephemeris: distribution decision

Reviewed 2026-11-01 against the upstream license notice preserved in
[Swiss-Ephemeris-NOTICE.txt](../LICENSES/Swiss-Ephemeris-NOTICE.txt), including the
notice inside every vendored C source file. This is a record of the dependency's
terms, not a license grant for this application's original code.

Swiss Ephemeris is **dual licensed**. Its notice requires the developer to choose
before distributing software containing it or activating a public service:

1. **GNU AGPL**: satisfy the AGPL's requirements for the combined application,
   including the corresponding source and license/copyright notices. The upstream
   notice expressly describes licensing the whole project under AGPL or a
   compatible license. The full AGPL v3 text is included in
   [LICENSES/AGPL-3.0.txt](../LICENSES/AGPL-3.0.txt).
2. **Swiss Ephemeris Professional License**: obtain the license and sign the
   applicable contract with Astrodienst. A private repository, an App Store
   developer account or the availability of the source does not supply that
   commercial license.

**No distribution choice or professional license has been supplied in this
project.** Development and numerical testing have continued; nothing was submitted
to the App Store or distributed as a release. Before a closed-source/App Store
release, resolve the professional license with Astrodienst, or independently
confirm that the chosen distribution terms satisfy the AGPL, including any
additional platform restrictions. This project does not claim that choosing AGPL
alone establishes App Store compatibility.

Upstream notice: <https://github.com/aloistr/swisseph/blob/master/LICENSE>.
Vendor's licensing information and contact:
<https://www.astro.com/swisseph/swephinfo_e.htm>.
The legal notice was verified from upstream source; a professional contract and
its current commercial terms have not been obtained or reviewed.

## What is included

- Native **Swiss Ephemeris 2.10.03 C source**, taken from the SHA-256 verified
  `pyswisseph 2.10.3.2` source archive. The Python extension/wrapper is not embedded
  in the iPhone app. The C code retains its original notices without modification;
  `SwissBridge.c` is the application's adapter.
- Planetary `sepl_18.se1` and lunar `semo_18.se1` data, pinned to upstream commit
  `94621aba9f3ff9c32cb721eac0380c30dbb153fe`. Both are bundled inside the Swift
  package, covering the selected 1800–2399 calendar range. Annual selections end
  at 2398 because the next solar return must also be available.
- Source, origin and per-file SHA-256 checksums:
  [SwissEphemeris-SOURCE.json](../LICENSES/SwissEphemeris-SOURCE.json).

Retain the upstream notices and include them with any permitted redistribution of
the library/data. The license model and its treatment of the bundled data must be
settled with the same release decision; do not infer a separate unrestricted data
license from the files being downloadable.
