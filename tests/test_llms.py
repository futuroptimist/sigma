import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import llms  # noqa: E402


def test_get_llm_endpoints_parses_file():
    endpoints = dict(llms.get_llm_endpoints())
    assert "token.place" in endpoints
    assert endpoints["OpenRouter"] == "https://openrouter.ai/"


def test_get_llm_endpoints_skips_unrelated_sections():
    endpoints = dict(llms.get_llm_endpoints())
    assert "GitHub repo" not in endpoints
