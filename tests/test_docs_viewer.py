from pathlib import Path


def test_sigma_s1_viewer_exists_and_references_stl():
    viewer_doc = Path("docs/sigma-s1-viewer.md")
    stl_path = Path("hardware/stl/sigma-s1-enclosure.stl")

    assert viewer_doc.is_file(), "3D viewer documentation is missing"
    assert stl_path.is_file(), "STL asset referenced by the viewer is missing"

    content = viewer_doc.read_text(encoding="utf-8")
    assert "<model-viewer" in content
    assert "hardware/stl/sigma-s1-enclosure.stl" in content
    assert "model-viewer.min.js" in content
