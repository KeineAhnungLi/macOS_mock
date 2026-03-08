#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script must be run on macOS."
  exit 1
fi

if ! command -v xcode-select >/dev/null 2>&1; then
  echo "xcode-select is required."
  exit 1
fi

if ! xcode-select -p >/dev/null 2>&1; then
  echo "Xcode Command Line Tools are required. Run: xcode-select --install"
  exit 1
fi

if ! command -v pkgbuild >/dev/null 2>&1; then
  echo "pkgbuild is missing. Install Xcode Command Line Tools first: xcode-select --install"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 3.10+ is required on the build machine."
  exit 1
fi

chmod +x build_macos_app.sh build_macos_pkg.sh packaging/macos/scripts/preinstall packaging/macos/scripts/postinstall

TARGET_ARCH="${TARGET_ARCH:-$(uname -m)}"
./build_macos_app.sh
./release/macos/"$TARGET_ARCH"/dist/TEM8Practice.app/Contents/MacOS/TEM8Practice --self-check-json
./build_macos_pkg.sh

echo
echo "Build finished."
echo "Arch: $TARGET_ARCH"
echo "App: $ROOT_DIR/release/macos/$TARGET_ARCH/dist/TEM8Practice.app"
echo "Pkg: $ROOT_DIR/release/macos/TEM8Practice-macOS-$TARGET_ARCH.pkg"
