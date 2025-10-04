from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

__all__ = ["get_llm_endpoints", "resolve_llm_endpoint"]


def get_llm_endpoints(path: str | Path | None = None) -> List[Tuple[str, str]]:
    """Return LLM endpoints listed in ``llms.txt``."""

    if path is None:
        llms_path = Path(__file__).with_name("llms.txt")
    else:
        raw_path = os.fspath(path)
        llms_path = Path(os.path.expandvars(raw_path)).expanduser()
    try:
        lines = llms_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return []

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


def resolve_llm_endpoint(
    name: str | None = None,
    *,
    path: str | Path | None = None,
) -> Tuple[str, str]:
    """Return a single LLM endpoint according to preference rules."""

    endpoints = get_llm_endpoints(path)
    if not endpoints:
        raise RuntimeError("llms.txt does not define any LLM endpoints")

    lookup: Dict[str, Tuple[str, str]] = {
        display.casefold(): (display, url) for display, url in endpoints
    }

    def _format_available() -> str:
        return ", ".join(display for display, _ in endpoints)

    if name is not None:
        candidate = lookup.get(name.casefold())
        if candidate is not None:
            return candidate
        available = _format_available()
        message = " ".join(
            [
                f"Unknown LLM endpoint '{name}'.",
                f"Available endpoints: {available}",
            ]
        )
        raise ValueError(message)

    env_preference = os.getenv("SIGMA_DEFAULT_LLM")
    if env_preference:
        candidate = lookup.get(env_preference.casefold())
        if candidate is not None:
            return candidate
        available = _format_available()
        message = (
            "Environment variable SIGMA_DEFAULT_LLM is set to "
            f"{env_preference!r}, but no matching endpoint was found. "
            f"Available endpoints: {available}"
        )
        raise RuntimeError(message)

    return endpoints[0]


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
