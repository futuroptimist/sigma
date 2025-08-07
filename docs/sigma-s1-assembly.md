# Sigma S1 Assembly Guide

This guide explains how to build the Sigma S1 push‑to‑talk device.
The design uses an ESP32‑WROOM module, a microphone, speaker and
an AA battery compartment housed in a 3D printed enclosure.

The case also features a small lanyard hole for attaching a strap.

See `hardware/cad/sigma-s1-enclosure.scad` for the OpenSCAD model.

## Bill of Materials

- ESP32‑WROOM module
- Electret microphone module
- Mini speaker (8 Ω)
- Push button
- 2× AA battery holder
- Miscellaneous wires and screws

## Printing the Case

1. Open `sigma-s1-enclosure.scad` in OpenSCAD.
2. Adjust the `thickness` and overall dimensions if needed.
3. Export to STL and print with 0.2 mm layer height.
   STL files are automatically generated in `hardware/stl/` by a
   GitHub Actions workflow whenever the SCAD sources change.

## Wiring Diagram

```
graph TD
    Button --> ESP32
    Mic --> ESP32
    Speaker --> ESP32
    ESP32 --> LDO
    LDO --> AA_Holder
```

The ESP32 sits in the upper section while the batteries slide into the
compartment at the bottom. Route the microphone and speaker wires through
the side openings before closing the shell.

## Assembly Steps

1. Solder the microphone and speaker leads to the ESP32.
2. Attach the push button to a GPIO pin and ground.
3. Place the ESP32 into the printed case.
4. Insert the AA holder and feed its leads to the module.
5. Close the enclosure with small screws or glue as preferred.

A future update will include a 3D viewer so you can inspect the model
right from the repository.
