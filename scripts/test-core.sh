#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -n "${JYOTISH_SWIFT_BIN:-}" ]]; then
  task_swift="$JYOTISH_SWIFT_BIN"
elif command -v swift >/dev/null; then
  task_swift="$(command -v swift)"
elif [[ -x /workspace/toolchains/swift-6.0.3-RELEASE-ubuntu22.04/usr/bin/swift ]]; then
  task_swift=/workspace/toolchains/swift-6.0.3-RELEASE-ubuntu22.04/usr/bin/swift
else
  echo 'Swift 5.9+ is required. On macOS, select full Xcode; on Linux install an official signed Swift toolchain.' >&2
  exit 2
fi
export CLANG_MODULE_CACHE_PATH="${CLANG_MODULE_CACHE_PATH:-$PWD/.validation/clang}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$PWD/.validation/cache}"
exec "$task_swift" test --package-path Packages/JyotishCore \
  --cache-path "$XDG_CACHE_HOME/swiftpm" --jobs "${JYOTISH_BUILD_JOBS:-4}" "$@"
