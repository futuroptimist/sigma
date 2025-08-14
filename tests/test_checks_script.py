from pathlib import Path


def test_checks_script_uses_strict_mode():
    script = Path("scripts/checks.sh")
    content = script.read_text(encoding="utf-8").splitlines()
    assert any(line.strip() == "set -euo pipefail" for line in content)


def test_checks_script_uses_python3():
    script = Path("scripts/checks.sh")
    text = script.read_text(encoding="utf-8")
    assert "python3 -m flake8" in text
