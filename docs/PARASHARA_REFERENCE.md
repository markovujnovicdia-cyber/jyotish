# Parashara’s Light 9 reference comparison

The November 20, 2026 comparison uses the user-supplied `tajika.pdf` and
screenshots of natal positions, the 2026–2027 Sahams, Mudda Dasha and monthly
charts. The user identified the annual chart as December 27, 2026.
The PDF SHA-256 is
`899c0cd47257fd6335856f1f2a4d0cf871616fc28c0fd1420787430856e468c9`.
The original documents are not redistributed in the repository.

This is a partial reference comparison, not certification that all PL9
calculation options or all sixteen yogas are reproduced.

## Input and precision

The screenshot confirms December 26, 1976, 11:55:00, Sisak. The tests convert
this to 10:55 UTC using Europe/Zagreb. Latitude 45.4881 and longitude 16.3745
are provisional: the exact coordinates selected in PL9 have been requested.
No coordinate, ayanamsha, ascendant or time offset is fitted to make a test pass.

The screenshot prints natal planetary positions to seconds of arc. Those nine
longitudes are independently transcribed. Seven classical planets pass a
1 arcsecond comparison. The two node comparisons failed that precision:
PL9 prints Rahu at Libra 06:38:18 and Ketu at Aries 06:38:18; our mean-node
calculation gives 06:38:26.75, a difference of about 8.75 arcseconds for each.
The passing regression covers the seven planets; the failed node comparison
is retained here as an unresolved reference difference, with no widened
precision budget and no fitted constant offset. The ascendant is not asserted to that precision until its exact
location and house settings are available. PL9's annual start is printed as
07:43 CET; the current solar return is approximately 07:43:36 CET.

## Changes selected by both application targets

`NativeCalculations` explicitly selects these conventions for annual calculations:

| Component | Application convention | Reference evidence |
| --- | --- | --- |
| Tajika aspects | `longitudeBothOrbs`: angular geometry, including sign-boundary aspects; residual inside both individual deeptamshas | Exact sets of six Ithasala and three Esharpha pairs in the PDF |
| Manau | In-orb conjunction, square or opposition from Mars/Saturn to the faster member, including a slower malefic member | Exact five qualifying pairs in the PDF |
| Mudda year | `fixedGregorianYear`: 365.2425 civil days | Eight major starts substantially closer than scaling to the next astronomical return |
| Mudda subperiods | Preserve the already-elapsed phase, then clip to the visible major period | Initial Sun subperiod starts in the screenshot |
| Roga Saham | `tajikaRoga`: Saturn − Moon + Asc in daytime, retaining arc correction | Reference operand matches; exact value still depends on the unconfirmed ascendant |

The aspect/orb convention is an explicit model consistent with this example;
one chart does not establish every internal PL9 rule. Actual signed ephemeris
speeds are used consistently in application pair and chart-wide aspect checks.
The unchanged Python comparison remains available through the explicit library
defaults `legacySignBased`, `solarReturnInterval` and `legacyPython`.

## Verified reference sets

- Ithasala: Mercury–Sun, Mercury–Mars, Mercury–Saturn, Sun–Mars, Sun–Saturn,
  Moon–Jupiter.
- Esharpha: Moon–Venus, Mercury–Jupiter, Sun–Jupiter.
- Manau: Mercury–Sun, Mercury–Mars, Mercury–Saturn, Sun–Mars, Sun–Saturn.

The Moon–Jupiter conjunction crosses a sign boundary and was previously
discarded. Using an averaged orb with angular geometry also admits an extra
Venus–Jupiter pair; requiring both individual orbs matches the supplied list.
Synthetic tests cover orbital thresholds, circular wrap, signed and stationary
speeds, exact aspects, reversed pair order and malefic self-aspect exclusion.

## Dates and display zones

The supplied summer timestamps agree with fixed CET (+01:00), not summer
Europe/Zagreb (+02:00). Annual Mudda and monthly views now offer a fixed-offset
display option alongside the historical IANA zone. This changes the displayed
clock, never the computed instant or the person's birth zone.

The eight supplied Mudda major boundaries agree within about 82 seconds under
the candidate fixed-year convention; the five visible initial subperiod starts
agree within about 66 seconds. The reference tests use a documented 90-second
budget and do not claim exact minute matching. Rescaling the shortened first
major period previously moved its next subperiod by approximately 2h15m.

The nine visible monthly returns already agree within about 69 seconds after
the display-zone difference is accounted for. Their astronomical solver is
unchanged. Three later monthly timestamps were not visible and were not tested
against PL9.

## Remaining differences

Twelve of the fifteen Sahams common to the visible screenshot and our list use
compatible formulas. Yasha and Sastra agree within one arcsecond independently
of the location; most others retain an ascendant-dependent discrepancy of about
1′32″ with the provisional coordinates. Exact coordinates and house settings
are needed before changing location-dependent values. Artha and Paradesa have
larger differences consistent with different house cusps; no cusp convention
has been guessed or substituted.

The visible PL9 list additionally contains Mahatmya, Asha, Samartha, Gaurava,
Jeeva, Kali, Mrityu, Paradara, Vanik and Karyasiddhi. Their formulas are not
inferred from one numerical result. Aliases include Yasa/Yasha, Bhratru/Bhratri,
Pitru/Pitri, Raja/Rajya and Matru/Matri.

The application's selected Lagnesha/Karyesha yoga checks are not a complete
chart-wide PL9 report. Gairi-Kamboola and Kutta remain absent. Rudda, Nakata,
Yamaya, Khallsara, Duphali-Kutta, Tambira and Durupha have remaining definition
or scope differences. The PDF leaves strength thresholds and “unqualified Moon”
undefined; its Iqabala wording is also ambiguous. These are recorded rather
than silently replaced by unverified rules. The supplied Roga case is daytime;
night reversal remains the inherited convention, not verified PL9 parity.

## Validation

All 70 core XCTest tests passed on Linux in both Debug and Release, including
the original Python reference suite and 19 new reference/edge-case tests. This
count does not include the two unresolved node comparisons described above.
The application bridge and its hosted test source additionally passed type
checking with a temporary Combine shim; that shim is only a Linux compilation
aid. SwiftUI syntax and project checks passed. iOS/Catalyst compilation, UI
execution and the Apple-hosted application-wiring test require Xcode and have
not run in this Linux session.
