# Hardware

This folder contains the hardware sources and exports for the Sigma S1
push-to-talk device.

- `scad/` – Parameterized OpenSCAD models for the enclosure.  Tune dimensions by
  editing [`inputs/enclosure.json`](inputs/enclosure.json); the STL build script
  injects those values via `openscad -D` flags.
- `stl/` – Auto-generated STL exports plus `checksums.sha256` for drift detection.

The enclosure includes cutouts for the button, microphone, speaker, battery,
USB-C port, a 5 mm status LED opening, and a 10 mm lanyard hole set 6 mm from the
left edge. The USB-C cutout is 14 mm wide for improved cable clearance.

## Editing parameters

Feed new dimensions into the SCAD by editing `inputs/enclosure.json`.  Run
`bash scripts/build_stl.sh` to regenerate meshes and the checksum manifest; the
script replays JSON values into OpenSCAD on every export.

## Safety guidance

Refer to [`docs/hardware/safety.md`](../docs/hardware/safety.md) for headset
SPL limits, microphone bias recommendations, and battery/charging cautions.
