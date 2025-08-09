import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import llms  # noqa: E402


def test_get_llm_endpoints_parses_file():
    endpoints = dict(llms.get_llm_endpoints())
    assert "token.place" in endpoints
    assert endpoints["OpenRouter"] == "https://openrouter.ai/"


def test_get_llm_endpoints_missing_file_returns_empty_list(tmp_path):
    missing_file = tmp_path / "missing.txt"
    endpoints = llms.get_llm_endpoints(str(missing_file))
    assert endpoints == []


def test_get_llm_endpoints_works_from_any_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    endpoints = dict(llms.get_llm_endpoints())
    assert "token.place" in endpoints


def test_get_llm_endpoints_allows_uppercase_scheme(tmp_path):
    test_file = tmp_path / "upper.txt"
    test_file.write_text("- [UPPER](HTTPS://example.com)")
    endpoints = dict(llms.get_llm_endpoints(str(test_file)))
    assert endpoints["UPPER"] == "HTTPS://example.com"
