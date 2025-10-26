#!/usr/bin/env python3
"""CI helper that rebuilds STLs and verifies checksum manifests."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STL_DIR = REPO_ROOT / "hardware" / "stl"
MANIFEST = STL_DIR / "checksums.sha256"


def run_build() -> None:
    subprocess.run(["bash", "scripts/build_stl.sh"], cwd=REPO_ROOT, check=True)


def read_manifest() -> dict[str, str]:
    mapping: dict[str, str] = {}
    if not MANIFEST.exists():
        raise SystemExit(f"Missing checksum manifest: {MANIFEST}")
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        digest, _, rel = line.partition("  ")
        if not digest or not rel:
            raise SystemExit(f"Malformed manifest entry: {line!r}")
        mapping[rel.strip()] = digest.strip()
    return mapping


def compute_checksums() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for stl in sorted(STL_DIR.rglob("*.stl")):
        digest = hashlib.sha256(stl.read_bytes()).hexdigest()
        try:
            relative_path = stl.relative_to(REPO_ROOT)
        except ValueError:
            relative_path = stl.resolve()
        mapping[relative_path.as_posix()] = digest
    return mapping


def main() -> None:
    run_build()
    expected = read_manifest()
    actual = compute_checksums()
    if expected != actual:
        missing = expected.keys() - actual.keys()
        extra = actual.keys() - expected.keys()
        mismatched = {
            name: (expected.get(name), actual.get(name))
            for name in expected.keys() & actual.keys()
            if expected[name] != actual[name]
        }
        lines = ["STL checksum drift detected:"]
        if missing:
            lines.append(f"  Missing exports: {sorted(missing)}")
        if extra:
            lines.append(f"  Unexpected exports: {sorted(extra)}")
        if mismatched:
            lines.append("  Hash mismatches:")
            for name, pair in mismatched.items():
                lines.append(f"    {name}: expected {pair[0]}, got {pair[1]}")
        raise SystemExit("\n".join(lines))

    print("[infra] STL manifest verified.")


if __name__ == "__main__":
    main()
