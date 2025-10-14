# Sigma Firmware

Sigma's firmware now lives under `apps/firmware` and is built with PlatformIO.  The
project targets the ESP32 `esp32dev` board using the Arduino framework and
mirrors the push-to-talk button onto a status LED so you can validate wiring
before enabling the full audio pipeline.

## Configuration

All hardware mappings and safety thresholds are centralized in
[`include/config.h`](include/config.h).  Update that file to adjust:

- Status LED and button pins
- Firmware metadata such as the advertised version string and serial baud rate
- Audio safety rails (recommended and absolute SPL limits)
- Microphone bias voltage guard rails
- Battery low/critical cut-offs

Sensitive credentials belong in `include/config.secrets.h`, derived from the
[`config.secrets.example.h`](include/config.secrets.example.h) template.  The real
secrets file is ignored by Git.

## Building and flashing

```bash
# From the repository root
pio run              # build the default esp32dev firmware
pio run -e native    # exercise native/unit tests
pio run --target upload  # flash connected board
```

Refer to [`docs/operations/firmware-flow.md`](../../docs/operations/firmware-flow.md)
for environment setup and flashing guidance.

## Testing

Firmware unit tests live in `test/` and use the PlatformIO Unity runner.  CI
invokes `pio test -e native` to ensure safety limits remain within spec.
