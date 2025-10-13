from __future__ import annotations

import argparse
import json
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


def _normalize_heading_title(raw: str) -> str:
    """Return a normalized heading title without trailing markers."""

    title = raw.strip()
    while title.endswith(("#", ":")):
        title = title[:-1].rstrip()
    return " ".join(title.split())


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
                title = _normalize_heading_title(heading.group(2))
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
        if not isinstance(name, str):
            raise TypeError("Endpoint name must be a string")
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Endpoint name must be a non-empty string")

        candidate = lookup.get(normalized_name.casefold())
        if candidate is not None:
            return candidate
        available = _format_available()
        if normalized_name == name:
            detail = f"Unknown LLM endpoint '{name}'."
        else:
            detail = "".join(
                [
                    "Unknown LLM endpoint ",
                    f"{name!r} (normalized to {normalized_name!r}).",
                ]
            )
        message = " ".join([detail, f"Available endpoints: {available}"])
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
        description="List or resolve configured LLM endpoints from llms.txt.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        help=(
            "Optional path to llms.txt. Defaults to the copy shipped with the "
            "module."
        ),
    )
    parser.add_argument(
        "-r",
        "--resolve",
        action="store_true",
        help=(
            "Resolve a single endpoint instead of listing all endpoints. The "
            "selection honours SIGMA_DEFAULT_LLM unless --name is provided."
        ),
    )
    parser.add_argument(
        "-n",
        "--name",
        help=(
            "Explicit endpoint name to resolve (case-insensitive). Implies "
            "--resolve."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help=(
            "Emit machine-readable JSON instead of formatted text. Listing "
            "produces an array; resolution yields a single object with "
            "name/url/is_default fields."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point for ``python -m llms``."""

    args = sys.argv[1:] if argv is None else argv
    namespace = _parse_args(args)
    if namespace.name and not namespace.resolve:
        namespace.resolve = True

    if namespace.resolve:
        try:
            name, url = resolve_llm_endpoint(
                namespace.name,
                path=namespace.path,
            )
        except (RuntimeError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        is_default = False
        try:
            default_candidate = resolve_llm_endpoint(path=namespace.path)
        except RuntimeError:
            default_candidate = None
        else:
            default_name, default_url = default_candidate
            is_default = (name, url) == (default_name, default_url)
        if namespace.json:
            payload = {
                "name": name,
                "url": url,
                "is_default": is_default,
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            suffix = " [default]" if is_default else ""
            print(f"{name}: {url}{suffix}")
        return 0

    endpoints = get_llm_endpoints(namespace.path)
    default_entry: tuple[str, str] | None = None
    if endpoints:
        try:
            default_entry = resolve_llm_endpoint(path=namespace.path)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    if namespace.json:
        payload = []
        for name, url in endpoints:
            is_default = False
            if default_entry is not None:
                is_default = (name, url) == default_entry
            entry = {
                "name": name,
                "url": url,
                "is_default": is_default,
            }
            payload.append(entry)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for name, url in endpoints:
            suffix = ""
            if default_entry is not None and (name, url) == default_entry:
                suffix = " [default]"
            print(f"{name}: {url}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
