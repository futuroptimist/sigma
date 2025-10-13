import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from sigma.llm_client import LLMResponse, query_llm  # noqa: E402


class _RecordingHandler(BaseHTTPRequestHandler):
    responses: List[Tuple[int, Dict[str, str], bytes]] = []
    requests: List[Dict[str, Any]] = []

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler naming
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        type(self).requests.append(
            {
                "path": self.path,
                "body": body,
                "headers": {k.lower(): v for k, v in self.headers.items()},
            }
        )
        if type(self).responses:
            status, headers, payload = type(self).responses.pop(0)
        else:
            status, headers, payload = 500, {"Content-Type": "text/plain"}, b""
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_args: Any, **_kwargs: Any) -> None:
        return  # pragma: no cover


@pytest.fixture
def llm_test_server() -> Tuple[str, type[_RecordingHandler]]:
    handler = _RecordingHandler
    handler.responses = []
    handler.requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}", handler
    finally:
        server.shutdown()
        thread.join()


def _write_llms_file(tmp_path: Path, url: str) -> Path:
    llms_file = tmp_path / "llms.txt"
    llms_file.write_text(
        f"## LLM Endpoints\n- [Local]({url})\n",
        encoding="utf-8",
    )
    return llms_file


def _latest_request(handler: type[_RecordingHandler]) -> Dict[str, Any]:
    assert handler.requests, "no request captured"
    return handler.requests[-1]


def test_query_llm_returns_response_field(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"response": "Hello"}).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Hi there", path=llms_file)

    assert isinstance(result, LLMResponse)
    assert result.text == "Hello"
    request_payload = _latest_request(handler)["body"].decode("utf-8")
    payload = json.loads(request_payload)
    assert payload == {"prompt": "Hi there"}


def test_query_llm_handles_openai_message(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "choices": [
                        {"message": {"content": "Sigma rocks!"}},
                        {"message": {"content": "Ignored"}},
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Explain Sigma", path=llms_file)

    assert result.text == "Sigma rocks!"


def test_query_llm_prefers_choices_over_messages(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "choices": [
                        {"message": {"content": "From choices"}},
                    ],
                    "messages": [
                        {"role": "user", "content": "User question"},
                        {"role": "assistant", "content": "From messages"},
                    ],
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Explain Sigma", path=llms_file)

    assert result.text == "From choices"


def test_query_llm_handles_openai_content_list(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": [
                                    {"type": "text", "text": "Hello"},
                                    {"type": "text", "text": " world"},
                                ]
                            }
                        }
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Segmented", path=llms_file)

    assert result.text == "Hello world"


def test_query_llm_filters_non_assistant_messages(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "messages": [
                        {"role": "system", "content": "You are helpful"},
                        {"role": "user", "content": "Hi"},
                        {"role": "assistant", "content": "Hello"},
                        {
                            "role": "assistant",
                            "content": [
                                {"type": "text", "text": " there"},
                                {"type": "text", "text": "!"},
                            ],
                        },
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Hello?", path=llms_file)

    assert result.text == "Hello there!"


def test_query_llm_handles_openai_content_value_objects(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": [
                                    {
                                        "type": "output_text",
                                        "text": {"value": "Hello"},
                                    },
                                    {
                                        "type": "output_text",
                                        "text": {"value": " world"},
                                    },
                                ]
                            }
                        }
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Responses API", path=llms_file)

    assert result.text == "Hello world"


def test_query_llm_combines_value_and_segments(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    segments = [
        {"text": " "},
        {
            "text": {
                "value": "world",
            }
        },
    ]
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": [
                                    {
                                        "type": "output_text",
                                        "text": {
                                            "value": "Hello",
                                            "segments": segments,
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Segmented value", path=llms_file)

    assert result.text == "Hello world"


def test_query_llm_appends_segments_before_trailing_fields(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": [
                                    {
                                        "type": "output_text",
                                        "text": {
                                            "segments": [
                                                {"text": " world"},
                                            ],
                                            "value": "Hello",
                                            "outputs": [
                                                {"text": "!"},
                                            ],
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Segment ordering", path=llms_file)

    assert result.text == "Hello world!"


def test_query_llm_keeps_extras_after_value_even_if_listed_first(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": [
                                    {
                                        "type": "output_text",
                                        "text": {
                                            "outputs": [
                                                {"text": "!"},
                                            ],
                                            "value": "Hello",
                                            "segments": [
                                                {"text": " world"},
                                            ],
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Segment ordering", path=llms_file)

    assert result.text == "Hello world!"


def test_query_llm_keeps_extras_after_value_without_segments(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": [
                                    {
                                        "type": "output_text",
                                        "text": {
                                            "outputs": [
                                                {"text": "!"},
                                            ],
                                            "value": "Hello",
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Segment ordering", path=llms_file)

    assert result.text == "Hello!"


def test_query_llm_keeps_extras_after_text_without_value(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": [
                                    {
                                        "type": "output_text",
                                        "text": {
                                            "outputs": [
                                                {"text": "!"},
                                            ],
                                            "text": "Hello",
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Segment ordering", path=llms_file)

    assert result.text == "Hello!"


def test_query_llm_combines_choices_with_top_level_outputs(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "choices": [
                        {"message": {"content": "Primary"}},
                    ],
                    "outputs": [
                        {"text": " extra"},
                    ],
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Combine", path=llms_file)

    assert result.text == "Primary extra"


def test_query_llm_combines_value_and_parts(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    nested_parts = [
        {"text": " "},
        {
            "text": {
                "value": "world",
            }
        },
    ]
    parts = [{"text": nested_parts}]
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": [
                                    {
                                        "type": "output_text",
                                        "text": {
                                            "value": "Hello",
                                            "parts": parts,
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Parts value", path=llms_file)

    assert result.text == "Hello world"


def test_query_llm_handles_responses_api_output(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "output": [
                        {
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": {"value": "Hello"},
                                },
                                {
                                    "type": "output_text",
                                    "text": {"value": " world"},
                                },
                            ]
                        }
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Responses API output", path=llms_file)

    assert result.text == "Hello world"


def test_query_llm_handles_responses_output_text(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"output_text": ["Hello", " world"]}).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Responses API text", path=llms_file)

    assert result.text == "Hello world"


def test_query_llm_prefers_structured_output_before_output_text(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "output": [
                        {
                            "content": [
                                {
                                    "text": {
                                        "value": "Hello",
                                        "segments": [
                                            {"text": " world"},
                                        ],
                                    }
                                }
                            ]
                        }
                    ],
                    "output_text": ["!"],
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Responses API mixed", path=llms_file)

    assert result.text == "Hello world!"


def test_query_llm_handles_openai_delta_segments(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "choices": [
                        {
                            "delta": {
                                "content": [
                                    {"type": "text", "text": "Hello"},
                                    {"type": "text", "text": " world"},
                                ]
                            }
                        }
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Streaming", path=llms_file)

    assert result.text == "Hello world"


def test_query_llm_concatenates_multiple_delta_choices(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "choices": [
                        {"delta": {"content": "Hello"}},
                        {"delta": {"content": " world"}},
                        {
                            "delta": {
                                "content": [
                                    {"type": "text", "text": "!"},
                                ]
                            }
                        },
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Streaming events", path=llms_file)

    assert result.text == "Hello world!"


def test_query_llm_handles_delta_value_segments(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    """Test concatenating nested 'segments' inside delta content values."""
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "choices": [
                        {
                            "delta": {
                                "content": [
                                    {
                                        "type": "output_text",
                                        "text": {
                                            "value": {
                                                "segments": [
                                                    {"text": "Hello"},
                                                ]
                                            }
                                        },
                                    },
                                    {
                                        "type": "output_text",
                                        "text": {
                                            "value": {
                                                "segments": [
                                                    {"text": " world"},
                                                ]
                                            }
                                        },
                                    },
                                ]
                            }
                        }
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Nested segments", path=llms_file)

    assert result.text == "Hello world"


def test_query_llm_handles_nested_response_payload(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    """Test that nested 'response' wrappers are automatically unwrapped."""
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "response": {
                        "choices": [
                            {
                                "message": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": {"value": "Nested"},
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Nested response", path=llms_file)

    assert result.text == "Nested"


def test_query_llm_handles_output_collection(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    """Test that query_llm parses OpenAI-style 'output[].content' arrays."""
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "output": [
                        {
                            "content": [
                                {
                                    "type": "text",
                                    "text": {"value": "Hello"},
                                },
                                {
                                    "type": "text",
                                    "text": {"value": " world"},
                                },
                            ]
                        }
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Output", path=llms_file)

    assert result.text == "Hello world"


def test_query_llm_handles_outputs_array(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    """Test that query_llm supports Anthropic-style 'outputs' arrays."""
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "outputs": [
                        {
                            "content": [
                                {"type": "text", "text": "Segment A"},
                                {"type": "text", "text": " & Segment B"},
                            ]
                        }
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Outputs", path=llms_file)

    assert result.text == "Segment A & Segment B"


def test_query_llm_handles_gemini_candidates_parts(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    """Test parsing Gemini-style candidates with parts arrays."""
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "candidates": [
                        {
                            "content": {
                                "role": "model",
                                "parts": [
                                    {"text": "Hello"},
                                    {"text": " Gemini"},
                                ],
                            }
                        }
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Gemini", path=llms_file)

    assert result.text == "Hello Gemini"


def test_query_llm_handles_gemini_candidates_content_list(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    """Test Gemini candidates where content is a list of messages."""
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "candidates": [
                        {
                            "content": [
                                {
                                    "role": "model",
                                    "parts": [
                                        {"text": "Hello"},
                                        {
                                            "text": {
                                                "value": {
                                                    "segments": [
                                                        {
                                                            "text": " world",
                                                        },
                                                    ]
                                                }
                                            }
                                        },
                                    ],
                                }
                            ]
                        }
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Gemini list", path=llms_file)

    assert result.text == "Hello world"


def test_query_llm_handles_messages_content(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    """Test parsing `messages[].content` arrays from multi-part responses."""
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "messages": [
                        {
                            "role": "assistant",
                            "content": [
                                {"type": "text", "text": "Hello"},
                                {
                                    "type": "text",
                                    "text": {"value": " world"},
                                },
                            ],
                        }
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Messages", path=llms_file)

    assert result.text == "Hello world"


def test_query_llm_handles_generations_payload(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    """Test parsing Cohere-style `generations[].text` arrays."""
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "generations": [
                        {"text": "Hello"},
                        {"text": " world"},
                    ]
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Cohere", path=llms_file)

    assert result.text == "Hello world"


def test_query_llm_handles_generated_text_list(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    """Test parsing Hugging Face-style `generated_text` lists."""
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                [
                    {"generated_text": "Hello"},
                    {"generated_text": " world"},
                ]
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("HuggingFace", path=llms_file)

    assert result.text == "Hello world"


def test_query_llm_handles_generated_text_string(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    """Test parsing single `generated_text` strings."""
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"generated_text": "Standalone"}).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("HF string", path=llms_file)

    assert result.text == "Standalone"


def test_query_llm_handles_nested_response_messages(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    """Test parsing nested `response.messages[].content` arrays."""
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(
                {
                    "response": {
                        "messages": [
                            {
                                "role": "assistant",
                                "content": [
                                    {
                                        "type": "output_text",
                                        "text": {
                                            "value": {
                                                "segments": [
                                                    {"text": "Nested"},
                                                    {
                                                        "text": {
                                                            "value": " reply",
                                                        }
                                                    },
                                                ]
                                            }
                                        },
                                    }
                                ],
                            }
                        ]
                    }
                }
            ).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Nested messages", path=llms_file)

    assert result.text == "Nested reply"


def test_query_llm_handles_plain_text(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    """Test that plain-text responses are returned unchanged."""
    base_url, handler = llm_test_server
    handler.responses.append(
        (200, {"Content-Type": "text/plain"}, b"plain text response")
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Plain please", path=llms_file)

    assert result.text == "plain text response"
    with pytest.raises(ValueError):
        result.json()


def test_query_llm_trims_whitespace_from_url(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"text": "ok"}).encode("utf-8"),
        )
    )
    llms_file = tmp_path / "llms.txt"
    llms_file.write_text(
        f"## LLM Endpoints\n- [Local](   {base_url}   )\n",
        encoding="utf-8",
    )

    result = query_llm("Whitespace", path=llms_file)

    assert result.text == "ok"
    assert result.url == base_url
    assert handler.requests, "no request captured"


def test_query_llm_extra_payload_included(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"text": "ack"}).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    query_llm(
        "Use extra payload",
        path=llms_file,
        extra_payload={"temperature": 0.3, "stream": False},
    )

    request_payload = _latest_request(handler)["body"].decode("utf-8")
    payload = json.loads(request_payload)
    assert payload == {
        "prompt": "Use extra payload",
        "temperature": 0.3,
        "stream": False,
    }


def test_query_llm_includes_authorisation_header(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"text": "ok"}).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    monkeypatch.setenv("SIGMA_LLM_AUTH_TOKEN", "secret-token")

    query_llm("Auth please", path=llms_file)

    headers = _latest_request(handler)["headers"]
    assert headers.get("authorization") == "Bearer secret-token"


def test_query_llm_customises_authorisation_scheme(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"text": "ack"}).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    monkeypatch.setenv("SIGMA_LLM_AUTH_TOKEN", "abc123")
    monkeypatch.setenv("SIGMA_LLM_AUTH_SCHEME", "ApiKey")

    query_llm("Custom scheme", path=llms_file)
    headers = _latest_request(handler)["headers"]
    assert headers.get("authorization") == "ApiKey abc123"

    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"text": "ack"}).encode("utf-8"),
        )
    )
    monkeypatch.setenv("SIGMA_LLM_AUTH_SCHEME", "   ")

    query_llm("No scheme", path=llms_file)
    headers = _latest_request(handler)["headers"]
    assert headers.get("authorization") == "abc123"


def test_query_llm_rejects_empty_prompt(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, _handler = llm_test_server
    llms_file = _write_llms_file(tmp_path, base_url)
    with pytest.raises(ValueError):
        query_llm("   ", path=llms_file)


def test_query_llm_extra_payload_prompt_ignored(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"text": "ok"}).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    query_llm(
        "Hello",
        path=llms_file,
        extra_payload={"prompt": "Override"},
    )

    request_payload = _latest_request(handler)["body"].decode("utf-8")
    payload = json.loads(request_payload)
    assert payload["prompt"] == "Hello"


def test_query_llm_supports_messages_only_payload(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"text": "ok"}).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    query_llm(
        None,
        path=llms_file,
        extra_payload={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Hi"}],
        },
    )

    request_body = _latest_request(handler)["body"].decode("utf-8")
    payload = json.loads(request_body)
    assert "prompt" not in payload
    assert payload["messages"][0]["content"] == "Hi"


def test_query_llm_uses_payload_prompt_when_argument_missing(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"text": "ok"}).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    query_llm(
        None,
        path=llms_file,
        extra_payload={"prompt": "Payload prompt"},
    )

    request_payload = _latest_request(handler)["body"].decode("utf-8")
    payload = json.loads(request_payload)
    assert payload["prompt"] == "Payload prompt"


def test_query_llm_rejects_empty_payload(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, _handler = llm_test_server
    llms_file = _write_llms_file(tmp_path, base_url)

    with pytest.raises(ValueError):
        query_llm(None, path=llms_file)


def test_query_llm_empty_authorisation_token_raises(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_url, _handler = llm_test_server
    llms_file = _write_llms_file(tmp_path, base_url)

    monkeypatch.setenv("SIGMA_LLM_AUTH_TOKEN", "   ")

    with pytest.raises(RuntimeError, match="SIGMA_LLM_AUTH_TOKEN"):
        query_llm("hello", path=llms_file)


def test_query_llm_requires_http_scheme(tmp_path: Path) -> None:
    llms_file = tmp_path / "llms.txt"
    llms_file.write_text(
        "## LLM Endpoints\n- [Invalid](ws://example.com)\n", encoding="utf-8"
    )
    with pytest.raises(RuntimeError):
        query_llm("hello", path=llms_file)


def test_query_llm_errors_on_unparseable_json(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"unexpected": "format"}).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    with pytest.raises(
        RuntimeError,
        match="without a recognised text field",
    ):
        query_llm("testing", path=llms_file)


def test_query_llm_errors_on_invalid_json(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            b"{invalid",
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    with pytest.raises(RuntimeError, match="invalid JSON"):
        query_llm("Hello?", path=llms_file)


def test_query_llm_errors_on_json_like_text_response(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "text/plain"},
            b"{invalid",
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    with pytest.raises(RuntimeError, match="invalid JSON"):
        query_llm("Hello?", path=llms_file)


def test_query_llm_errors_on_empty_json(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            b"",
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    with pytest.raises(RuntimeError, match="empty JSON response"):
        query_llm("Hello?", path=llms_file)


def test_query_llm_handles_choices_text(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"choices": [{"text": "Choice text"}]}).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = query_llm("Pick a choice", path=llms_file)

    assert result.text == "Choice text"


def test_query_llm_http_error(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            503,
            {"Content-Type": "text/plain"},
            b"Service unavailable",
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    with pytest.raises(RuntimeError, match="HTTP status 503"):
        query_llm("Are you there?", path=llms_file)


def test_llm_client_cli_basic(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"text": "CLI reply"}).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "sigma.llm_client",
            "Hello from CLI",
            "--path",
            str(llms_file),
            "--show-json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    lines = result.stdout.splitlines()
    stdout_lines = [line for line in lines if line.strip()]
    assert stdout_lines[0] == "CLI reply"
    parsed_json = json.loads("\n".join(stdout_lines[1:]))
    assert parsed_json == {"text": "CLI reply"}

    latest = json.loads(_latest_request(handler)["body"].decode("utf-8"))
    assert latest["prompt"] == "Hello from CLI"


def test_llm_client_cli_show_json_without_payload(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "text/plain"},
            b"Plain CLI reply",
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "sigma.llm_client",
            "Plain please",
            "--path",
            str(llms_file),
            "--show-json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "Plain CLI reply"
    assert "Warning: Unable to display JSON payload" in result.stderr


def test_llm_client_cli_show_json_empty_body_warns(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "text/plain"},
            b"",
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "sigma.llm_client",
            "Empty please",
            "--path",
            str(llms_file),
            "--show-json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == ""
    assert "Warning: No JSON payload available." in result.stderr


def test_llm_client_cli_reads_stdin(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"text": "Read stdin"}).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "sigma.llm_client",
            "--path",
            str(llms_file),
        ],
        input="Prompt from stdin\n",
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == "Read stdin"
    latest = json.loads(_latest_request(handler)["body"].decode("utf-8"))
    assert latest["prompt"] == "Prompt from stdin"


def test_llm_client_cli_invalid_extra(
    tmp_path: Path,
    llm_test_server: Tuple[str, type[_RecordingHandler]],
) -> None:
    base_url, handler = llm_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"text": "ignored"}).encode("utf-8"),
        )
    )
    llms_file = _write_llms_file(tmp_path, base_url)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "sigma.llm_client",
            "Hello",
            "--path",
            str(llms_file),
            "--extra",
            "not-json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "Failed to parse --extra JSON" in result.stderr
