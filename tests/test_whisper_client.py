from __future__ import annotations

import base64
import io
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Iterator, Tuple

import pytest

from sigma.whisper_client import WhisperResult, transcribe_audio


class _RecordingHandler(BaseHTTPRequestHandler):
    responses: list[Tuple[int, Dict[str, str], bytes]] = []
    requests: list[Dict[str, Any]] = []

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
            status, headers, payload = (
                200,
                {"Content-Type": "application/json"},
                b"{}",
            )
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_args: Any, **_kwargs: Any) -> None:
        return  # pragma: no cover


ServerFixture = Tuple[str, type[_RecordingHandler]]


@pytest.fixture
def whisper_test_server() -> Iterator[ServerFixture]:
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


def _latest_request(handler: type[_RecordingHandler]) -> Dict[str, Any]:
    assert handler.requests, "no request captured"
    return handler.requests[-1]


def test_transcribe_audio_with_bytes(
    whisper_test_server: ServerFixture,
) -> None:
    base_url, handler = whisper_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"text": "hello", "language": "en"}).encode("utf-8"),
        )
    )

    result = transcribe_audio(
        b"\x01\x02",
        url=f"{base_url}/inference",
        model="base.en",
        language="en",
        temperature=0.0,
    )

    assert isinstance(result, WhisperResult)
    assert result.text == "hello"
    assert result.language == "en"

    latest = _latest_request(handler)
    request_payload = json.loads(latest["body"].decode("utf-8"))
    assert request_payload["model"] == "base.en"
    assert request_payload["language"] == "en"
    assert request_payload["temperature"] == 0.0
    assert base64.b64decode(request_payload["audio"]) == b"\x01\x02"


def test_transcribe_audio_accepts_path(
    tmp_path: Path, whisper_test_server: ServerFixture
) -> None:
    base_url, handler = whisper_test_server
    segments_payload = {"segments": [{"text": "Hello "}, {"text": "world"}]}
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps(segments_payload).encode("utf-8"),
        )
    )

    audio_path = tmp_path / "clip.raw"
    audio_path.write_bytes(b"audio-bytes")

    result = transcribe_audio(audio_path, url=f"{base_url}/inference")

    assert result.text == "Hello world"

    latest = _latest_request(handler)
    payload = json.loads(latest["body"].decode("utf-8"))
    assert base64.b64decode(payload["audio"]) == b"audio-bytes"


def test_transcribe_audio_expands_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    whisper_test_server: ServerFixture,
) -> None:
    base_url, handler = whisper_test_server
    handler.responses.extend(
        [
            (
                200,
                {"Content-Type": "application/json"},
                json.dumps({"text": "first"}).encode("utf-8"),
            ),
            (
                200,
                {"Content-Type": "application/json"},
                json.dumps({"text": "second"}).encode("utf-8"),
            ),
        ]
    )

    audio_path = tmp_path / "clip.raw"
    audio_path.write_bytes(b"bytes")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("SIGMA_AUDIO_DIR", str(tmp_path))

    first = transcribe_audio(
        "~/clip.raw",
        url=f"{base_url}/inference",
    )
    second = transcribe_audio(
        "$SIGMA_AUDIO_DIR/clip.raw",
        url=f"{base_url}/inference",
    )

    assert first.text == "first"
    assert second.text == "second"

    assert len(handler.requests) == 2
    payload_one = json.loads(handler.requests[0]["body"].decode("utf-8"))
    payload_two = json.loads(handler.requests[1]["body"].decode("utf-8"))
    assert base64.b64decode(payload_one["audio"]) == b"bytes"
    assert base64.b64decode(payload_two["audio"]) == b"bytes"


def test_transcribe_audio_accepts_file_object(
    whisper_test_server: ServerFixture,
) -> None:
    base_url, handler = whisper_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "text/plain"},
            b"transcribed text",
        )
    )

    buffer = io.BytesIO(b"streamed-bytes")
    result = transcribe_audio(buffer, url=f"{base_url}/inference")

    assert result.text == "transcribed text"
    latest = _latest_request(handler)
    payload = json.loads(latest["body"].decode("utf-8"))
    assert base64.b64decode(payload["audio"]) == b"streamed-bytes"


def test_transcribe_audio_requires_transcript(
    whisper_test_server: ServerFixture,
) -> None:
    base_url, handler = whisper_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"detail": "no transcript"}).encode("utf-8"),
        )
    )

    with pytest.raises(RuntimeError, match="did not include a transcription"):
        transcribe_audio(b"abc", url=f"{base_url}/inference")


def test_transcribe_audio_rejects_empty_audio() -> None:
    with pytest.raises(ValueError, match="audio payload must be non-empty"):
        transcribe_audio(b"")


def test_transcribe_audio_rejects_invalid_audio_type() -> None:
    with pytest.raises(TypeError, match="audio must be bytes"):
        transcribe_audio(123)  # type: ignore[arg-type]


def test_transcribe_audio_http_error(
    whisper_test_server: ServerFixture,
) -> None:
    base_url, handler = whisper_test_server
    handler.responses.append(
        (
            400,
            {"Content-Type": "text/plain"},
            b"bad request",
        )
    )

    with pytest.raises(RuntimeError, match="HTTP status 400"):
        transcribe_audio(b"bytes", url=f"{base_url}/inference")
