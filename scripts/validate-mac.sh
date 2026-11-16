#!/usr/bin/env bash
# Compile the Catalyst app with Apple's SDK. UI behavior still needs a Mac run.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$(uname -s)" != Darwin ]] || ! command -v xcodebuild >/dev/null; then
  echo 'Mac Catalyst validation requires macOS with full Xcode.' >&2
  exit 2
fi
python3 scripts/validate_xcode_project.py
mkdir -p .validation/mac
task_run_dir="$(mktemp -d "$PWD/.validation/mac/run.XXXXXX")"
xcodebuild build \
  -project Jyotish.xcodeproj -scheme Jyotish -configuration Debug \
  -destination 'platform=macOS,variant=Mac Catalyst' \
  -derivedDataPath "$task_run_dir/DerivedData" \
  CODE_SIGNING_ALLOWED=NO 2>&1 | tee "$task_run_dir/xcodebuild.log"
