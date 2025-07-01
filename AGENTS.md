# AGENTS

This file documents how LLMs and other AI agents are used within the **sigma** project.

Sigma is a hardware and firmware stack for an ESP32 "AI pin" that relays
voice through Whisper-based speech recognition, routes the text to a
configurable LLM, and plays replies back with text‑to‑speech.

## LLM Workflows

1. **Speech‑to‑Text**
   - Audio from the ESP32 is streamed to a `whisper.cpp` service.
2. **Conversation Engine**
   - The transcribed text is sent to an LLM endpoint listed in `llms.txt`.
   - The default endpoint is `token.place`, but you may use local or cloud providers.
3. **Text‑to‑Speech**
   - The LLM response is synthesized to audio and returned to the device.

## Adding or Updating Agents

- Document new endpoints in `llms.txt`.
- Keep prompt templates short with a **purpose**, **context**, and
  **request** section.
- If you add helper scripts or CLI flags, describe them here so future
  contributors can reproduce your workflow.

## Repo Layout

- `firmware/` – PlatformIO project for the ESP32.
- `enclosure/` – OpenSCAD files for the enclosure.
- `software/` – Python helpers for STT/TTS and LLM calls.

Refer to the [README](README.md) for installation steps and the project roadmap.
