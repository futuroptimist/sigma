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
so `## llm endpoints` also works. Closing `#` characters (even when separated by
spaces) and an optional trailing colon are ignored, so `## LLM Endpoints ##`,
`## LLM Endpoints:`, `## LLM Endpoints ##:`, or even `## LLM Endpoints ## :` are
treated the same way.
Bullet links may start with `-`, `*`, or `+`; spacing after the bullet is optional, so
`-[Example](https://example.com)` and `-   [Example](https://example.com)` both work.
URLs may include balanced parentheses in the link target and are preserved as written,
including any leading or trailing whitespace inside the parentheses.
Single-`#` comment lines are allowed before the list begins, but once endpoints appear a
new single-`#` heading ends the section the same way any `##` heading does.

`sigma.query_llm` trims surrounding whitespace from endpoint URLs before making a request, so
padded entries still resolve even though `get_llm_endpoints` preserves the original text.

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
Pass endpoint names as strings—non-string inputs raise ``TypeError`` to surface
misuse quickly.

You can list the configured endpoints with:

```bash
python -m llms
python -m llms --json  # machine-readable output
```

Plain-text listings append ``[default]`` to the entry that
``resolve_llm_endpoint`` would select so you can spot the active endpoint at a
glance.

Add `--json` to emit a machine-readable list of endpoints. Each object includes
`name`, `url`, and an `is_default` flag that mirrors the plain-text `[default]`
marker:

```bash
python -m llms --json
```

Resolve a single endpoint (respecting ``SIGMA_DEFAULT_LLM`` when set) with:

```bash
python -m llms --resolve
python -m llms --resolve --name OpenRouter
python -m llms --resolve --name OpenRouter --json  # emits {"name", "url", "is_default"}
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

Pass ``--json`` when you need machine-readable output: endpoint listings become an
array of ``{"name", "url", "is_default"}`` objects and ``--resolve`` emits a single
object with the same fields, making automation scripts easier to write.

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

### Secret scanning

Scan staged changes for accidentally committed credentials before creating a
commit:

```bash
git diff --cached | ./scripts/scan-secrets.py
```

Lines that intentionally contain tokens can opt out with
`# pragma: allowlist secret`.

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
floats, provided every number is finite. Boolean inputs raise `ValueError` so `True`/`False`
aren't silently treated as `1`/`0`.

Use `clamp` to bound a value to an inclusive range; booleans are rejected for the value and
bounds so logical flags do not masquerade as numbers:

```python
from decimal import Decimal

from sigma.utils import clamp

print(clamp(5, 0, 10))   # 5
print(clamp(15, 0, 10))  # 10
print(clamp(Decimal("1.5"), Decimal("0"), Decimal("2")))  # Decimal('1.5')
```

### Speech recognition

Sigma ships a helper for sending audio clips to a local
[`whisper.cpp`](https://github.com/ggerganov/whisper.cpp) server. The
`transcribe_audio` function accepts raw bytes, file paths, or file-like objects
and posts the clip as base64-encoded JSON to
`http://127.0.0.1:8080/inference` (override the URL to match your deployment).
The payload is encoded with Python's `base64` module so the `audio` field is a
pure ASCII string suitable for JSON APIs.
It returns a `WhisperResult` containing the decoded text, response metadata,
and an optional language hint reported by the server:

```python
from sigma import transcribe_audio

result = transcribe_audio("/tmp/clip.wav", model="base.en", language="en")
print(result.text)
print(result.language)
```

Set `temperature=` to control sampling when your deployment supports it. The helper accepts
any real number convertible to a float (for example `Decimal("0.3")`) and rejects values that
are non-numeric, boolean, `NaN`, or infinite so misconfigured requests fail fast.

Pass `extra_params={...}` to forward provider-specific arguments to the
service—any values you include are merged into the JSON body alongside the
encoded audio. String paths expand environment variables and `~`, so
`transcribe_audio("~/clips/status.wav")` reads from your home directory without
extra path handling.

Secure Whisper deployments often expect an `Authorization` header. Set
`SIGMA_WHISPER_AUTH_TOKEN` to inject one automatically; the value is trimmed
before use, and a `RuntimeError` is raised if the variable is present but
empty. Provide an optional `SIGMA_WHISPER_AUTH_SCHEME` to override the default
`Bearer` prefix (set it to an empty string to send the raw token).

### Text-to-Speech

Sigma includes a tiny formant-based synthesiser so replies can be rendered to
audio without external dependencies:

```python
from sigma import save_speech, synthesize_speech

data = synthesize_speech("Sigma online and listening.")
with open("reply.wav", "wb") as stream:
    stream.write(data)

# Convenience helper that writes the WAV file for you.
save_speech("Button pressed, recording…", "status.wav")
```

The synthesiser outputs 16-bit mono WAV data (22,050 Hz by default) and accepts
alphanumeric characters, punctuation, and whitespace. Provide a custom sample
rate via the `sample_rate` keyword when you need a different playback speed.
The helper is completely self-contained, relying only on Python's standard
library, so you can drop it into standalone scripts without extra setup.

### Querying an LLM

Use `sigma.query_llm` to send a prompt to the currently configured LLM endpoint.
The helper resolves the endpoint via `llms.resolve_llm_endpoint`, sends a JSON
payload containing the prompt, and extracts a sensible reply from common JSON
shapes (`{"response": ...}`, `{"text": ...}`, OpenAI-style chat payloads
`{"choices": [{"message": {"content": ...}}]}`, message arrays
`{"messages": [{"content": ...}]}`, streaming-style deltas
`{"choices": [{"delta": {"content": ...}}]}`, OpenAI Responses API
payloads `{"output": [{"content": ...}]}` or `{"output_text": [...]}`,
Anthropic-style collections such as `{"output": ...}` or `{"outputs": ...}`,
Cohere-style responses like `{"generations": [{"text": ...}]}`, Hugging Face
replies shaped as `[{"generated_text": ...}]` or `{"generated_text": ...}`, or
Google Gemini payloads shaped like `{"candidates": [{"content": {"parts": ...}}]}`.
Nested response objects (for example `{"response": {"choices": ...}}`) are
unwrapped automatically. When `message.content`, `delta.content`,
`output[].content`, or `output_text` contains a list of text segments (as
returned by newer OpenAI APIs) the helper concatenates the pieces automatically,
including segments whose `text` field is an object with a `value` string or a
nested `segments`/`parts` list of further fragments. Plain-text responses are
returned as-is. Bodies that look like JSON are parsed even when the server labels
them `text/plain` so malformed payloads still raise errors instead of slipping
through as text.
When a provider supplies both a base `value` and additional `segments` or
`parts`, the helper preserves the initial string and appends each nested
fragment in order so streaming responses are reconstructed without missing
tokens.

Additional response fields (such as trailing `outputs` arrays) are appended
after the reconstructed base-and-segment text so the streamed content remains
contiguous before any provider-specific extras. When providers return
top-level `outputs` collections alongside `choices`, Sigma appends those
extras after the primary completion instead of replacing it.

When both structured `output[].content` data and aggregated `output_text`
strings are present, Sigma prioritises the structured stream and appends the
aggregated text afterwards so the original generation order is preserved.

When an API leaves the aggregated `value` string empty but provides nested
`segments` or `parts`, Sigma still stitches those fragments together so the
reply is not lost.

```python
from sigma import query_llm

result = query_llm("Tell me a joke")
print(result.text)
```

Supply `extra_payload` to add provider-specific options without clobbering the
prompt; when the `prompt` argument is provided any `prompt` key in
`extra_payload` is ignored, so set `prompt=None` if you need to manage the
field yourself. Pass `name=` to target a specific endpoint:

```python
result = query_llm(
    "Summarise Sigma in one sentence.",
    name="OpenRouter",
    extra_payload={"temperature": 0.2},
)
print(result.status)  # HTTP status code
print(result.json())  # Full JSON payload when available
```

Secure endpoints such as OpenRouter or the OpenAI API often require an
`Authorization` header. Set `SIGMA_LLM_AUTH_TOKEN` to inject a bearer token into
every request. The value is trimmed before use; if the variable is present but
empty a `RuntimeError` is raised to surface misconfiguration quickly. Provide an
optional `SIGMA_LLM_AUTH_SCHEME` to override the default `Bearer` prefix (set it
to an empty string to send the raw token).

The helper raises `RuntimeError` if the endpoint does not speak HTTP(S), if a
JSON reply is malformed or empty, or if it lacks an obvious text field, making
integration failures easier to spot.

Send a prompt from the command line with the module's CLI:

```bash
python -m sigma.llm_client "Summarise Sigma in one sentence."
python -m sigma.llm_client --name OpenRouter --show-json \
    --extra '{"temperature": 0.2}' "Tell me a joke"
```

When the prompt argument is omitted the CLI reads from standard input, so you
can pipe content directly into the helper. Use `--path` to point at an
alternate `llms.txt` file and `--show-json` to display the parsed JSON payload
  alongside the extracted text. When a response omits JSON the CLI still prints
  the text reply and logs a `Warning:`-prefixed message on standard error instead of failing.

### Orchestrating a conversation

When you want to stitch Whisper, the LLM client, and text-to-speech into a
single round trip, call `sigma.conversation.run_conversation`. The helper
transcribes your audio clip, forwards the transcript (or a formatted prompt) to
the configured LLM, and returns a synthesized WAV response:

```python
from sigma.conversation import run_conversation

result = run_conversation(
    "mic-input.wav",
    whisper_model="base.en",
    llm_name="OpenRouter",
    prompt_template="Answer briefly: {transcript}",
    output_path="reply.wav",
)

print(result.transcript.text)
print(result.llm.text)
```

Set `prompt_template=None` when your `llm_extra_payload` already supplies a
structured body (such as chat `messages`), or pass an explicit `prompt` string
to override the transcript entirely. The template receives the recognised
transcript and detected language (`{transcript}` and `{language}`) so you can add
context before querying the model.

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
