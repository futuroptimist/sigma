from configparser import ConfigParser
from pathlib import Path

FIRMWARE_DIR = Path("firmware")
PLATFORMIO_PATH = FIRMWARE_DIR / "platformio.ini"
MAIN_CPP_PATH = FIRMWARE_DIR / "src" / "main.cpp"
MISSING_PLATFORMIO = "platformio.ini missing from firmware/"
MISSING_MAIN_CPP = "src/main.cpp missing from firmware project"


def test_platformio_ini_defines_esp32_env():
    assert PLATFORMIO_PATH.is_file(), MISSING_PLATFORMIO
    parser = ConfigParser()
    parser.read(PLATFORMIO_PATH)
    assert "env:esp32dev" in parser
    env = parser["env:esp32dev"]
    assert env.get("platform") == "espressif32"
    assert env.get("framework") == "arduino"
    assert env.get("board") == "esp32dev"
    assert env.get("monitor_speed") == "115200"
    build_flags = env.get("build_flags", "")
    for macro in (
        "SIGMA_FIRMWARE_VERSION",
        "SIGMA_STATUS_LED",
        "SIGMA_BUTTON_PIN",
    ):
        assert macro in build_flags


def test_main_cpp_configures_button_and_led():
    assert MAIN_CPP_PATH.is_file(), MISSING_MAIN_CPP
    text = MAIN_CPP_PATH.read_text(encoding="utf-8")
    required_tokens = [
        "pinMode(SIGMA_STATUS_LED, OUTPUT)",
        "pinMode(SIGMA_BUTTON_PIN, INPUT_PULLUP)",
        "digitalRead(SIGMA_BUTTON_PIN)",
        "digitalWrite(SIGMA_STATUS_LED",
    ]
    for token in required_tokens:
        assert token in text
    assert 'Serial.print("Button state: ")' in text
