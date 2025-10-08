from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "scan-secrets.py"
TOKENS = {
    "stripe": (
        "sk_test_",
        "abcdefghijklmnopqrstuvwxyz123",
    ),  # pragma: allowlist secret
    "aws": (
        "AKIA",
        "0123456789ABCDEF",
    ),  # pragma: allowlist secret
    "github": (
        "ghp_",
        "abcdefghijklmnopqrstuvwxyz0123456789",  # pragma: allowlist secret
    ),
    "slack": (
        "xoxb-",
        "1234567890-ABCDEFGHIJ",
    ),  # pragma: allowlist secret
}
STRIPE_TEST_KEY = "".join(TOKENS["stripe"])
AWS_ACCESS_KEY = "".join(TOKENS["aws"])
GITHUB_TOKEN = "".join(TOKENS["github"])
SLACK_TOKEN = "".join(TOKENS["slack"])
PASSWORD_DIFF_LINE = "".join(
    ['+password = "SuperSecretValue123"']  # pragma: allowlist secret
)


def run_scan(diff: str, *extra_args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *extra_args],
        input=diff,
        text=True,
        capture_output=True,
    )


def build_diff(lines: list[str]) -> str:
    return "\n".join(lines) + "\n"


def test_scan_secrets_allows_clean_diff():
    diff = build_diff(
        [
            "diff --git a/file b/file",
            "+++ b/file",
            "@@",
            "+print('hello world')",
        ]
    )
    result = run_scan(diff)
    assert result.returncode == 0
    assert not result.stdout
    assert not result.stderr


def test_scan_secrets_detects_pattern():
    diff = build_diff(
        [
            "diff --git a/file b/file",
            "+++ b/file",
            "@@",
            f'+api_key = "{STRIPE_TEST_KEY}"',
        ]
    )
    result = run_scan(diff)
    assert result.returncode == 1
    assert "Stripe secret key" in result.stdout


@pytest.mark.parametrize(
    "token",
    [AWS_ACCESS_KEY, GITHUB_TOKEN, SLACK_TOKEN],
)
def test_scan_secrets_flags_known_tokens(token: str):
    diff = build_diff(
        [
            "diff --git a/file b/file",
            "+++ b/file",
            "@@",
            f"+value = '{token}'",
        ]
    )
    result = run_scan(diff)
    assert result.returncode == 1
    assert token in result.stdout


def test_scan_secrets_supports_allowlist_comment():
    diff = build_diff(
        [
            "diff --git a/file b/file",
            "+++ b/file",
            "@@",
            " ".join(
                [
                    f"+token = '{SLACK_TOKEN}'",
                    "# pragma: allowlist secret",
                ]
            ),
        ]
    )
    result = run_scan(diff)
    assert result.returncode == 0


def test_scan_secrets_outputs_json_payload():
    diff = build_diff(
        [
            "diff --git a/file b/file",
            "+++ b/file",
            "@@",
            PASSWORD_DIFF_LINE,
        ]
    )
    result = run_scan(diff, "--json")
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload[0]["rule"] == "Generic secret assignment"
    assert payload[0]["value"]
