# LLM Endpoint Guide

`llms.py` parses `llms.txt` to discover available language model endpoints.
The `llms.txt` file uses Markdown bullet lists under the `## LLM Endpoints`
heading; entries can start with `-`, `*`, or `+`. Trailing `#` characters after
the heading text and an optional colon are ignored, so `## LLM Endpoints ##`
and `## LLM Endpoints:` are both recognised.
URLs may include balanced parentheses inside the link target; the parser keeps
them intact when returning entries, including any leading or trailing whitespace
inside the parentheses.
Comments that start with a single `#` may appear before the list, but once an
endpoint has been parsed another single-`#` heading terminates the section just
like a `##` heading.

## Listing Endpoints

Run `python -m llms` to print configured endpoints:

```bash
python -m llms
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

## Issuing a Request

The `sigma.query_llm` helper wraps `resolve_llm_endpoint` and submits a JSON
payload to the selected HTTP(S) endpoint. It accepts an optional
`extra_payload` mapping for provider-specific parameters and extracts a reply
from common response shapes (`response`, `text`, or the first
`choices[].message.content`). If the message content is provided as a list of
text fragments (as in the latest OpenAI APIs) the helper concatenates the
segments for you. Plain-text responses are returned unchanged, and a
`RuntimeError` is raised if a JSON response cannot be interpreted.
