"""Ensure safety documentation stays aligned with firmware thresholds."""

from __future__ import annotations

import re
from pathlib import Path

CONFIG_PATH = Path("apps/firmware/include/config.h")
SAFETY_DOC_PATH = Path("docs/hardware/safety.md")

CONSTANT_SPECS: dict[str, dict[str, str]] = {
    "kRecommendedMaxSplDb": {"format": "{:.0f}", "suffix": " dB"},
    "kAbsoluteMaxSplDb": {"format": "{:.0f}", "suffix": " dB"},
    "kMicBiasMinVolts": {"format": "{:.1f}", "suffix": "\u2013"},
    "kMicBiasMaxVolts": {"format": "{:.1f}", "suffix": " V"},
    "kBatteryLowVolts": {"format": "{:.1f}", "suffix": " V"},
    "kBatteryCriticalVolts": {"format": "{:.1f}", "suffix": " V"},
}


def _parse_config_constants() -> dict[str, float]:
    """Return float constants defined in ``config.h``."""

    pattern_parts = [
        r"constexpr\s+float\s+(k[A-Za-z0-9_]+)\s*=",
        r"\s*([0-9]+(?:\.[0-9]+)?)f\s*;",
    ]
    pattern = re.compile("".join(pattern_parts))
    text = CONFIG_PATH.read_text(encoding="utf-8")
    return {name: float(value) for name, value in pattern.findall(text)}


def test_safety_doc_matches_firmware_thresholds() -> None:
    """Documented safety limits must match the firmware configuration."""

    config_values = _parse_config_constants()
    doc_text = SAFETY_DOC_PATH.read_text(encoding="utf-8")

    for constant, spec in CONSTANT_SPECS.items():
        missing_message = f"{constant} missing from {CONFIG_PATH}"
        assert constant in config_values, missing_message
        fmt = spec["format"]
        suffix = spec["suffix"]
        formatted_value = fmt.format(config_values[constant])
        expected_snippet = f"{formatted_value}{suffix}"
        message = (
            f"{expected_snippet} derived from {constant} missing "
            f"in {SAFETY_DOC_PATH}"
        )
        assert expected_snippet in doc_text, message
