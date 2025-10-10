# LLM Endpoint Guide

`llms.py` parses `llms.txt` to discover available language model endpoints.
The `llms.txt` file uses Markdown bullet lists under the `## LLM Endpoints`
heading; entries can start with `-`, `*`, or `+`. Trailing `#` characters after
the heading text (even when spaced apart) and an optional colon are ignored, so
`## LLM Endpoints ##`, `## LLM Endpoints:`, `## LLM Endpoints ##:`, or
`## LLM Endpoints ## :` are all recognised.
URLs may include balanced parentheses inside the link target; the parser keeps
them intact when returning entries, including any leading or trailing whitespace
inside the parentheses.
Comments that start with a single `#` may appear before the list, but once an
endpoint has been parsed another single-`#` heading terminates the section just
like a `##` heading.

When issuing a request, `sigma.query_llm` strips surrounding whitespace from the
resolved URL before contacting the endpoint so padded entries still work even
though the parser preserves their original formatting.

## Listing Endpoints

Run `python -m llms` to print configured endpoints:

```bash
python -m llms
python -m llms --json  # list endpoints as JSON
```

Provide `--json` to return a machine-readable list of endpoints:

```bash
python -m llms --json
```

The `scripts/llms-cli.sh` helper exports ``PYTHONPATH`` automatically so you can
invoke the CLI from any directory:

```bash
./scripts/llms-cli.sh
```

Add an optional path to load a different file. The CLI expands environment
variables and ``~`` in the same order as calling ``llms.get_llm_endpoints``:

```bash
python -m llms $HOME/custom-llms.txt
```

Resolve a single endpoint from the command line (respecting
``SIGMA_DEFAULT_LLM`` unless ``--name`` is supplied):

```bash
python -m llms --resolve
python -m llms --resolve --name OpenRouter
python -m llms --resolve --name OpenRouter --json  # returns {"name": ..., "url": ...}
```

You can also import the helper in Python:

```python
from llms import get_llm_endpoints

for name, url in get_llm_endpoints():
    print(f"{name}: {url}")
```

The helper resolves `llms.txt` relative to its own file, so it works from
any working directory. The optional path argument expands environment
variables (e.g. `$HOME`) before resolving `~` to your home directory and can
be a `str` or `pathlib.Path`.

Use ``--json`` for machine-readable output when integrating with other
tooling. Listings return an array of ``{"name", "url"}`` objects and
``--resolve`` emits a single object describing the selected endpoint.

## Selecting a Default Endpoint

Use `resolve_llm_endpoint` to choose a specific entry:

```python
from llms import resolve_llm_endpoint

name, url = resolve_llm_endpoint()  # defaults to the first configured entry
name, url = resolve_llm_endpoint("OpenRouter")  # case-insensitive lookup
```

Set the `SIGMA_DEFAULT_LLM` environment variable to change the default without
modifying code. Leading and trailing whitespace is ignored, and the resolver
raises an error if the variable is empty, references an unknown endpoint, or if
`llms.txt` does not list any entries. Explicit `name` lookups receive the same
trimming, so `resolve_llm_endpoint("  OpenRouter  ")` resolves successfully.
The `name` parameter expects a string—passing any other type raises
``TypeError`` so incorrect calls fail fast.

## Issuing a Request

The `sigma.query_llm` helper wraps `resolve_llm_endpoint` and submits a JSON
payload to the selected HTTP(S) endpoint. It accepts an optional
`extra_payload` mapping for provider-specific parameters and ignores any
`prompt` field from that mapping when the function's `prompt` argument is
present, ensuring helper callers retain control of the final prompt value. Pass
`prompt=None` to supply the field yourself when needed. The helper extracts a reply
from common response shapes (`response`, `text`, the first
`choices[].message.content`, streaming deltas in `choices[].delta.content`,
OpenAI Responses API payloads in `output[].content` or `output_text`,
Anthropic-style collections such as `output` or `outputs`, Cohere-style
responses like `generations[].text`, Hugging Face payloads in
`generated_text` arrays or objects, or Google Gemini payloads shaped like
`candidates[].content.parts`). Nested `response` objects are handled
recursively so wrappers like `{"response": {"choices": ...}}` resolve correctly.
If the message, delta, output content, or `output_text` is provided as a list of
text fragments (as in the latest OpenAI APIs) the helper concatenates the segments for you,
including cases where each fragment stores its text inside an object with a
`value` string or a nested `segments`/`parts` array. Plain-text responses are
returned unchanged, and a `RuntimeError` is raised if a JSON response cannot be
interpreted.
When providers send both a base `value` and additional `segments` or `parts`,
the helper preserves the base text and appends the nested fragments in order so
streaming completions remain intact.

When providers omit the aggregated `value` string but include `segments` or
`parts`, the helper still combines those fragments so the final reply surfaces
correctly.

Most hosted providers also expect an `Authorization` header. Configure
`SIGMA_LLM_AUTH_TOKEN` with your API key to add one automatically. The helper
normalises the token by stripping whitespace and raises a `RuntimeError` if the
variable is set but empty. Use `SIGMA_LLM_AUTH_SCHEME` to customise the prefix
(`Bearer` by default, set it to an empty string to send the raw token).

## Command-line Queries

Invoke the helper directly from the command line to send a prompt without
writing Python code:

~~~bash
python -m sigma.llm_client "Summarise Sigma"
python -m sigma.llm_client --name OpenRouter --extra '{"temperature": 0.2}' \
    --show-json "Tell me a joke"
~~~

The CLI reads the prompt from standard input when no positional argument is
supplied, making it easy to pipe prompts into the tool:

~~~bash
echo "How windy is it today?" | python -m sigma.llm_client --path ~/custom-llms.txt
~~~

Use `--path` to target a different `llms.txt` file and `--show-json` to print
the parsed JSON payload alongside the extracted text response. When the
response lacks JSON the CLI still prints the text reply and writes a
`Warning:`-prefixed message to standard error. Provider-specific options can be
supplied via `--extra` as a JSON object string.
