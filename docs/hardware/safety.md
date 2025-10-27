# Safety guidance

Sigma devices are intended for safe, prolonged daily use.  Follow these guard
rails when assembling and operating hardware.

## Headset sound pressure level (SPL)

- Target 75–80 dB SPL for normal listening sessions.
- Never exceed 85 dB SPL for more than 8 continuous hours (OSHA guidance).
- Hard-stop firmware and amplifier gains below 94 dB SPL to prevent hearing
  damage during fault conditions.
- Document your print's acoustic damping materials and verify output with an SPL
  meter if you modify the enclosure volume.

The firmware prints these reminders on boot and the configuration header exposes
`kRecommendedMaxSplDb` and `kAbsoluteMaxSplDb` constants for quick tuning. The
serial boot banner pulls the SPL and battery thresholds directly from
`config.h`, so adjusting `kAbsoluteMaxSplDb`, `kBatteryLowVolts`, or
`kBatteryCriticalVolts` automatically updates the warnings without editing the
source.

Automated tests compare these documented limits against
`apps/firmware/include/config.h`, so update both when thresholds change.

## Microphone biasing

- Electret capsules typically expect 2.0–3.0 V bias.
- The reference design supplies 2.5 V through a 2.2 kΩ resistor.
- Stay within the firmware-defined limits of 1.8–3.3 V to avoid damaging the
  capsule.
- Add RC filtering at the bias node to keep Whisper transcriptions clean.

## Battery and charging

- Use protected 3.7 V Li-ion cells with an onboard PCM.
- Terminate discharge at 3.3 V and cut off completely by 3.0 V.
- Charge at 0.5 C and keep the enclosure vented while charging.
- Incorporate a thermal fuse or monitor pack temperature if deploying in hot
  environments.

CI blocks merges unless documentation, firmware safety checks, and STL manifests
are kept in sync with these thresholds.
