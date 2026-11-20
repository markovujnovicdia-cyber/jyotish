# Parashara’s Light 9 reference comparison

This comparison uses the user-supplied `tajika.pdf`, `var.pdf` and screenshots
of natal positions, Sahams, Mudda periods, monthly charts, birth coordinates
and calculation preferences. The annual reference is December 27, 2026.

- `tajika.pdf` SHA-256: `899c0cd47257fd6335856f1f2a4d0cf871616fc28c0fd1420787430856e468c9`
- `var.pdf` SHA-256: `dc936cf6048c77af3b3d68b672238084b3a57f165b36bc57afad6bda7f43507b`

The original documents are not redistributed. The verified comparisons below
do not establish equivalence with every PL9 option or every Tajika yoga.

## Confirmed inputs and preferences

The birth screenshot gives December 26, 1976, 11:55:00, Sisak:

- Latitude **45°27′00″ N = 45.45**.
- Longitude **16°22′00″ E = 16.366666666666667**.
- PL9 timezone field `−01:00:00` is the correction to UTC; DST is zero.
  Europe/Zagreb resolves this birth uniquely to **10:55 UTC**, not UTC−1.
- Lahiri ayanamsha, additional offset zero; mean Rahu/Ketu.
- True solar return; Vimshottari year **365.25 days**, balance by degree.
- The selected annual-period method is Mudda dasha. Its separate observed
  fixed-year convention is not inferred from the Vimshottari year setting.

Reference tests now use the confirmed coordinates rather than the previously
provisional 45.4881/16.3745. Other people's data and the GeoNames city catalog
are not rewritten. On an existing Mac/iPhone profile, manually enter latitude
`45,45`, longitude `16,3666666667`, and zone `Europe/Zagreb` to compare this case.
The app accepts decimal commas or dots and now shows the saved coordinates.

## Application conventions

Both targets share `NativeCalculations` and the core package. They select:

| Component | Convention | Evidence |
| --- | --- | --- |
| Zodiac | Lahiri, zero additional offset | User preference screenshot; seven classical natal/annual longitudes within 1″ |
| Mean nodes | `meanTropicalTrueAyanamsa`: non-nutated tropical mean node minus true Lahiri ayanamsha | Both supplied node epochs within 1″; annual speed within 1″/day |
| Vimshottari | `.julian`, 365.25 days, initial Moon fraction by degree | User preference screenshot; cycle/balance/boundary tests |
| Tajika aspects | `longitudeBothOrbs`: angular geometry, residual inside both individual deeptamshas | Exact six Ithasala and three Esharpha pairs |
| Manau | In-orb hostile aspect from Mars/Saturn to the faster member, including a slower malefic member | Exact five qualifying pairs |
| Mudda | Fixed 365.2425-day year; preserve the elapsed phase before clipping subperiods | Supplied major/subperiod tables; distinct from Vimshottari |
| Sahams | `tajikaSripati`: corrected Roga operand and Sripati cusp longitudes, retaining whole-sign house lords | Fifteen shared Sahams from the external reports |

The app's **Model vremena** selector controls the time convention separately.
Changing it recomputes the same selected annual year, without resetting the
comparison to the currently active annual year.

### Reference time model

`historical2019Forecast` reproduces the published future Delta-T formula from
an authoritative Swiss Ephemeris `swephlib.c` whose observational table ends in
2019 at 69.50 seconds. Its blend approaches the Stephenson (1997) quadratic.
It is not a fitted offset or a claim to know PL9's proprietary implementation.

Source commit: `cb7971a07d166ff8768e22247f63568718f2cd66` in
[aloistr/swisseph](https://github.com/aloistr/swisseph/blob/cb7971a07d166ff8768e22247f63568718f2cd66/swephlib.c).
Source SHA-256: `af3bd16fb4213eae201c146f156df0cd6421b0cdecb20a9258cde4132393ac9f`.
Tag labels and the embedded version disagree, so the implementation pins the
commit and formula instead of claiming a particular engine version.

The alternate forecast applies after fractional year 2019; earlier epochs keep
the current observed Swiss model. It is a comparison profile, not a complete
historical engine. The **Aktualni Swiss** option retains the current Delta-T
model. Every calculation restores its selected convention under the ephemeris
lock; interleaving modes is tested.

At the printed annual UTC, current Swiss Delta-T is about 68.8008 seconds and
the historical forecast about 82.2088 seconds. With the latter, the real native
calculation bridge returns **06:43:23.183 UTC**, versus PL9's printed
**06:43:23 UTC**. The current mode returns about 13.35 seconds later.
The root test uses a 0.5-second budget, matching the report's second precision.
No solar-longitude, timestamp or ascendant correction is added to fit this case.

## Verified comparisons

The external pair sets are checked in full, including absence of extra pairs:

- Ithasala: Mercury–Sun, Mercury–Mars, Mercury–Saturn, Sun–Mars, Sun–Saturn,
  Moon–Jupiter.
- Esharpha: Moon–Venus, Mercury–Jupiter, Sun–Jupiter.
- Manau: Mercury–Sun, Mercury–Mars, Mercury–Saturn, Sun–Mars, Sun–Saturn.

The Moon–Jupiter conjunction crosses a sign boundary and was previously
rejected. An averaged angular orb admits an extra Venus–Jupiter pair; requiring
both individual deeptamshas matches the supplied list. This is an explicit
model consistent with the examples, not proof of every internal PL9 rule.

Thirteen shared Sahams match direct formula checks using the annual PDF's own
rounded inputs: twelve within 2″ and Mitra within 3″ to propagate the input
rounding. Artha and Paradesa additionally match using Sripati cusp longitudes
and whole-sign house lords. Substituting the cusp-sign lord would be incorrect
for this reference.

All **fifteen** shared Sahams also pass an end-to-end calculation from the
confirmed birth data and reference time model, with a separate **10″** budget.
That budget includes the one-second reference-time precision and small residual
local-angle differences. It does not replace the stricter direct-formula tests.
Small ascendant differences remain: about 3.69″ at birth and a few arcseconds
in the annual comparison, with no fitted coordinate or ayanamsha offset.

## Periods and display zones

The screenshots use fixed CET (+01:00), including summer. The app offers this
fixed-offset display alongside historical Europe/Zagreb (+02:00 in summer).
Only the clock display changes; the birth zone and computed instant do not.

The supplied Mudda tables support a fixed near-tropical year. Their minute
precision cannot uniquely distinguish 365.2425 from 365.2422 days. The tests
retain a documented 90-second comparison budget for eight major boundaries
and five initial subperiod starts. Rescaling the shortened first major period
previously displaced the next subperiod by approximately 2h15m; preserving the
elapsed phase corrects that error.

Nine monthly timestamps have external references; three were not visible.
The older current-time comparison remains tested within 90 seconds. Monthly
calculations in the app now carry the selected time model consistently with
the annual solver. Vimshottari's confirmed 365.25-day preference is tested
independently and does not silently alter the separate Mudda convention.

## Remaining scope

The PL list contains ten additional names absent from our current twenty:
Mahatmya, Asha, Samartha, Gaurava, Jeeva, Kali, Mrityu, Paradara, Vanik and
Karyasiddhi. Their formulas are not inferred from a single numerical result.
Aliases include Yasa/Yasha, Bhratru/Bhratri, Pitru/Pitri, Raja/Rajya, Matru/Matri.

Selected Lagnesha/Karyesha checks are not the complete chart-wide PL9 yoga
report. Gairi-Kamboola and Kutta remain absent; several other yogas have
remaining definition or scope differences. Strength thresholds and “unqualified
Moon” are not numerically specified by the supplied report. Roga's supplied
case is daytime; its night reversal remains the inherited convention.

## Validation

All **92 core XCTest tests pass** in Linux Debug and Release. They include
external report checks, historical-forecast values from a separately compiled
authoritative source, time-mode isolation, Sripati/lord selection, degree-based
Vimshottari balance and the original unchanged Python-reference checks.

The actual application calculation bridge is also compiled and executed with
a temporary Combine shim: annual time-model switching, six/three pair sets,
365.25-day dasha selection and twelve monthly returns pass. The shim is only a
Linux compilation aid; it is not an Apple UI test. Application/hosted-test type
checking, SwiftUI syntax and project checks are performed. iOS/Catalyst builds
and UI execution require Xcode and have not run in this Linux session.
