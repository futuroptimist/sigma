from configparser import ConfigParser
from pathlib import Path

FIRMWARE_DIR = Path("apps/firmware")
PLATFORMIO_PATH = FIRMWARE_DIR / "platformio.ini"
MAIN_CPP_PATH = FIRMWARE_DIR / "src" / "main.cpp"
MISSING_PLATFORMIO = "platformio.ini missing from apps/firmware"
MISSING_MAIN_CPP = "src/main.cpp missing from apps/firmware project"


def test_platformio_ini_defines_esp32_env():
    assert PLATFORMIO_PATH.is_file(), MISSING_PLATFORMIO
    parser = ConfigParser()
    parser.read(PLATFORMIO_PATH)
    assert "env" in parser
    shared = parser["env"]
    shared_flags = shared.get("build_flags", fallback="")
    assert "-Iinclude" in shared_flags
    assert "env:esp32dev" in parser
    esp32 = parser["env:esp32dev"]
    assert esp32.get("platform") == "espressif32"
    assert esp32.get("framework") == "arduino"
    assert esp32.get("board") == "esp32dev"
    assert esp32.get("monitor_speed") == "115200"
    assert "env:native" in parser
    native = parser["env:native"]
    assert native.get("platform") == "native"


def test_main_cpp_configures_button_and_led():
    assert MAIN_CPP_PATH.is_file(), MISSING_MAIN_CPP
    text = MAIN_CPP_PATH.read_text(encoding="utf-8")
    required_tokens = [
        '#include "config.h"',
        "sigma::config::kStatusLedPin",
        "sigma::config::kButtonPin",
        "sigma::config::kFirmwareVersion",
        "report_safety_callouts",
    ]
    for token in required_tokens:
        assert token in text
    assert "[safety] Maintain SPL under" in text
