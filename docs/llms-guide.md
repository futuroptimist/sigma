# LLM Endpoint Guide

`llms.py` parses `llms.txt` to discover available language model endpoints.
The `llms.txt` file uses Markdown bullet lists under the `## LLM Endpoints`
heading; entries can start with `-`, `*`, or `+`. Trailing `#` characters after
the heading text are ignored, so `## LLM Endpoints ##` is also recognised.
URLs may include balanced parentheses inside the link target; the parser keeps
them intact when returning entries.
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
`llms.txt` does not list any entries.
