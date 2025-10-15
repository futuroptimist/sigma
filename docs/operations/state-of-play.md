# Sigma repository inventory

This snapshot documents how the repository is organized after the migration to
`apps/` and `hardware/scad`.

## Directory ownership

- `apps/firmware/` – Firmware team (PlatformIO project, configuration headers,
  Unity tests).
- `apps/firmware/include/` – Holds `config.h` plus the `config.secrets` template
  that downstream device builders copy and fill outside of source control.
- `hardware/` – Hardware team (OpenSCAD sources in `hardware/scad`, generated
  STL exports in `hardware/stl`, checksum manifests).
- `docs/` – Documentation team (assembly manual, operational guides, SPL
  guidance, charging cautions, STL checksum instructions).
- `scripts/` – Release engineering (helper scripts for CAD, linting, and
  safety/secret scanning).
- `infra/` – CI automation and reproducibility tooling.
- `sigma/` – Audio pipeline runtime shared by host-side utilities.
- `tests/` – Python test suite covering CAD constraints, firmware config, LLM
  routing, and supporting scripts.
- `viewer/` – Lightweight Node server for previewing docs and STL safety callouts.

## PlatformIO environments

`apps/firmware/platformio.ini` defines:

- `env:esp32dev` for ESP32 hardware builds using the Arduino framework at
  115200 baud.
- `env:native` for host-side builds that exercise Unity tests without the
  toolchain.

Run `pio run` to build the device image and `pio test -e native` to execute the
Unity tests.

## Flashing workflow

1. Install PlatformIO Core (`pip install platformio`).
2. Connect the ESP32 board over USB.
3. From the repository root: `pio run` then `pio run --target upload`.
4. Monitor serial output at 115200 baud (`pio device monitor`).

Configuration and safety limits live in `apps/firmware/include/config.h`; keep
credentials out of the repo by copying `config.secrets.example.h`.

## STL regeneration

OpenSCAD sources reside in `hardware/scad`.  Regenerate STLs and the checksum
manifest with:

```bash
bash scripts/build_stl.sh
```

The script writes exports into `hardware/stl` and records SHA-256 hashes in
`hardware/stl/checksums.sha256`.  CI validates that the manifest matches the
committed meshes.

## LLM routing and secrets

`llms.py` reads endpoint metadata from [`llms.txt`](../llms.txt).  The parser
supports comments, default fallbacks, and tags; see
[`tests/test_llms.py`](../tests/test_llms.py) for coverage.  Secrets are loaded
from environment variables or `.env` files—start from the tracked
[`.env.example`](../.env.example) for host services and from
`apps/firmware/include/config.secrets.example.h` for embedded credentials.
Never commit real tokens.  The `scripts/llms-cli.sh` helper bootstraps
`PYTHONPATH` so the CLI works from any directory.

## Release support scripts

- `scripts/checks.sh` – wrapper that runs formatting, lint, and pytest.
- `scripts/build_stl.sh` – regenerates OpenSCAD models and checksum manifests.
- `scripts/scan-secrets.py` – pre-commitable secret scanner.
- `infra/ci/stl_regression.py` – invoked by CI to rebuild CAD assets and assert
  the manifest is up to date.
