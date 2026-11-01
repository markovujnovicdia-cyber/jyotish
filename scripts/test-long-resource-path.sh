#!/usr/bin/env bash
# Exercise the existing Linux XCTest executable after relocating its resource
# bundles into a simulator-like path. This command never starts a Swift build.
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ "$(uname -s)" != Linux ]]; then
  echo 'This relocation regression uses the Linux standalone XCTest executable. On macOS run scripts/validate-ios.sh for the iOS host/resource tests.' >&2
  exit 2
fi

configuration="${1:-debug}"
if [[ "$#" -gt 1 || ( "$configuration" != debug && "$configuration" != release ) ]]; then
  echo 'Usage: bash scripts/test-long-resource-path.sh [debug|release]' >&2
  exit 2
fi

python3 - "$PWD/Packages/JyotishCore/.build/$configuration" <<'PY'
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile

build = Path(sys.argv[1])
binary_name = 'JyotishCorePackageTests.xctest'
bundles = (
    'JyotishCore_JyotishCore.resources',
    'JyotishCore_JyotishCoreTests.resources',
)
if not (build / binary_name).is_file():
    raise SystemExit('Build the selected configuration first: bash scripts/test-core.sh' +
                     (' -c release' if build.name == 'release' else ''))
for name in bundles:
    if not (build / name).is_dir():
        raise SystemExit(f'Missing resource bundle from selected build: {name}')

with tempfile.TemporaryDirectory(prefix='jyotish long bundle regression-') as temporary:
    relocated = Path(temporary).resolve()
    # Individual filesystem components remain short; the total UTF-8 pathname
    # intentionally exceeds Swiss Ephemeris 2.10.03's 242-byte path limit.
    while len(str(relocated).encode('utf-8')) <= 350:
        relocated /= 'simulator profile Ž-' + 'resource-container-' * 2
    relocated.mkdir(parents=True)
    executable = relocated / binary_name
    shutil.copy2(build / binary_name, executable)
    for name in bundles:
        shutil.copytree(build / name, relocated / name)

    ephemeris = relocated / bundles[0] / 'Ephemeris'
    length = len(str(ephemeris).encode('utf-8'))
    assert length > 350 and ' ' in str(ephemeris) and 'Ž' in str(ephemeris)
    for name in ('sepl_18.se1', 'semo_18.se1'):
        assert (ephemeris / name).is_file(), f'Copied data is missing: {name}'
    print(f'Relocated bundled Ephemeris path: {length} UTF-8 bytes (spaces and Unicode included).', flush=True)

    # A successful runner exit with no selected tests would not establish that
    # bundled Swiss data or numerical parity was exercised.
    listing = subprocess.run([str(executable), '--dump-tests-json'], capture_output=True, text=True)
    if listing.returncode:
        sys.stdout.write(listing.stdout)
        sys.stderr.write(listing.stderr)
        raise SystemExit(listing.returncode if listing.returncode > 0 else 128 - listing.returncode)
    catalog = json.loads(listing.stdout)
    suites = {}
    def collect(node):
        children = node.get('tests', [])
        if node.get('name', '').startswith('JyotishCoreTests.'):
            suites[node['name']] = children
        for child in children:
            collect(child)
    collect(catalog)
    for suite in ('JyotishCoreTests.EphemerisTests', 'JyotishCoreTests.PythonParityTests'):
        if not suites.get(suite):
            raise SystemExit(f'Required nonempty test suite unavailable: {suite}')
        print(f'Executing relocated {suite}: {len(suites[suite])} tests.', flush=True)
        result = subprocess.run([str(executable), suite])
        if result.returncode:
            raise SystemExit(result.returncode if result.returncode > 0 else 128 - result.returncode)
    print('PASS actual relocated Swiss-resource and Python-parity suites.', flush=True)
PY
