# Sigma

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Sigma is an open-source ESP32 "AI pin" with a push-to-talk button, mic and speaker that streams audio through Whisper STT → any LLM → low-latency TTS, all inside a printable OpenSCAD case you can fork, hack and wear.

## Features
- Push-to-talk hardware using ESP32
- Whisper speech-to-text via local or remote server
- Pluggable LLM backend (token.place by default)
- Low-latency text-to-speech playback
- Parametric OpenSCAD enclosure

## Getting Started
1. Clone this repository.
2. Install [PlatformIO](https://platformio.org/) for the firmware.
3. Build the firmware inside `firmware/`:
   ```bash
   cd firmware
   pio run
   ```
4. Edit `llms.txt` to point to your preferred LLM endpoint.

See [AGENTS.md](AGENTS.md) for details on using LLM-driven tooling.

## Roadmap
- [ ] Breadboard MVP with LED and button
- [ ] Connect to LLM backend
- [ ] Integrate Whisper STT
- [ ] Add TTS playback
- [ ] Design printable push-to-talk button
- [ ] Complete OpenSCAD enclosure
- [ ] Publish build log and demo video
- [ ] Add `CONTRIBUTORS.md`

## Contributing
Pull requests are welcome. Please open an issue to discuss major changes first.

## Origin of name
No deep meaning—"Sigma" just sounded cool! If you prefer an acronym, try **Secure Interactive Gizmo Materializing AI** (S.I.G.M.A.). This project is MIT-licensed, so feel free to remix it in your own fork.
