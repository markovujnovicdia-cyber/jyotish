#!/usr/bin/env bash
# Compile the app, execute hosted/unit/UI tests, and retain the actual xcresult.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$(uname -s)" != Darwin ]] || ! command -v xcodebuild >/dev/null; then
  echo 'iOS validation requires macOS with full Xcode and an installed iOS 17+ simulator.' >&2
  exit 2
fi
python3 scripts/validate_xcode_project.py
xcodebuild -version
validation_dir="${JYOTISH_VALIDATION_DIR:-$PWD/.validation/ios}"
mkdir -p "$validation_dir"
# A new result path prevents an older successful run from being mistaken for this run.
run_dir="$(mktemp -d "$validation_dir/run.XXXXXX")"
set +e
swift test --package-path Packages/JyotishCore 2>&1 | tee "$run_dir/swift-test.log"
core_status=${PIPESTATUS[0]}
set -e
if [[ "$core_status" -ne 0 ]]; then
  python3 scripts/report-ci-errors.py "$run_dir/swift-test.log" 'Swift core tests'
  exit "$core_status"
fi
xcrun simctl list devices available --json > "$run_dir/devices.json"
simulator_id="$(python3 - "$run_dir/devices.json" "${JYOTISH_SIMULATOR_UDID:-}" <<'PY'
import json,re,sys
with open(sys.argv[1]) as f: runtimes=json.load(f)['devices']
choices=[]
for runtime, devices in runtimes.items():
 match=re.search(r'\.iOS-(\d+)-(\d+)(?:-(\d+))?$',runtime)
 if not match or int(match.group(1))<17: continue
 version=tuple(int(part or 0) for part in match.groups())
 for device in devices:
  if device.get('isAvailable') and device['name'].startswith('iPhone'):
   choices.append((version,device.get('state')=='Booted',device['name'],device['udid']))
requested=sys.argv[2]
if requested:
 choices=[entry for entry in choices if entry[-1]==requested]
if not choices:
 raise SystemExit('No matching available iPhone simulator with iOS 17+. Install one in Xcode Settings > Platforms.')
print(max(choices)[-1])
PY
)"
printf 'Selected iPhone simulator: %s\n' "$simulator_id"
# Avoid trying to boot an already booted device. bootstatus waits for readiness.
if ! xcrun simctl list devices booted --json | python3 -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if any(v["udid"]==sys.argv[1] for a in d["devices"].values() for v in a) else 1)' "$simulator_id"; then
  xcrun simctl boot "$simulator_id"
fi
xcrun simctl bootstatus "$simulator_id" -b
set +e
xcodebuild test \
  -project Jyotish.xcodeproj \
  -scheme Jyotish \
  -configuration Debug \
  -destination "platform=iOS Simulator,id=$simulator_id" \
  -derivedDataPath "$run_dir/DerivedData" \
  -resultBundlePath "$run_dir/Jyotish.xcresult" \
  -parallel-testing-enabled NO \
  CODE_SIGNING_ALLOWED=NO \
  2>&1 | tee "$run_dir/xcodebuild.log"
ios_status=${PIPESTATUS[0]}
set -e
if [[ "$ios_status" -ne 0 ]]; then
  python3 scripts/report-ci-errors.py "$run_dir/xcodebuild.log" 'iOS build or simulator tests'
  exit "$ios_status"
fi
printf 'Simulator tests completed. Results: %s\n' "$run_dir/Jyotish.xcresult"
