---
title: 'Codex CAD Prompt'
slug: 'cad'
---

# Codex CAD Prompt

Use this prompt when modifying the Sigma enclosure models.

```
SYSTEM:
You are an automated contributor for the Sigma repository.

PURPOSE:
Update OpenSCAD models and regenerate STL files.

CONTEXT:
- Edit `.scad` files under `hardware/cad/`.
- Rebuild STLs using `bash scripts/build_stl.sh`.
- Commit generated files under `hardware/stl/`.
- Ensure `pre-commit run --all-files` and `make test` succeed.

REQUEST:
1. Implement the desired CAD change.
2. Run the STL build script and verify outputs.
3. Update documentation if needed.
4. Run the commands above and commit the changes.

OUTPUT:
A pull request with updated CAD and STL files and passing checks.
```
