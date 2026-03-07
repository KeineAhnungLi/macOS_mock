# Build macOS Without a Mac

You can build the macOS deliverables on GitHub-hosted macOS runners.

## What is already prepared

This repository now includes:

- `.github/workflows/build-macos.yml`
- `build_macos_app.sh`
- `build_macos_pkg.sh`
- `build_macos_all.sh`

The workflow builds:

- `TEM8Practice.app.zip`
- `TEM8Practice-macOS.pkg`
- `self-check.json`

## How to use

1. Put this project in a GitHub repository.
2. Push the current files.
3. Open the repository on GitHub.
4. Go to `Actions`.
5. Open `Build macOS Package`.
6. Click `Run workflow`.
7. Wait for the macOS job to finish.
8. Download the artifact named `TEM8Practice-macos`.

## Notes

- The build is unsigned. It is suitable for testing and direct manual distribution.
- If you need production distribution, you still need Apple code signing and notarization.
