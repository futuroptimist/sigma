# Sigma Agents Guide

This file helps AI agents like OpenAI Codex understand the structure and workflows of the
**Sigma** project. Sigma is a fully open-source ESP32 "AI pin" that uses Whisper for speech
recognition, routes text to a configurable LLM, and replies with text-to-speech.

## Project Structure
- `/firmware` – PlatformIO project for the ESP32
- `/hardware/cad` – OpenSCAD models for the enclosure
- `/hardware/stl` – generated STL files committed by CI
- `/scripts` – helper scripts and CI checks
- `/tests` – pytest suite verifying basic functionality

## Coding Conventions
- Python code is formatted with **black**, **isort**, and **flake8** (run via `pre-commit`)
- Keep prompt templates short with a **purpose**, **context**, and **request** section
- Document new conversation endpoints in [llms.txt](llms.txt)

## LLM Workflow
1. **Speech‑to‑Text** – Audio is streamed to a `whisper.cpp` service
2. **Conversation** – Transcripts are sent to an LLM endpoint from `llms.txt` (default is [token.place](https://github.com/futuroptimist/token.place); alternatives include [OpenRouter](https://openrouter.ai/), [OpenAI API](https://platform.openai.com/), [Ollama](https://ollama.ai/), or a local [llama.cpp](https://github.com/ggerganov/llama.cpp) instance)
3. **Text‑to‑Speech** – Responses are synthesized and played back on the device

## Testing Requirements
Run all checks before committing:

```bash
pre-commit run --all-files
make test
```

## Pull Request Guidelines
1. Provide a concise description of your changes
2. Reference any related issues
3. Ensure `pre-commit` and tests pass
4. Keep PRs focused on a single concern

## Programmatic Checks
`scripts/checks.sh` runs `flake8`, `isort`, `black`, and `pytest`. CI mirrors these checks so they must pass locally first.

## CAD Exports
Generate updated STL files with:

```bash
bash scripts/build_stl.sh
```

Refer to the [README](README.md) for installation steps and the project roadmap.
