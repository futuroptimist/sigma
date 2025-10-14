import re
from pathlib import Path

SCAD_PATH = Path("hardware/scad/sigma-s1-enclosure.scad")


def _read_scad() -> str:
    return SCAD_PATH.read_text(encoding="utf-8")


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


def test_enclosure_exposes_thickness_parameter():
    thickness = _extract_param("thickness")
    assert thickness == 2.0


def test_lanyard_hole_runs_front_to_back():
    text = _read_scad()
    pattern = re.compile(r"rotate\s*\(\s*\[\s*90\s*,\s*0\s*,\s*0\s*\]\s*\)")
    message = "lanyard hole should rotate cylinder front to back"
    assert pattern.search(text), message


def test_lanyard_hole_uses_documented_height_expression():
    text = _read_scad()
    assert "height - thickness - lanyard_d/2" in text
