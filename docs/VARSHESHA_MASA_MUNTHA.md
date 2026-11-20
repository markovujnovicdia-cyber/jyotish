# Annual lord, monthly lord and Muntha reference checks

This revision addresses three separate outputs for the supplied 2026–2027 PL9
case: Varshesha, Masa Pravesha lord and the annual/monthly Muntha longitude.
Inputs and calculation preferences are in [PARASHARA_REFERENCE.md](PARASHARA_REFERENCE.md).

## Annual lord eligibility

The previous implementation required a candidate to aspect the exact degree
of the annual lagna within the planet's deeptamsha. For this example that
excluded Jupiter in Leo from the trine to Sagittarius: its degree residual is
about 9.80°, just beyond Jupiter's 9° orb. Venus was excluded too, leaving
Saturn as the winner even though Jupiter has the largest candidate Bala.

The app now explicitly selects `VarsheshwaraConvention.signAspect`. A candidate
qualifies through a Tajika sign aspect to the annual lagna; degree orb is not
an additional gate. The strongest qualified candidate is selected using the
full numerical Bala rather than a rounded display tie. The five candidate
roles and existing Bala component tables are retained.

For the supplied input the derived candidate scores are Jupiter 16.42,
Venus 15.14 and Saturn 7.56; the new selection is **Jupiter**. This is an
algorithm regression check, not a claim that the supplied annual PDF explicitly
names PL9's Varshesha. That final label has been requested separately.
`legacyOrb` remains the library default for the original Python fixtures.

Public implementation corroboration for sign-based lord qualification is
available in [PyJHora's Tajika module](https://github.com/naturalstupid/PyJHora/blob/f8c6de2f54338752bdb667384a8b0ca5791c5bdf/src/jhora/horoscope/transit/tajaka.py).
That code has unrelated date/candidate-index inconsistencies and is not used
as a numerical oracle or as proof of every PL9 rule. The inherited Bala tables
have not been altered without a component-level PL9 reference.

## Monthly lord

`MasaLord.calculate` defines six monthly candidate roles: natal lagna lord,
Muntha lord, monthly lagna lord, day/night luminary sign lord, triplicity lord
and the separately calculated annual lord. It reuses sign-based eligibility
and numerical election, without a lookup of expected planets by month.

All six visible ML labels from the user's monthly screenshot are tested:

| Monthly entry, fixed CET | PL9 ML | Calculated ML |
| --- | --- | --- |
| 27 December 2026 | Jupiter | Jupiter |
| 25 January 2027 | Venus | Venus |
| 24 February 2027 | Jupiter | Jupiter |
| 26 March 2027 | Venus | Venus |
| 26 April 2027 | Venus | Venus |
| 27 May 2027 | Venus | Venus |

The annual context must match the monthly series' starting Julian day, solar
longitude, ephemeris time convention and node convention. Legacy calls without
annual context get no invented monthly lord or Muntha. Both app targets pass
the complete context and show the selected planet and candidate details.

The caller supplies the Muntha sign explicitly. The app currently uses the
progressed monthly Muntha. All first six references remain in Taurus, so they
cannot distinguish that choice from a fixed annual Muntha in lord selection.
The eighth entry, **28 July 2027**, distinguishes them: progressed Gemini
Muntha gives Mercury, fixed annual Taurus gives Jupiter. That PL9 label is
still required to validate the scope beyond the six supplied examples. Other
later-month outputs are calculations, not externally verified PL9 matches.

## Full Muntha position

The annual position is `normalize(natal ascendant + 30° × completed years)`.
The natal degree is retained, and integer years are reduced before conversion
to avoid overflow. For 2026 the supplied birth has 50 completed years, placing
Muntha in **Taurus**, with **Venus** as its lord.

Monthly Muntha advances continuously from the annual return by 30° per
365.25 days. It is not advanced by an arbitrary fixed 2.5° for every solar
month: actual monthly intervals have different lengths. The supplied six
increments match this Julian-year convention within 1″; a single example does
not prove a universal PL9 year convention.

The exact external monthly positions are Taurus 16:30:57, 18:56:06, 21:22:10,
23:50:12, 26:20:45 and 28:53:44. Absolute end-to-end values pass a separate 10″
budget. The native baseline is Taurus **16:30:51** when rounded to seconds;
the approximately 5.7″ difference includes the existing 3.69″ natal ascendant
residual and the report's own 2″ difference between printed natal and annual
starting degrees. No constant angle is added to conceal that discrepancy.

Annual and monthly views now show sign, degrees, minutes, seconds and Muntha
lord. Rounding across 30°/360° is handled before formatting.

## Keeping the comparison year

The header explicitly shows the selected annual cycle. Editing the same
person's coordinates no longer discards a manually selected year. Switching
people initially selects the active year; the user can choose a different
year or explicitly select “Trenutačna Varshaphala”. Comparing the supplied
reference requires **2026–2027**, whereas the active cycle before the December
2026 solar return is 2025–2026.

## Validation

Core tests cover sign qualification, full-precision ranking, six external ML
labels, optional sixth candidate participation, Muntha progression/wrap/input
validation and the annual-to-monthly context. Original Python reference tests
continue to use the explicit legacy policy. The real native calculation bridge
has also been compiled and executed with a temporary Combine shim and verifies
Jupiter, the six ML labels and nonempty monthly Muntha values.

SwiftUI syntax/project checks and hosted-test source type checking are separate
from a real Apple build. iOS/Catalyst UI execution requires Xcode and has not
run in this Linux session.
