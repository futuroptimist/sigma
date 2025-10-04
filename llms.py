from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

__all__ = ["get_llm_endpoints", "resolve_llm_endpoint"]


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


def resolve_llm_endpoint(
    name: str | None = None,
    *,
    path: str | Path | None = None,
) -> Tuple[str, str]:
    """Return a single LLM endpoint according to preference rules.

    Parameters
    ----------
    name:
        Optional display name of the endpoint to resolve. The lookup is
        case-insensitive and raises :class:`ValueError` if no match exists.
    path:
        Optional override path for ``llms.txt``. Mirrors
        :func:`get_llm_endpoints` and supports environment variables and
        ``~`` expansion.

    Returns
    -------
    Tuple[str, str]
        ``(name, url)`` pair for the resolved endpoint.

    Notes
    -----
    The resolver checks for an explicit ``name`` first. If omitted, it then
    honours the ``SIGMA_DEFAULT_LLM`` environment variable before falling back
    to the first configured endpoint. ``RuntimeError`` is raised when no
    endpoints are configured or when ``SIGMA_DEFAULT_LLM`` references an
    unknown endpoint.
    """

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


if __name__ == "__main__":
    for name, url in get_llm_endpoints():
        print(f"{name}: {url}")
