from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple


def get_llm_endpoints(path: str = "llms.txt") -> List[Tuple[str, str]]:
    """Return LLM endpoints listed in ``llms.txt``.

    Parameters
    ----------
    path: str
        Path to the ``llms.txt`` file.

    Returns
    -------
    List[Tuple[str, str]]
        List of ``(name, url)`` tuples for each configured endpoint.
        Only links under the "## LLM Endpoints" section are considered.
    """

    lines = Path(path).read_text(encoding="utf-8").splitlines()
    pattern = re.compile(r"^- \[(?P<name>[^\]]+)\]\((?P<url>https?://[^)]+)\)")
    endpoints: List[Tuple[str, str]] = []
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = stripped == "## LLM Endpoints"
            continue
        if in_section:
            match = pattern.match(stripped)
            if match:
                endpoints.append((match.group("name"), match.group("url")))
    return endpoints


if __name__ == "__main__":
    for name, url in get_llm_endpoints():
        print(f"{name}: {url}")
