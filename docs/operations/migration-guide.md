# Repository migration guide

This release restructures firmware, CAD assets, and automation so downstream
projects can consume Sigma components more easily.

## Layout changes

- Firmware moved from `firmware/` to `apps/firmware/`.
- OpenSCAD sources now live in `hardware/scad/` with parameter files in
  `hardware/inputs/`.
- STL checksum manifests are stored in `hardware/stl/checksums.sha256`.
- Docs preview tooling lives in `viewer/` with a lightweight Node server.
- CI automation scripts reside in `infra/`.

Update your environment variables, IDE workspace settings, and scripts to point
at the new paths.

## Firmware configuration

- Include headers from `apps/firmware/include/` instead of macros passed via
  PlatformIO `build_flags`.
- Copy `config.secrets.example.h` for any Wi-Fi or API keys.
- Run `pio run -d apps/firmware`, `pio test -d apps/firmware -e native`, and
  `pio run -d apps/firmware --target upload` from the repository root to keep
  relative paths working with CI.

## CAD regeneration

- Adjust enclosure dimensions in `hardware/inputs/enclosure.json`.
- Run `bash scripts/build_stl.sh` to rebuild meshes and refresh the checksum
  manifest.
- Commit `hardware/stl/*.stl` and `hardware/stl/checksums.sha256` together.

## Infra checks

- The STL workflow now calls `infra/ci/stl_regression.py`; run it locally when
  updating CAD to reproduce CI behaviour.
- `pre-commit run --all-files`, `make test`, `pio run -d apps/firmware`, and
  `pio test -d apps/firmware -e native` remain mandatory before submitting PRs.

## Viewer usage

- Serve docs locally via `cd viewer && npm run dev`.
- Preview the STL safety callouts and assembly diagrams introduced in this
  release from the running server at `http://localhost:4173`.

Following these steps keeps firmware, CAD, documentation, and automation aligned
with the new project structure.
