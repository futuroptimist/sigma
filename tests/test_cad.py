import re
from pathlib import Path

SCAD_PATH = Path("hardware/cad/sigma-s1-enclosure.scad")


def _extract_param(name: str) -> float:
    pattern = re.compile(rf"^{name}\s*=\s*([0-9]+(?:\.[0-9]+)?)", re.MULTILINE)
    match = pattern.search(SCAD_PATH.read_text(encoding="utf-8"))
    if not match:
        raise AssertionError(f"Parameter {name!r} not found in {SCAD_PATH}")
    return float(match.group(1))


def test_lanyard_hole_matches_documented_dimensions():
    diameter = _extract_param("lanyard_d")
    offset = _extract_param("lanyard_offset")
    assert diameter == 10.0
    assert offset == 6.0
