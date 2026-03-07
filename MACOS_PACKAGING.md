# macOS Packaging

## What this produces

- `build_macos_app.sh`: builds `release/macos/dist/TEM8Practice.app`
- `build_macos_pkg.sh`: builds `release/macos/TEM8Practice-macOS.pkg`

## macOS build machine requirements

- macOS 12+
- `python3` 3.10+
- network access for first-time `pip install pyinstaller`
- optional: Google Chrome installed in `/Applications/Google Chrome.app`

## Build commands

```bash
chmod +x build_macos_app.sh build_macos_pkg.sh
./build_macos_pkg.sh
```

## Runtime behavior on macOS

- bundled app does not require a separate Python install for end users
- user data is written to `~/Library/Application Support/TEM8Practice`
- if Chrome exists, the app prefers Chrome
- if Chrome does not exist, the app falls back to the default browser

## Self-check

After building, you can inspect runtime dependencies with:

```bash
./release/macos/dist/TEM8Practice.app/Contents/MacOS/TEM8Practice --self-check-json
```
