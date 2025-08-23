# LLM Endpoint Guide

`llms.py` parses `llms.txt` to discover available language model endpoints.
The `llms.txt` file uses Markdown bullet lists under the `## LLM Endpoints`
heading; entries can start with `-`, `*`, or `+`.

## Listing Endpoints

Run `python -m llms` to print configured endpoints:

```bash
python -m llms
```

You can also import the helper in Python:

```python
from llms import get_llm_endpoints

for name, url in get_llm_endpoints():
    print(f"{name}: {url}")
```

The helper resolves `llms.txt` relative to its own file, so it works from
any working directory. The optional path argument expands environment
variables (e.g. `$HOME`) before resolving `~` to your home directory.
