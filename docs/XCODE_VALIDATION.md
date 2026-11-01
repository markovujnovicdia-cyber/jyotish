# Native iOS build and simulator validation

The `Jyotish` shared scheme builds the SwiftUI app and enables two iOS test targets. The app links the local `Packages/JyotishCore` package; neither package resolution nor calculations require an external ephemeris server. Swiss Ephemeris data is included in the package resource bundle. iOS 17 is the minimum deployment target.

Open `Jyotish.xcodeproj` in Xcode on macOS, select an installed iPhone simulator, then run or test the `Jyotish` scheme. Simulator builds do not require an Apple development team. For a physical iPhone, select your own Team and a unique bundle identifier in Signing & Capabilities. Distribution also requires resolving the Swiss Ephemeris licensing choice described in the project's license notes.

For repeatable validation from the repository root:

```bash
bash scripts/validate-ios.sh
```

The script checks project structure, runs the platform-independent Swift package tests, selects an available iPhone simulator with iOS 17 or later, boots it if necessary, and runs `xcodebuild test` with code signing disabled. An existing booted compatible simulator is preferred within the newest installed runtime. To choose a specific simulator, set `JYOTISH_SIMULATOR_UDID` to its UDID. To change the output location, set `JYOTISH_VALIDATION_DIR`.

Each invocation creates a new `.validation/ios/run.XXXXXX` directory containing that run's `xcodebuild.log` and `Jyotish.xcresult`. The pipeline retains the underlying `xcodebuild` exit status; a stale result bundle is never reused. The script does not delete simulator data, shut down an existing simulator, or erase saved people.

The hosted `JyotishTests` suite checks native Swiss Ephemeris results inside the iOS test host, invalid coordinates, selected-zone UTC conversion, daylight-saving gaps and folds, and person save/edit/delete/reload. Numerical core/parity coverage also runs independently through `swift test --package-path Packages/JyotishCore`.

The `JyotishUITests` suite checks creating a person and obtaining a natal result through the app, and refusing an out-of-range latitude. It launches with `-ui-testing-reset`, which selects and clears the dedicated `JyotishUITests` defaults suite. Production saved people are not cleared by this test argument.

The GitHub Actions workflow `.github/workflows/ios.yml` runs the same validation on `macos-15` for pushes, pull requests, and manual dispatch. It uploads current-run Xcode logs and result bundles, including failure results. Adding this workflow does not mean it has run: its first actual result must be inspected after the repository is pushed.

## What this Linux workspace can establish

`python3 scripts/validate_xcode_project.py` verifies the OpenStep project syntax, object references, build phases, file membership, three target definitions, package product linkage, deployment settings, removed server permissions, shared scheme, and icon resources. `bash -n scripts/validate-ios.sh` validates shell syntax. These are static checks; they do not typecheck SwiftUI or establish an iOS build, simulator launch, UI test pass, signing result, or App Store eligibility.

This development machine is Linux and has no `xcodebuild` or iPhone simulator. The iOS build and simulator tests must therefore be reported as **not executed here**, until the macOS validation produces a real result bundle. Running `validate-ios.sh` on Linux intentionally exits with status 2 and an explanation.

## Executed in this workspace (2026-11-01)

- Swift 6.0.3 on Linux: all **38 XCTest tests passed in Debug and Release**,
  compiling the actual vendored Swiss C sources and resolving bundled resources.
  This includes end-to-end Python parity, date/DST input, concurrent C access,
  invalid inputs and license/data resource checks. The separate Swift Testing
  runner's “0 tests” line does not describe the preceding 38-test XCTest suite.
- Actual app calculation/persistence sources compiled and ran against the core
  on Linux with a minimal temporary Combine shim: natal, five dasha levels,
  annual20 sahams,12 monthly charts, transit, and isolated person CRUD passed.
  This exercises Foundation/model code only; the shim supplies no SwiftUI or
  Apple SDK behavior.
- All five SwiftUI source files and iOS test files passed frontend syntax parse.
  Project graph, Bash syntax and source/data checksums passed.
- Original Python:225 passed,2 existing PDF-font failures.
- **Not executed:** Apple-SDK typechecking/linking, iPhone simulator launch,
  hosted XCTest, XCUITest, device signing or App Store submission. GitHub CI results have not been inspected.

No claim of a successful iOS build is made by these Linux checks.

## Simulator resource-path regression

A user-supplied iPhone simulator screenshot showed the app launching, but its
calculation reported `sepl_18.se1` missing from the default
`.:/users/ephe2/:/users/ephe/` search path. The Swift bundle lookup had already
found the two packaged data files. The cause is Swiss Ephemeris 2.10.03's
**242-byte UTF-8 limit** in `swe_set_ephe_path`: an excessive path is silently
replaced with that default. Simulator application/resource paths can exceed it.
This is a resource-location defect; changing astronomical formulas or accepting
Moshier output would not fix it.

The original Linux XCTest executable and its two resource bundles were copied
into a 358-byte Ephemeris path. Its real bundled-data test reproduced the exact
simulator error and exited with failure. This independently establishes the
cause without claiming an Apple simulator execution in this workspace.

The fix selects a supported private staging directory for long bundled paths,
retains the original bundled data, and rejects a C configuration that would
silently select another path/backend. The regression command below operates on
an **already built** package; it never launches a concurrent SwiftPM build:

```sh
bash scripts/test-core.sh
bash scripts/test-long-resource-path.sh debug
# After building the optimized test executable:
bash scripts/test-core.sh -c release
bash scripts/test-long-resource-path.sh release
```

This additional script is explicitly Linux-only. It copies the actual XCTest
executable plus both `.resources` bundles into a path longer than 350 UTF-8
bytes containing spaces and `Ž`, verifies that the selected suites contain
real tests, then executes the Swiss-resource/concurrency tests and end-to-end
Python parity tests. It propagates any runner failure. macOS/iPhone validation
continues to use the hosted tests and `scripts/validate-ios.sh`.

For the actual iOS host, run
`NativeCalculationTests.testJ2000ReferenceChartAndMeanNodes` in the `JyotishTests`
target on the affected simulator (or run the full shared scheme). That existing
test obtains data from the real application/package bundle and requires Swiss
results at strict reference precision. A naturally long simulator bundle path
therefore exercises the production staging code without exposing a test-only
resource override. A successful hosted result still requires execution on
macOS; the Linux relocation test does not substitute for it.

The repaired Debug and Release builds each passed all38 XCTest tests. The
relocation regression additionally ran4 ephemeris/resource/concurrency tests
and3 end-to-end parity tests successfully in both configurations, using real
resource directories over400UTF-8bytes. Four resource-resolver tests cover
short/long Unicode paths, cache deletion, stale-data replacement and clear
configuration failures. Vendored Swiss sources, data and Python formulas are
unchanged. Only the application adapter validates the library's path bound.
