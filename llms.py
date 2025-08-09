from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple


def get_llm_endpoints(path: str | Path | None = None) -> List[Tuple[str, str]]:
    """Return LLM endpoints listed in ``llms.txt``.

    Parameters
    ----------
    path: str | Path | None, optional
        Optional path to ``llms.txt``. ``~`` expands to the user home
        directory. Defaults to the copy beside this module.

    Returns
    -------
    List[Tuple[str, str]]
        List of ``(name, url)`` tuples for each configured endpoint.

    Notes
    -----
    Only bullet links within the ``## LLM Endpoints`` section are parsed. If
    the file does not exist an empty list is returned instead of raising
    ``FileNotFoundError``.
    """

    if path is None:
        llms_path = Path(__file__).with_name("llms.txt")
    else:
        llms_path = Path(path).expanduser()
    try:
        lines = llms_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return []

    # Only parse bullet links in the "## LLM Endpoints" section.
    pattern = re.compile(r"^- \[(?P<name>[^\]]+)\]\((?P<url>https?://[^)]+)\)")
    endpoints: List[Tuple[str, str]] = []
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("##"):
            in_section = stripped == "## LLM Endpoints"
            continue
        if not in_section:
            continue
        match = pattern.match(stripped)
        if match:
            endpoints.append((match.group("name"), match.group("url")))
    return endpoints


if __name__ == "__main__":
    for name, url in get_llm_endpoints():
        print(f"{name}: {url}")
