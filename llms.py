from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

__all__ = ["get_llm_endpoints", "resolve_llm_endpoint"]


def _parse_markdown_link(text: str) -> tuple[str, str] | None:
    """Return the ``[text](url)`` tuple parsed from Markdown content."""

    open_bracket = text.find("[")
    if open_bracket == -1:
        return None
    close_bracket = text.find("]", open_bracket + 1)
    if close_bracket == -1:
        return None
    name_start = open_bracket + 1
    name = text[name_start:close_bracket]

    index = close_bracket + 1
    length = len(text)
    while index < length and text[index].isspace():
        index += 1
    if index >= length or text[index] != "(":
        return None

    index += 1
    depth = 1
    url_start = index
    while index < length:
        char = text[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                url = text[url_start:index]
                return name, url
        index += 1
    return None


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
        if not stripped or stripped[0] not in "-*+":
            continue
        content = stripped[1:].lstrip()
        link = _parse_markdown_link(content)
        if link is None:
            continue
        name, url = link
        normalized_url = url.strip()
        if not normalized_url:
            continue
        lowered = normalized_url.casefold()
        if lowered.startswith(("http://", "https://")):
            endpoints.append((name, url))
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

    env_preference_raw = os.getenv("SIGMA_DEFAULT_LLM")
    if env_preference_raw is not None:
        normalized = env_preference_raw.strip()
        if not normalized:
            raise RuntimeError(
                "Environment variable SIGMA_DEFAULT_LLM is set but empty."
            )
        candidate = lookup.get(normalized.casefold())
        if candidate is not None:
            return candidate
        available = _format_available()
        message = (
            "Environment variable SIGMA_DEFAULT_LLM is set to "
            f"{env_preference_raw!r} (normalized to {normalized!r}), but no "
            "matching endpoint was found. "
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
