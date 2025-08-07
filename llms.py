from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple


def get_llm_endpoints(path: str | Path = "llms.txt") -> List[Tuple[str, str]]:
    """Return LLM endpoints listed in ``llms.txt``.

    Parameters
    ----------
    path: str | Path
        Path to the ``llms.txt`` file.

    Returns
    -------
    List[Tuple[str, str]]
        List of ``(name, url)`` tuples for each configured endpoint.

    Notes
    -----
    If the file does not exist an empty list is returned instead of raising
    ``FileNotFoundError``.
    """

    llms_path = Path(path)
    try:
        lines = llms_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return []

    pattern = re.compile(r"^- \[(?P<name>[^\]]+)\]\((?P<url>https?://[^)]+)\)")
    endpoints: List[Tuple[str, str]] = []
    for line in lines:
        match = pattern.match(line.strip())
        if match:
            endpoints.append((match.group("name"), match.group("url")))
    return endpoints


if __name__ == "__main__":
    for name, url in get_llm_endpoints():
        print(f"{name}: {url}")
