from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


def get_llm_endpoints(path: str | Path | None = None) -> List[Tuple[str, str]]:
    """Return LLM endpoints listed in ``llms.txt``.

    Parameters
    ----------
    path: str | Path | None, optional
        Optional path to ``llms.txt``. Environment variables like ``$HOME``
        are expanded, then ``~`` expands to the user home directory.
        Defaults to the copy beside this module.

    Returns
    -------
    List[Tuple[str, str]]
        List of ``(name, url)`` tuples for each configured endpoint.

    Notes
    -----
    Only bullet links starting with ``-``, ``*``, or ``+`` within the
    ``## LLM Endpoints`` section are parsed. Any amount of whitespace may
    follow the bullet before the link. The section heading is matched
    case-insensitively, and optional trailing ``#`` characters are ignored
    so ``## LLM Endpoints ##`` is treated the same as ``## LLM Endpoints``.
    URL schemes are also matched case-insensitively so ``HTTPS`` and
    ``https`` are treated the same. If the file does not exist an empty list
    is returned instead of raising ``FileNotFoundError``.
    """

    if path is None:
        llms_path = Path(__file__).with_name("llms.txt")
    else:
        raw_path = os.fspath(path)
        llms_path = Path(os.path.expandvars(raw_path)).expanduser()
    try:
        lines = llms_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return []

    # Only parse bullet links in the "## LLM Endpoints" section.
    pattern = re.compile(
        r"^[-*+]\s*\[(?P<name>[^\]]+)\]\((?P<url>https?://[^)]+)\)",
        re.IGNORECASE,
    )
    endpoints: List[Tuple[str, str]] = []
    in_section = False
    section_has_entry = False
    heading_pattern = re.compile(r"^(#+)\s*(.*?)\s*#*\s*$")
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") and not stripped.startswith("##"):
            if in_section and section_has_entry:
                in_section = False
                section_has_entry = False
            continue
        heading = heading_pattern.match(stripped)
        if heading:
            level = len(heading.group(1))
            if level <= 2:
                title = heading.group(2).strip()
                in_section = title.casefold() == "llm endpoints"
                section_has_entry = False
            continue
        if not in_section:
            continue
        match = pattern.match(stripped)
        if match:
            endpoints.append((match.group("name"), match.group("url")))
            section_has_entry = True
    return endpoints


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Return parsed CLI arguments for the ``llms`` helper."""

    parser = argparse.ArgumentParser(
        prog="python -m llms",
        description="List configured LLM endpoints from llms.txt.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        help=(
            "Optional path to llms.txt. Defaults to the copy shipped with the "
            "module."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point for ``python -m llms``."""

    args = sys.argv[1:] if argv is None else argv
    namespace = _parse_args(args)
    for name, url in get_llm_endpoints(namespace.path):
        print(f"{name}: {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
