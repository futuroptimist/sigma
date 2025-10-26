# STL checksum manifest

The Sigma CAD toolchain commits rendered meshes alongside a checksum manifest so
regressions are detected automatically.

## Regenerating meshes

1. Adjust OpenSCAD parameters in [`hardware/inputs`](../../hardware/inputs/) as
   needed.
2. Run the build script from the repository root:

   ```bash
   bash scripts/build_stl.sh
   ```

   The script renders every SCAD file in [`hardware/scad`](../../hardware/scad/)
   into [`hardware/stl`](../../hardware/stl/) and rewrites
   `hardware/stl/checksums.sha256` with SHA-256 hashes. Manifest entries are
   recorded relative to the repository root (for example
   `hardware/stl/sigma-s1-enclosure.stl`) so CI tooling can compare them
   directly against regenerated exports.

3. Commit both the `.stl` exports and the checksum manifest together.

## Verifying in CI

[`infra/ci/stl_regression.py`](../../infra/ci/stl_regression.py) is executed by
GitHub Actions (see `.github/workflows/scad-to-stl.yml`).  It reruns the build
script, recomputes hashes, and fails if the manifest disagrees with the freshly
rendered meshes.  Run the script locally before pushing to mirror CI:

```bash
python infra/ci/stl_regression.py
```

The script prints `[infra] STL manifest verified.` when the manifest matches.
Any drift reports missing, extra, or mismatched entries with actionable detail.

## Safety and documentation coupling

- The manifest lives alongside [`docs/hardware/safety.md`](safety.md) so acoustic
  limits, microphone bias guidance, and battery cautions stay in lockstep with
  the printed enclosure revisions.
- Update the manifest whenever the enclosure geometry changes so assembly notes
  and exploded diagrams remain accurate.

Following this flow keeps CAD artifacts reproducible and traceable through CI.
