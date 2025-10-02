from pathlib import Path


def test_stl_viewer_references_enclosure_file():
    viewer = Path("docs/sigma-s1-viewer.html")
    assert viewer.is_file()
    text = viewer.read_text(encoding="utf-8")
    assert "../hardware/stl/sigma-s1-enclosure.stl" in text
    assert "OrbitControls" in text
    assert "__sigmaViewer" in text
