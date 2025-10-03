# Sigma Firmware

This PlatformIO project targets the ESP32 `esp32dev` board using the Arduino
framework. It mirrors the push-to-talk button onto a status LED so you can
validate the hardware wiring before integrating speech features.

- `SIGMA_BUTTON_PIN` (default `GPIO0`) is configured as an `INPUT_PULLUP`.
- `SIGMA_STATUS_LED` (default `GPIO2`) is driven `HIGH` when the button is held.
- `SIGMA_FIRMWARE_VERSION` prints on boot along with button state transitions.

Build the firmware from this directory with:

```bash
pio run
```

Flash the resulting binary with `pio run --target upload` once your board is
connected.
