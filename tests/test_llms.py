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


def test_get_llm_endpoints_handles_uppercase_scheme(tmp_path):
    llms_file = tmp_path / "custom.txt"
    llms_file.write_text(
        "## LLM Endpoints\n- [Example](HTTPS://example.com)", encoding="utf-8"
    )
    endpoints = llms.get_llm_endpoints(str(llms_file))
    assert endpoints == [("Example", "HTTPS://example.com")]


def test_get_llm_endpoints_ignores_optional_section():
    endpoints = dict(llms.get_llm_endpoints())
    assert "GitHub repo" not in endpoints


def test_get_llm_endpoints_expands_user_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    path = tmp_path / "custom.txt"
    path.write_text(
        "## LLM Endpoints\n- [foo](https://example.com)\n",
        encoding="utf-8",
    )
    endpoints = dict(llms.get_llm_endpoints("~/custom.txt"))
    assert endpoints == {"foo": "https://example.com"}


def test_get_llm_endpoints_supports_star_bullets(tmp_path):
    llms_file = tmp_path / "custom.txt"
    llms_file.write_text(
        "## LLM Endpoints\n* [Example](https://example.com)", encoding="utf-8"
    )
    endpoints = llms.get_llm_endpoints(str(llms_file))
    assert endpoints == [("Example", "https://example.com")]


def test_get_llm_endpoints_heading_case_insensitive(tmp_path):
    llms_file = tmp_path / "custom.txt"
    llms_file.write_text(
        "## llm endpoints\n- [Example](https://example.com)", encoding="utf-8"
    )
    endpoints = dict(llms.get_llm_endpoints(str(llms_file)))
    assert "Example" in endpoints


def test_get_llm_endpoints_allows_indented_bullets(tmp_path):
    llms_file = tmp_path / "custom.txt"
    llms_file.write_text(
        "## LLM Endpoints\n" "  - [Example](https://example.com)",
        encoding="utf-8",
    )
    endpoints = llms.get_llm_endpoints(str(llms_file))
    assert endpoints == [("Example", "https://example.com")]
