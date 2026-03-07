# Build and Release macOS Without a Mac

You can build and publish the macOS deliverables on GitHub-hosted macOS runners.

## What is already prepared

This repository now includes:

- `.github/workflows/build-macos.yml`
- `.github/workflows/release-macos.yml`
- `build_macos_app.sh`
- `build_macos_pkg.sh`
- `build_macos_all.sh`

The workflow builds:

- `TEM8Practice.app.zip`
- `TEM8Practice-macOS.pkg`
- `self-check.json`

## Build workflow

Use `Build macOS Package` when you only want a test build artifact.

1. Put this project in a GitHub repository.
2. Push the current files.
3. Open the repository on GitHub.
4. Go to `Actions`.
5. Open `Build macOS Package`.
6. Click `Run workflow`.
7. Wait for the macOS job to finish.
8. Download the artifact named `TEM8Practice-macos`.

## Release workflow

Use `Release macOS Package` when you want a real GitHub Release.

It supports two ways:

- `workflow_dispatch`: run it manually and provide a tag such as `v2026.03.08`
- tag push: push a tag like `v2026.03.08`

The release workflow will:

- build `TEM8Practice.app.zip`
- build `TEM8Practice-macOS.pkg`
- build `self-check.json`
- upload `TEM8Practice-macos-release` as a workflow artifact
- create or update the corresponding GitHub Release

## Notes

- The build is unsigned. It is suitable for testing and direct manual distribution.
- If you need production distribution, you still need Apple code signing and notarization.
