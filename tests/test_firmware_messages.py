"""Firmware messaging regression tests."""

from __future__ import annotations

from pathlib import Path

FIRMWARE_SOURCE = Path("apps/firmware/src/main.cpp")


def _extract_function_body(text: str, signature: str) -> str:
    """Return the body of the function matching *signature*."""

    start = text.find(signature)
    assert start != -1, f"{signature} missing from {FIRMWARE_SOURCE}"
    brace_index = text.find("{", start)
    assert brace_index != -1, f"Opening brace missing for {signature}"
    depth = 0
    for index in range(brace_index, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                start_index = brace_index + 1
                end_index = index
                return text[start_index:end_index]
    raise AssertionError(f"Closing brace missing for {signature}")


def test_report_safety_callouts_uses_config_thresholds() -> None:
    """Ensure boot messages stay aligned with configuration constants."""

    source = FIRMWARE_SOURCE.read_text(encoding="utf-8")
    body = _extract_function_body(source, "void report_safety_callouts()")
    assert "kAbsoluteMaxSplDb" in body
    assert "kBatteryCriticalVolts" in body
