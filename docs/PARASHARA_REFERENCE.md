# Parashara’s Light 9 reference comparison

The November 20, 2026 comparison uses the user-supplied `tajika.pdf` and
screenshots of natal positions, the 2026–2027 Sahams, Mudda Dasha and monthly
charts, followed by `var.pdf` with exact annual positions and a second-precision
return time. The user identified the annual chart as December 27, 2026.
The PDF SHA-256 hashes are:

- `tajika.pdf`: `899c0cd47257fd6335856f1f2a4d0cf871616fc28c0fd1420787430856e468c9`
- `var.pdf`: `dc936cf6048c77af3b3d68b672238084b3a57f165b36bc57afad6bda7f43507b`

The original documents are not redistributed in the repository.

This is a partial reference comparison, not certification that all PL9
calculation options or all sixteen yogas are reproduced.

## Input and precision

The screenshot confirms December 26, 1976, 11:55:00, Sisak. The tests convert
this to 10:55 UTC using Europe/Zagreb. Latitude 45.4881 and longitude 16.3745
are provisional: the exact coordinates selected in PL9 have been requested.
No coordinate, ayanamsha, ascendant or time offset is fitted to make a test pass.

The screenshot prints natal planetary positions to seconds of arc. Seven
classical planets pass a 1 arcsecond comparison. Initially, the default Swiss
sidereal mean nodes differed by 8.75 arcseconds at birth and 9.98 arcseconds in
the annual chart. The app now uses an explicit alternate coordinate convention:
mean tropical node without nutation, minus true Lahiri ayanamsha. This agrees
with BOTH supplied node epochs within 1 arcsecond, without a fitted constant.
Node speed subtracts the ayanamsha's centered daily rate. The legacy Swiss
sidereal mode remains available and unchanged in the core library.

`var.pdf` gives the annual lagna as Sagittarius 12:15:23 and the return as
07:43:23 CET. Our return remains approximately 07:43:36.5405 CET, **13.5405 seconds
later**. Seven classical annual longitudes and their printed daily speeds agree
within one arcsecond at our computed return. At the PL printed UT, several
planetary positions differ more. A different Delta-T model is one possible
explanation, but the PDF does not specify it and the available Swiss historical
presets do not establish that explanation. No arbitrary time correction is made.

The location remains unconfirmed. At the PDF's UT, coordinates 45.45 N,
16.3667 E put the lagna about 4.10 arcseconds from the report, whereas the
provisional 45.4881 N, 16.3745 E differ by about 107.19 arcseconds. These are
coordinate diagnostics; the saved location has not been replaced by a fitted
value. The PDF names Sisak but does not print its coordinates or house options.

## Changes selected by both application targets

`NativeCalculations` selects the node convention for natal, annual, monthly
and transit charts, and the following conventions for annual calculations:

| Component | Application convention | Reference evidence |
| --- | --- | --- |
| Lunar nodes | `meanTropicalTrueAyanamsa`: non-nutated tropical mean node minus true Lahiri ayanamsha | Both natal and annual node longitudes within 1″; annual speed within 1″/day |
| Tajika aspects | `longitudeBothOrbs`: angular geometry, including sign-boundary aspects; residual inside both individual deeptamshas | Exact sets of six Ithasala and three Esharpha pairs in the PDF |
| Manau | In-orb conjunction, square or opposition from Mars/Saturn to the faster member, including a slower malefic member | Exact five qualifying pairs in the PDF |
| Mudda year | `fixedGregorianYear`: 365.2425 civil days | Eight major starts substantially closer than scaling to the next astronomical return |
| Mudda subperiods | Preserve the already-elapsed phase, then clip to the visible major period | Initial Sun subperiod starts in the screenshot |
| Roga Saham | `tajikaRoga`: Saturn − Moon + Asc in daytime, retaining arc correction | Reference operand matches; exact value still depends on the unconfirmed ascendant |

The aspect/orb convention is an explicit model consistent with this example;
one chart does not establish every internal PL9 rule. Actual signed ephemeris
speeds are used consistently in application pair and chart-wide aspect checks.
The unchanged Python comparison remains available through the explicit library
defaults `legacySignBased`, `solarReturnInterval`, `legacyPython` and `swissSidereal`.

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

Thirteen of the fifteen shared Sahams now pass a direct formula comparison
using the annual PDF's OWN rounded ascendant and planetary longitudes, with
Roga's corrected operand. Twelve are within 2 arcseconds and Mitra allows 3
arcseconds because it combines more rounded operands; the largest observed
residual is Mitra's 1 arcsecond. This verifies formulas separately from the
still-unresolved location/return-time calculation. The two fully computed,
ascendant-independent values Yasha and Sastra agree within one arcsecond.

Most other computed Sahams still show about 1′32″ ascendant-dependent difference
with the provisional coordinates. Exact coordinates, Delta-T and house settings
are needed before changing those values. Artha and Paradesa have larger
differences consistent with different house cusps; no cusp convention has been
guessed or substituted.

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

All 77 core XCTest tests passed on Linux in both Debug and Release, including
the original Python reference suite and 26 new external-reference/edge-case
tests. The application bridge and its hosted test source additionally passed
type checking with a temporary Combine shim; that shim is only a Linux
compilation aid. SwiftUI syntax and project checks passed. iOS/Catalyst compilation,
UI execution and the Apple-hosted application-wiring test require Xcode and
have not run in this Linux session.
