import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(REPO_ROOT))

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


@pytest.mark.parametrize("bullet", ["*", "+"])
def test_get_llm_endpoints_supports_alt_bullets(tmp_path, bullet):
    llms_file = tmp_path / "custom.txt"
    llms_file.write_text(
        f"## LLM Endpoints\n{bullet} [Example](https://example.com)",
        encoding="utf-8",
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


def test_get_llm_endpoints_heading_allows_closing_hashes(tmp_path):
    llms_file = tmp_path / "custom.txt"
    llms_file.write_text(
        "## LLM Endpoints ##\n- [Example](https://example.com)",
        encoding="utf-8",
    )
    endpoints = dict(llms.get_llm_endpoints(str(llms_file)))
    assert endpoints == {"Example": "https://example.com"}


def test_get_llm_endpoints_allows_indented_bullets(tmp_path):
    llms_file = tmp_path / "custom.txt"
    llms_file.write_text(
        "## LLM Endpoints\n" "  - [Example](https://example.com)",
        encoding="utf-8",
    )
    endpoints = llms.get_llm_endpoints(str(llms_file))
    assert endpoints == [("Example", "https://example.com")]


def test_get_llm_endpoints_allows_multiple_spaces_after_bullet(tmp_path):
    llms_file = tmp_path / "custom.txt"
    llms_file.write_text(
        "## LLM Endpoints\n-   [Example](https://example.com)",
        encoding="utf-8",
    )
    endpoints = llms.get_llm_endpoints(str(llms_file))
    assert endpoints == [("Example", "https://example.com")]


def test_get_llm_endpoints_allows_no_space_after_bullet(tmp_path):
    llms_file = tmp_path / "custom.txt"
    llms_file.write_text(
        "## LLM Endpoints\n-[Example](https://example.com)",
        encoding="utf-8",
    )
    endpoints = llms.get_llm_endpoints(str(llms_file))
    assert endpoints == [("Example", "https://example.com")]


def test_get_llm_endpoints_expands_env_vars(tmp_path, monkeypatch):
    llms_file = tmp_path / "custom.txt"
    llms_file.write_text(
        "## LLM Endpoints\n- [foo](https://example.com)\n", encoding="utf-8"
    )
    monkeypatch.setenv("SIGMA_LLM_DIR", str(tmp_path))
    endpoints = dict(llms.get_llm_endpoints("$SIGMA_LLM_DIR/custom.txt"))
    assert endpoints == {"foo": "https://example.com"}


def test_get_llm_endpoints_accepts_path_objects(tmp_path):
    llms_file = tmp_path / "custom.txt"
    llms_file.write_text(
        "## LLM Endpoints\n- [Example](https://example.com)",
        encoding="utf-8",
    )
    endpoints = llms.get_llm_endpoints(llms_file)
    assert endpoints == [("Example", "https://example.com")]


def test_get_llm_endpoints_stops_at_top_level_heading(tmp_path):
    llms_file = tmp_path / "custom.txt"
    llms_file.write_text(
        (
            "# Title\n"
            "## LLM Endpoints\n"
            "# Comment about the list\n"
            "- [Example](https://example.com)\n"
            "# Another Section\n"
            "- [Ignored](https://ignored.example.com)\n"
        ),
        encoding="utf-8",
    )
    endpoints = llms.get_llm_endpoints(llms_file)
    assert endpoints == [("Example", "https://example.com")]


def test_resolve_llm_endpoint_defaults_to_first_entry():
    expected = llms.get_llm_endpoints()[0]
    assert llms.resolve_llm_endpoint() == expected


def test_resolve_llm_endpoint_respects_explicit_name(tmp_path):
    llms_file = tmp_path / "custom.txt"
    llms_file.write_text(
        (
            "## LLM Endpoints\n"
            "- [Alpha](https://alpha.example.com)\n"
            "- [Beta](https://beta.example.com)\n"
        ),
        encoding="utf-8",
    )
    name, url = llms.resolve_llm_endpoint("beta", path=llms_file)
    assert name == "Beta"
    assert url == "https://beta.example.com"


def test_resolve_llm_endpoint_respects_env_variable(tmp_path, monkeypatch):
    llms_file = tmp_path / "custom.txt"
    llms_file.write_text(
        (
            "## LLM Endpoints\n"
            "- [First](https://first.example.com)\n"
            "- [Second](https://second.example.com)\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SIGMA_DEFAULT_LLM", "second")
    assert llms.resolve_llm_endpoint(path=llms_file) == (
        "Second",
        "https://second.example.com",
    )


def test_resolve_llm_endpoint_unknown_name_raises(tmp_path):
    llms_file = tmp_path / "custom.txt"
    llms_file.write_text(
        "## LLM Endpoints\n- [Alpha](https://alpha.example.com)",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Unknown LLM endpoint"):
        llms.resolve_llm_endpoint("gamma", path=llms_file)


def test_resolve_llm_endpoint_invalid_env_raises(tmp_path, monkeypatch):
    llms_file = tmp_path / "custom.txt"
    llms_file.write_text(
        "## LLM Endpoints\n- [Alpha](https://alpha.example.com)",
        encoding="utf-8",
    )
    monkeypatch.setenv("SIGMA_DEFAULT_LLM", "missing")
    with pytest.raises(RuntimeError, match="SIGMA_DEFAULT_LLM"):
        llms.resolve_llm_endpoint(path=llms_file)


def test_resolve_llm_endpoint_no_entries(tmp_path):
    llms_file = tmp_path / "custom.txt"
    llms_file.write_text("## LLM Endpoints\n", encoding="utf-8")
    with pytest.raises(
        RuntimeError,
        match="does not define any LLM endpoints",
    ):
        llms.resolve_llm_endpoint(path=llms_file)


def test_llms_cli_accepts_path_argument(tmp_path):
    llms_file = tmp_path / "custom.txt"
    llms_file.write_text(
        "## LLM Endpoints\n- [CLI](https://cli.example.com)\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-m", "llms", str(llms_file)],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = result.stdout.strip().splitlines()
    assert lines == ["CLI: https://cli.example.com"]


def test_llms_cli_expands_env_vars(tmp_path, monkeypatch):
    llms_file = tmp_path / "custom.txt"
    llms_file.write_text(
        "## LLM Endpoints\n- [Env](https://env.example.com)\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SIGMA_LLM_FILE", str(llms_file))
    result = subprocess.run(
        [sys.executable, "-m", "llms", "$SIGMA_LLM_FILE"],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = result.stdout.strip().splitlines()
    assert lines == ["Env: https://env.example.com"]


def test_llms_cli_script_runs_from_any_directory(tmp_path):
    script = REPO_ROOT / "scripts" / "llms-cli.sh"
    assert script.is_file()

    env = os.environ.copy()
    env["PYTHON_BIN"] = sys.executable

    result = subprocess.run(
        [str(script)],
        check=True,
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
    )
    lines = result.stdout.strip().splitlines()
    assert lines
    name, url = lines[0].split(": ", 1)
    assert name == "token.place"
    assert url == "https://github.com/futuroptimist/token.place"
