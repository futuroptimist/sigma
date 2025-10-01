from __future__ import annotations

import re
from pathlib import Path

SCAD_PATH = Path("hardware/cad/sigma-s1-enclosure.scad")
DOC_PATH = Path("docs/sigma-s1-assembly.md")


def test_lanyard_hole_matches_documentation():
    scad_text = SCAD_PATH.read_text(encoding="utf-8")
    match = re.search(r"lanyard_d\s*=\s*([0-9]+(?:\.[0-9]+)?)", scad_text)
    assert match, "lanyard_d parameter not found in SCAD file"
    scad_value = float(match.group(1))
    assert scad_value == 10

    doc_text = DOC_PATH.read_text(encoding="utf-8")
    assert "hole is 10\u00a0mm in diameter" in doc_text
