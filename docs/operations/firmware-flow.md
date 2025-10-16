# Firmware workflow

1. Install PlatformIO Core (`pip install platformio`).
2. Configure hardware pins and safety thresholds in
   [`apps/firmware/include/config.h`](../../apps/firmware/include/config.h).
3. Optional: copy `config.secrets.example.h` to `config.secrets.h` for Wi-Fi and
   API credentials.  Keep the real file untracked.
4. Build and test (either run the commands from `apps/firmware/` or pass `-d apps/firmware`):

```bash
pio run -d apps/firmware             # builds ESP32 firmware
pio test -d apps/firmware -e native  # runs Unity safety/unit tests
```

5. Flash hardware with `pio run -d apps/firmware --target upload`.
6. Monitor serial output with `pio device monitor --baud 115200` to confirm the
   safety callouts fire on boot.

Additional host-side dependencies are tracked via `.env.example` and
[`docs/operations/secrets.md`](secrets.md).
