#!/usr/bin/env python3
"""Lightweight diff scanner that flags obvious secrets before commit."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from typing import Iterable, List

ALLOWLIST_TOKEN = "pragma: allowlist secret"

_PATTERNS: dict[str, re.Pattern[str]] = {
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "AWS session key": re.compile(r"ASIA[0-9A-Z]{16}"),
    "GitHub token": re.compile(r"ghp_[A-Za-z0-9]{36}"),
    "GitLab token": re.compile(r"glpat-[A-Za-z0-9-_]{20,}"),
    "Slack token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    "Stripe secret key": re.compile(r"sk_(live|test)_[A-Za-z0-9]{24,}"),
    "Google API key": re.compile(r"AIza[0-9A-Za-z-_]{35}"),
    "OpenAI key": re.compile(r"sk-[A-Za-z0-9]{20,}"),
    "Private key block": re.compile(r"-----BEGIN [A-Z ]+-----"),
    "Generic secret assignment": re.compile(
        (
            r"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*"
            r"[\"']?[A-Za-z0-9\-_/+=]{12,}"
        )
    ),
}

_HIGH_ENTROPY_CANDIDATE = re.compile(r"[A-Za-z0-9+/=_-]{20,}")


@dataclass
class Finding:
    line_no: int
    rule: str
    value: str
    line: str


def _shannon_entropy(value: str) -> float:
    counts: dict[str, int] = {}
    for char in value:
        counts[char] = counts.get(char, 0) + 1
    length = len(value)
    if length == 0:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        probability = count / length
        entropy -= probability * math.log2(probability)
    return entropy


def _detect_high_entropy_values(
    text: str, *, threshold: float, min_length: int
) -> Iterable[str]:
    for match in _HIGH_ENTROPY_CANDIDATE.finditer(text):
        value = match.group(0)
        if len(value) < min_length:
            continue
        if _shannon_entropy(value) >= threshold:
            yield value


def scan_diff(
    diff_text: str,
    *,
    entropy_threshold: float = 4.0,
    min_length: int = 32,
) -> List[Finding]:
    findings: List[Finding] = []
    for idx, raw_line in enumerate(diff_text.splitlines(), start=1):
        if not raw_line.startswith("+") or raw_line.startswith("+++"):
            continue
        line = raw_line[1:]
        if ALLOWLIST_TOKEN in line:
            continue
        for rule, pattern in _PATTERNS.items():
            match = pattern.search(line)
            if match:
                findings.append(
                    Finding(
                        line_no=idx,
                        rule=rule,
                        value=match.group(0),
                        line=line.strip(),
                    )
                )
                break
        else:
            for value in _detect_high_entropy_values(
                line,
                threshold=entropy_threshold,
                min_length=min_length,
            ):
                findings.append(
                    Finding(
                        line_no=idx,
                        rule="High entropy string",
                        value=value,
                        line=line.strip(),
                    )
                )
                break
    return findings


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan a unified diff from stdin for potential secrets.",
    )
    parser.add_argument(
        "--entropy-threshold",
        type=float,
        default=4.0,
        help=(
            "Minimum Shannon entropy (bits) to flag high-entropy strings "
            "(default: 4.0)"
        ),
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=32,
        help=("Minimum length for entropy-based detection " "(default: 32)"),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as JSON for tooling integration.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    diff_text = sys.stdin.read()
    if not diff_text.strip():
        return 0

    findings = scan_diff(
        diff_text,
        entropy_threshold=args.entropy_threshold,
        min_length=args.min_length,
    )

    if not findings:
        return 0

    if args.json:
        payload = [finding.__dict__ for finding in findings]
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print("Potential secrets detected:\n")
        for finding in findings:
            print(f"- line {finding.line_no}: {finding.rule}")
            print(f"  snippet: {finding.line}")
        print(
            "\nIf this is a false positive, add 'pragma: allowlist secret' "
            "to the line or adjust the commit.",
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
