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
The primary OpenSCAD file exposes a `thickness` parameter so you can tweak the
wall thickness before exporting a print.
Regenerate STLs locally with:

```bash
bash scripts/build_stl.sh
```

Preview the enclosure in 3D by serving the repo locally (for example,
`python -m http.server`) and opening
[`docs/sigma-s1-viewer.html`](docs/sigma-s1-viewer.html) in a browser.

Assembly instructions live in [`docs/sigma-s1-assembly.md`](docs/sigma-s1-assembly.md).

## Getting Started

1. Install [PlatformIO](https://platformio.org/).
2. Clone this repository.
3. Build the firmware:

```bash
cd firmware
pio run
```

4. Install [uv](https://github.com/astral-sh/uv) and set up pre-commit hooks:
```bash
curl -Ls https://astral.sh/uv/install.sh | sh
uv venv
uv pip install pre-commit
pre-commit install
```

Helper scripts live in [`scripts/`](scripts/) and LLM helpers in [`llms.py`](llms.py).
Use the `llms.py` helper to manage language model endpoints.
Configure LLM endpoints in [`llms.txt`](llms.txt), which the [`llms.py`](llms.py) helper parses.
The parser matches the `## LLM Endpoints` heading case-insensitively,
so `## llm endpoints` also works. Closing `#` characters are ignored,
so `## LLM Endpoints ##` is treated the same way.
Bullet links may start with `-`, `*`, or `+`; spacing after the bullet is optional, so
`-[Example](https://example.com)` and `-   [Example](https://example.com)` both work.
URLs may include balanced parentheses in the link target and are preserved as written,
including any leading or trailing whitespace inside the parentheses.
Single-`#` comment lines are allowed before the list begins, but once endpoints appear a
new single-`#` heading ends the section the same way any `##` heading does.

Select a specific endpoint with `resolve_llm_endpoint`:

```python
from llms import resolve_llm_endpoint

name, url = resolve_llm_endpoint()  # first entry by default
name, url = resolve_llm_endpoint("OpenRouter")  # case-insensitive lookup
```

Set the `SIGMA_DEFAULT_LLM` environment variable to override the default without
changing code; surrounding whitespace is ignored, and the resolver raises an error if the
variable is empty or references an unknown entry. Direct lookups via the `name` argument
receive the same whitespace trimming so `resolve_llm_endpoint("  OpenRouter  ")` succeeds.

You can list the configured endpoints with:

```bash
python -m llms
```

Resolve a single endpoint (respecting ``SIGMA_DEFAULT_LLM`` when set) with:

```bash
python -m llms --resolve
python -m llms --resolve --name OpenRouter
```

When you're working outside the repository root, use the helper script which
bootstraps ``PYTHONPATH`` before calling the module:

```bash
./scripts/llms-cli.sh
```

Provide an optional path to load a different file. Environment variables and
``~`` are expanded just like when calling ``get_llm_endpoints`` from Python:

```bash
python -m llms ~/custom-llms.txt
```

If `llms.txt` is missing the command prints nothing and exits without error. The helper
locates `llms.txt` relative to its own file, so you can run it from any working
directory. The optional path argument to ``llms.get_llm_endpoints`` expands environment
variables (e.g. ``$HOME``) before resolving ``~`` to the user's home, and accepts either
string paths or ``pathlib.Path`` objects.

## Firmware

The [`firmware/`](firmware) directory contains a PlatformIO project targeting the
`esp32dev` board with the Arduino framework. By default the build flags expose
three macros:

- `SIGMA_FIRMWARE_VERSION` – firmware version string printed on boot.
- `SIGMA_STATUS_LED` – GPIO driving the status LED (defaults to `GPIO2`).
- `SIGMA_BUTTON_PIN` – GPIO assigned to the push-to-talk button (defaults to `GPIO0`).

When flashed to an ESP32 the firmware mirrors the button state to the status LED
and reports transitions over the serial console at 115200 baud. Adjust the GPIO
mappings by overriding the macros via PlatformIO's `build_flags` if your
hardware layout differs.

See [`AGENTS.md`](AGENTS.md) for details on how we integrate LLMs and prompts.

## Testing

Run pre-commit hooks and the test suite before committing:

```bash
pre-commit run --all-files
make test
```

Playwright powers the end-to-end coverage for the enclosure viewer. Install its
runtime once before running the tests locally:

```bash
uv pip install playwright pytest-playwright
python -m playwright install --with-deps chromium
```

If those system dependencies are missing the Playwright-based viewer test skips automatically
and prints a reminder to run `playwright install-deps`.

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

Both `average_percentile` and `percentile_rank` accept any iterable, so generators work too.
The helpers handle `decimal.Decimal` and `fractions.Fraction` values in addition to ints and
floats, provided every number is finite.

Use `clamp` to bound a value to an inclusive range:

```python
from decimal import Decimal

from sigma.utils import clamp

print(clamp(5, 0, 10))   # 5
print(clamp(15, 0, 10))  # 10
print(clamp(Decimal("1.5"), Decimal("0"), Decimal("2")))  # Decimal('1.5')
```

### Querying an LLM

Use `sigma.query_llm` to send a prompt to the currently configured LLM endpoint.
The helper resolves the endpoint via `llms.resolve_llm_endpoint`, sends a JSON
payload containing the prompt, and extracts a sensible reply from common JSON
shapes (`{"response": ...}`, `{"text": ...}`, or OpenAI-style
`{"choices": [{"message": {"content": ...}}]}`). Plain-text responses are
returned as-is.

```python
from sigma import query_llm

result = query_llm("Tell me a joke")
print(result.text)
```

Supply `extra_payload` to add provider-specific options without clobbering the
prompt, and pass `name=` to target a specific endpoint:

```python
result = query_llm(
    "Summarise Sigma in one sentence.",
    name="OpenRouter",
    extra_payload={"temperature": 0.2},
)
print(result.status)  # HTTP status code
print(result.json())  # Full JSON payload when available
```

The helper raises `RuntimeError` if the endpoint does not speak HTTP(S) or if a
JSON reply lacks an obvious text field, making integration failures easier to
spot.

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
