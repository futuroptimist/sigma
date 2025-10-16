from __future__ import annotations

import base64
import io
import json
import math
import threading
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Iterator, Tuple

import pytest

from sigma import whisper_client

WhisperResult = whisper_client.WhisperResult
WhisperSpeechToText = whisper_client.WhisperSpeechToText
transcribe_audio = whisper_client.transcribe_audio

_TEMPERATURE_ERROR = "temperature must be a finite number"


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
    audio_payload = request_payload["audio"]
    assert isinstance(audio_payload, str)
    assert audio_payload.isascii()
    assert base64.b64decode(audio_payload) == b"\x01\x02"


def test_transcribe_audio_coerces_numeric_temperature(
    whisper_test_server: ServerFixture,
) -> None:
    base_url, handler = whisper_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"text": "ok"}).encode("utf-8"),
        )
    )

    transcribe_audio(
        b"\x01",
        url=f"{base_url}/inference",
        temperature=Decimal("0.25"),
    )

    latest = _latest_request(handler)
    payload = json.loads(latest["body"].decode("utf-8"))
    assert math.isclose(
        payload["temperature"],
        0.25,
        rel_tol=1e-9,
    )


def test_transcribe_audio_rejects_non_numeric_temperature() -> None:
    with pytest.raises(TypeError, match=_TEMPERATURE_ERROR):
        transcribe_audio(b"\x01", temperature="warm")


def test_transcribe_audio_rejects_boolean_temperature() -> None:
    with pytest.raises(TypeError, match=_TEMPERATURE_ERROR):
        transcribe_audio(b"\x01", temperature=True)


def test_transcribe_audio_rejects_non_finite_temperature() -> None:
    for value in (math.nan, math.inf, -math.inf):
        with pytest.raises(ValueError, match=_TEMPERATURE_ERROR):
            transcribe_audio(b"\x01", temperature=value)


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


def test_transcribe_audio_includes_authorisation_header(
    whisper_test_server: ServerFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_url, handler = whisper_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"text": "ok"}).encode("utf-8"),
        )
    )
    monkeypatch.setenv("SIGMA_WHISPER_AUTH_TOKEN", "secret-token")

    transcribe_audio(b"auth", url=f"{base_url}/inference")

    headers = _latest_request(handler)["headers"]
    assert headers.get("authorization") == "Bearer secret-token"


def test_transcribe_audio_customises_authorisation_scheme(
    whisper_test_server: ServerFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_url, handler = whisper_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"text": "ok"}).encode("utf-8"),
        )
    )
    monkeypatch.setenv("SIGMA_WHISPER_AUTH_TOKEN", "abc123")
    monkeypatch.setenv("SIGMA_WHISPER_AUTH_SCHEME", "ApiKey")

    transcribe_audio(b"first", url=f"{base_url}/inference")

    first_headers = _latest_request(handler)["headers"].copy()
    assert first_headers.get("authorization") == "ApiKey abc123"

    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"text": "ok"}).encode("utf-8"),
        )
    )
    monkeypatch.setenv("SIGMA_WHISPER_AUTH_SCHEME", "   ")

    transcribe_audio(b"second", url=f"{base_url}/inference")

    second_headers = _latest_request(handler)["headers"]
    assert second_headers.get("authorization") == "abc123"


def test_transcribe_audio_empty_authorisation_token_raises(
    whisper_test_server: ServerFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_url, handler = whisper_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"text": "ok"}).encode("utf-8"),
        )
    )
    monkeypatch.setenv("SIGMA_WHISPER_AUTH_TOKEN", "   ")

    with pytest.raises(RuntimeError, match="SIGMA_WHISPER_AUTH_TOKEN"):
        transcribe_audio(b"bytes", url=f"{base_url}/inference")


def test_transcribe_audio_uses_environment_url(
    whisper_test_server: ServerFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_url, handler = whisper_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"text": "env ok"}).encode("utf-8"),
        )
    )
    monkeypatch.setenv("SIGMA_WHISPER_URL", f"  {base_url}/env  ")

    result = transcribe_audio(b"env-bytes")

    assert result.text == "env ok"
    latest = _latest_request(handler)
    assert latest["path"] == "/env"


def test_transcribe_audio_empty_environment_url_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SIGMA_WHISPER_URL", "   ")

    with pytest.raises(RuntimeError, match="SIGMA_WHISPER_URL"):
        transcribe_audio(b"env-error")


def test_whisper_speech_to_text_honours_environment_default(
    whisper_test_server: ServerFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_url, handler = whisper_test_server
    handler.responses.append(
        (
            200,
            {"Content-Type": "application/json"},
            json.dumps({"text": "speech ok"}).encode("utf-8"),
        )
    )
    monkeypatch.setenv("SIGMA_WHISPER_URL", f"{base_url}/speech")

    stt = WhisperSpeechToText()
    result = stt.transcribe(b"speech-bytes")

    assert result.text == "speech ok"
    latest = _latest_request(handler)
    assert latest["path"] == "/speech"
