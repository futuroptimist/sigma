# sigma

[![Lint & Format](https://img.shields.io/github/actions/workflow/status/futuroptimist/sigma/.github/workflows/01-lint-format.yml?label=lint%20%26%20format)](https://github.com/futuroptimist/sigma/actions/workflows/01-lint-format.yml)
[![Tests](https://img.shields.io/github/actions/workflow/status/futuroptimist/sigma/.github/workflows/02-tests.yml?label=tests)](https://github.com/futuroptimist/sigma/actions/workflows/02-tests.yml)
[![Coverage](https://codecov.io/gh/futuroptimist/sigma/branch/main/graph/badge.svg)](https://codecov.io/gh/futuroptimist/sigma)
[![Docs](https://img.shields.io/github/actions/workflow/status/futuroptimist/sigma/.github/workflows/03-docs.yml?label=docs)](https://github.com/futuroptimist/sigma/actions/workflows/03-docs.yml)
[![License](https://img.shields.io/github/license/futuroptimist/sigma)](LICENSE)

Sigma is an open-source ESP32 "AI pin" that lets you talk to a language model via a push‑to‑talk button. Audio is captured and sent to Whisper for speech recognition, routed through the LLM of your choice, then played back with low‑latency text‑to‑speech in a 3D‑printed OpenSCAD case.

Hardware models for the enclosure live in [`hardware/cad`](hardware/cad) with
STL exports in [`hardware/stl`](hardware/stl). A GitHub Actions workflow
automatically regenerates the STL files whenever the SCAD sources change.
Assembly instructions live in [`docs/sigma-s1-assembly.md`](docs/sigma-s1-assembly.md).

## Getting Started

1. Install [PlatformIO](https://platformio.org/).
2. Clone this repository.
3. Build the firmware:

```bash
pio run
```

4. Install [uv](https://github.com/astral-sh/uv) and set up pre-commit hooks:
```bash
curl -Ls https://astral.sh/uv/install.sh | sh
uv venv
uv pip install pre-commit
pre-commit install
```

Helper scripts for STT, TTS and the LLM API live in `software/`.
Configure the endpoint you want to use in [`llms.txt`](llms.txt).
The parser matches the `## LLM Endpoints` heading case-insensitively,
so `## llm endpoints` also works.

You can list the configured endpoints with:

```bash
python -m llms
```

If `llms.txt` is missing the command prints nothing and exits without error. The helper
locates `llms.txt` relative to its own file, so you can run it from any working
directory. The optional path argument to ``llms.get_llm_endpoints`` expands environment
variables (e.g. ``$HOME``) before resolving ``~`` to the user's home.

See [`AGENTS.md`](AGENTS.md) for details on how we integrate LLMs and prompts.

## Testing

Run the test suite with Make:

```bash
make test
```

## Utilities

Helper functions live in the `sigma` package. For example, `average_percentile`
returns the mean percentile rank of a sequence:

```python
from sigma.utils import average_percentile

values = [1, 2, 3]
print(average_percentile(values))  # 50.0
```

The percentile rank of a single value is available via `percentile_rank`:

```python
from sigma.utils import percentile_rank

print(percentile_rank(2, [1, 2, 3]))  # 50.0
```

## Roadmap

- [ ] Breadboard MVP with a button toggling an LED
- [ ] Hook up LLM
- [ ] Voice input via [whisper.cpp](https://github.com/ggerganov/whisper.cpp)
- [ ] Voice output via an open source TTS
- [ ] 3D print enclosure for push-to-talk button
- [ ] 3D print enclosure for the microcontroller
- [ ] Blog post
- [ ] Demo video
- [x] CONTRIBUTING.md
- [ ] Modular magnetic connectors for accessories (NFC-based detection)
- [ ] Detachable compute unit for local LLM inference
- [ ] Robotic carrier platform (quadruped → flying → biped)

## Contributing

Pull requests are welcome! Please open an issue first to discuss major changes. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. By contributing you agree to license your work under the MIT license.

## Origin of the Name

"Sigma" just sounds cool. If you prefer an acronym, call it **Secure Interactive Gizmo Materializing AI (S.I.G.M.A.)**. Feel free to rebrand it in your own fork.

## Values

We aim for a positive-sum, empathetic community. Sigma follows regenerative and open-source principles so knowledge flows back into every project.

## Related Projects

- [flywheel](https://github.com/futuroptimist/flywheel) – GitHub template powering this repo
- [Axel](https://github.com/futuroptimist/axel) – personal LLM accelerator
- [Gabriel](https://github.com/futuroptimist/gabriel) – security-focused LLM companion
- [token.place](https://github.com/futuroptimist/token.place) – stateless faucet for LLM inference
