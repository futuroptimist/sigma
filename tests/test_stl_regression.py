from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


def test_compute_checksums_uses_repo_relative_paths(tmp_path, monkeypatch):
    module_path = Path("infra/ci/stl_regression.py")
    load_spec = importlib.util.spec_from_file_location
    spec = load_spec("stl_regression", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    repo_root = tmp_path / "repo"
    stl_root = repo_root / "hardware" / "stl"
    nested_dir = stl_root / "nested"
    nested_dir.mkdir(parents=True)

    top = stl_root / "top.stl"
    top.write_bytes(b"top")
    inner = nested_dir / "inner.stl"
    inner.write_bytes(b"nested")

    monkeypatch.setattr(module, "REPO_ROOT", repo_root)
    monkeypatch.setattr(module, "STL_DIR", stl_root)

    result = module.compute_checksums()

    expected = {
        "hardware/stl/top.stl": hashlib.sha256(b"top").hexdigest(),
        "hardware/stl/nested/inner.stl": hashlib.sha256(b"nested").hexdigest(),
    }

    assert result == expected
