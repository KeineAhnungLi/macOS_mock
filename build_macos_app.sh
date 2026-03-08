#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script must be run on macOS."
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
APP_NAME="${APP_NAME:-TEM8Practice}"
TARGET_ARCH="${TARGET_ARCH:-$(uname -m)}"
BUILD_VENV="${ROOT_DIR}/.venv-macos-build"
DIST_DIR="${ROOT_DIR}/release/macos/${TARGET_ARCH}/dist"
BUILD_DIR="${ROOT_DIR}/release/macos/${TARGET_ARCH}/build"
SPEC_DIR="${ROOT_DIR}/release/macos/${TARGET_ARCH}/spec"
APP_PATH="${DIST_DIR}/${APP_NAME}.app"
STATIC_SRC="${ROOT_DIR}/app/static"
QUESTIONS_SRC="${ROOT_DIR}/data/questions.json"
ANSWER_KEY_SRC="${ROOT_DIR}/data/answer_key.json"
ANSWER_KEY_TEMPLATE_SRC="${ROOT_DIR}/data/answer_key.template.json"

"$PYTHON_BIN" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 'Python 3.10+ is required.')"

if [[ ! -d "$BUILD_VENV" ]]; then
  "$PYTHON_BIN" -m venv "$BUILD_VENV"
fi

source "$BUILD_VENV/bin/activate"
python --version
uname -a
python -m pip install --upgrade pip setuptools wheel pyinstaller
pyinstaller --version

rm -rf "$DIST_DIR" "$BUILD_DIR" "$SPEC_DIR"
mkdir -p "$DIST_DIR" "$BUILD_DIR" "$SPEC_DIR"

pyinstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "$APP_NAME" \
  --target-arch "$TARGET_ARCH" \
  --distpath "$DIST_DIR" \
  --workpath "$BUILD_DIR" \
  --specpath "$SPEC_DIR" \
  --osx-bundle-identifier "com.hw.tem8practice" \
  --add-data "${STATIC_SRC}:app/static" \
  --add-data "${QUESTIONS_SRC}:data" \
  --add-data "${ANSWER_KEY_SRC}:data" \
  --add-data "${ANSWER_KEY_TEMPLATE_SRC}:data" \
  gateway.py

if [[ ! -d "$APP_PATH" ]]; then
  echo "Expected app bundle was not created: $APP_PATH"
  exit 1
fi

ls -la "$DIST_DIR"

if command -v codesign >/dev/null 2>&1; then
  if ! codesign --force --deep --sign - "$APP_PATH"; then
    echo "Warning: ad-hoc codesign failed, continuing with unsigned app."
  fi
fi

echo "Built app ($TARGET_ARCH): $APP_PATH"
