#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script must be run on macOS."
  exit 1
fi

APP_NAME="${APP_NAME:-TEM8Practice}"
TARGET_ARCH="${TARGET_ARCH:-$(uname -m)}"
APP_PATH="${ROOT_DIR}/release/macos/${TARGET_ARCH}/dist/${APP_NAME}.app"
PKG_ROOT="${ROOT_DIR}/release/macos/${TARGET_ARCH}/pkgroot"
PKG_SCRIPTS="${ROOT_DIR}/packaging/macos/scripts"
PKG_PATH="${ROOT_DIR}/release/macos/${APP_NAME}-macOS-${TARGET_ARCH}.pkg"

if [[ ! -d "$APP_PATH" ]]; then
  "$ROOT_DIR/build_macos_app.sh"
fi

if [[ ! -d "$APP_PATH" ]]; then
  echo "App bundle not found: $APP_PATH"
  exit 1
fi

rm -rf "$PKG_ROOT" "$PKG_PATH"
mkdir -p "$PKG_ROOT/Applications"
cp -R "$APP_PATH" "$PKG_ROOT/Applications/"
chmod +x "$PKG_SCRIPTS/preinstall" "$PKG_SCRIPTS/postinstall"

pkgbuild \
  --root "$PKG_ROOT" \
  --identifier "com.hw.tem8practice" \
  --version "2026.03.07" \
  --install-location "/" \
  --scripts "$PKG_SCRIPTS" \
  "$PKG_PATH"

echo "Built package ($TARGET_ARCH): $PKG_PATH"
