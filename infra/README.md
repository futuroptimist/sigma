# Sigma infrastructure

Automation helpers that keep the repo reproducible.

- `ci/stl_regression.py` – rebuilds OpenSCAD sources, regenerates STL exports,
  and verifies `hardware/stl/checksums.sha256` matches the results.

CI uses these helpers to enforce that CAD outputs, firmware safety rails, and
documentation stay synchronized.
