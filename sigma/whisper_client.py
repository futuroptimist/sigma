"""Helpers for sending audio to ``whisper.cpp``-style servers."""

from __future__ import annotations

import base64
import json
import math
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO, Mapping
from urllib import error, request

from sigma.audio.interfaces import AudioInput, SpeechToTextInterface

__all__ = ["WhisperResult", "transcribe_audio", "WhisperSpeechToText"]


@dataclass(frozen=True)
class WhisperResult:
    """Response returned by :func:`transcribe_audio`."""

    text: str
    language: str | None
    status: int
    headers: Mapping[str, str]
    raw: bytes
    encoding: str

    def json(self) -> Any:
        """Return the decoded JSON payload when available."""

        if not self.raw:
            return None
        try:
            decoded = self.raw.decode(self.encoding)
        except UnicodeDecodeError as exc:  # pragma: no cover - defensive guard
            message = "Response payload is not valid UTF-8 JSON"
            raise ValueError(message) from exc
        try:
            return json.loads(decoded)
        except json.JSONDecodeError as exc:
            raise ValueError("Response payload is not valid JSON") from exc


_DEFAULT_WHISPER_URL = "http://127.0.0.1:8080/inference"
_ERR_NO_TRANSCRIPT = "Whisper server response did not include a transcription"
_AUTH_TOKEN_ENV = "SIGMA_WHISPER_AUTH_TOKEN"
_AUTH_SCHEME_ENV = "SIGMA_WHISPER_AUTH_SCHEME"
_URL_OVERRIDE_ENV = "SIGMA_WHISPER_URL"
_AUDIO_STAGING_ENV = "SIGMA_AUDIO_DIR"


def _coerce_audio_bytes(audio: Any) -> bytes:
    """Return raw audio bytes extracted from *audio*."""

    if isinstance(audio, (bytes, bytearray, memoryview)):
        data = bytes(audio)
    elif isinstance(audio, (str, os.PathLike)):
        expanded = Path(os.path.expandvars(os.fspath(audio))).expanduser()
        data = expanded.read_bytes()
    else:
        if not hasattr(audio, "read"):
            message = "audio must be bytes, a path, or a binary file object"
            raise TypeError(message)
        stream = audio  # type: ignore[assignment]
        chunk = stream.read()
        if not isinstance(chunk, (bytes, bytearray, memoryview)):
            raise TypeError("audio file objects must yield bytes")
        data = bytes(chunk)
    if not data:
        raise ValueError("audio payload must be non-empty")
    return data


def _stage_audio_payload(data: bytes) -> None:
    """Persist *data* to ``SIGMA_AUDIO_DIR`` when configured."""

    staging_raw = os.getenv(_AUDIO_STAGING_ENV)
    if staging_raw is None:
        return

    expanded = os.path.expandvars(staging_raw)
    trimmed = expanded.strip()
    if not trimmed:
        message = (
            f"Environment variable {_AUDIO_STAGING_ENV} is set "
            "but empty after stripping."
        )
        raise RuntimeError(message)

    destination_dir = Path(trimmed).expanduser()
    try:
        destination_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:  # pragma: no cover - filesystem failure guard
        detail = f"{destination_dir}: {exc}"
        message = "Failed to create audio staging directory " + detail
        raise RuntimeError(message) from exc

    extension = "wav" if data.startswith(b"RIFF") else "raw"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"capture-{timestamp}-{uuid.uuid4().hex}.{extension}"
    destination = destination_dir / filename
    try:
        destination.write_bytes(data)
    except OSError as exc:  # pragma: no cover - filesystem failure guard
        message = f"Failed to write staged audio to {destination}: {exc}"
        raise RuntimeError(message) from exc


def _extract_transcript(value: Any) -> tuple[str | None, str | None]:
    """Return ``(text, language)`` extracted from ``value`` when available."""

    if isinstance(value, Mapping):
        language_raw = value.get("language")
        language = language_raw if isinstance(language_raw, str) else None

        for key in ("text", "transcription", "transcript"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate:
                return candidate, language

        segments = value.get("segments")
        if isinstance(segments, list):
            fragments: list[str] = []
            segment_language: str | None = None
            for segment in segments:
                text, lang = _extract_transcript(segment)
                if text:
                    fragments.append(text)
                if segment_language is None and lang:
                    segment_language = lang
            if fragments:
                combined = "".join(fragments)
                return combined, segment_language or language

        for key in ("result", "results", "data", "response", "output"):
            if key in value:
                text, nested_language = _extract_transcript(value[key])
                if text:
                    return text, nested_language or language

        nested_text = value.get("text")
        if isinstance(nested_text, list):
            text, nested_language = _extract_transcript(nested_text)
            if text:
                return text, nested_language or language

        return None, language

    if isinstance(value, list):
        fragments: list[str] = []
        language: str | None = None
        for item in value:
            text, item_language = _extract_transcript(item)
            if text:
                fragments.append(text)
            if language is None and item_language:
                language = item_language
        if fragments:
            return "".join(fragments), language
        return None, language

    if isinstance(value, str) and value:
        return value, None

    return None, None


def _build_authorisation_header() -> dict[str, str]:
    """Return optional ``Authorization`` header derived from environment."""

    token_raw = os.getenv(_AUTH_TOKEN_ENV)
    if token_raw is None:
        return {}
    token = token_raw.strip()
    if not token:
        message = (
            f"Environment variable {_AUTH_TOKEN_ENV} is set "
            "but empty after stripping."
        )
        raise RuntimeError(message)

    scheme_raw = os.getenv(_AUTH_SCHEME_ENV)
    scheme = scheme_raw.strip() if scheme_raw is not None else "Bearer"
    if not scheme:
        value = token
    else:
        value = f"{scheme} {token}"
    return {"Authorization": value}


def _resolve_whisper_url(url: str | None) -> str:
    """Return the Whisper endpoint URL honouring environment overrides."""

    if url is not None:
        if not isinstance(url, str):
            raise TypeError("url must be a string when provided")
        return url

    env_override_raw = os.getenv(_URL_OVERRIDE_ENV)
    if env_override_raw is not None:
        env_override = env_override_raw.strip()
        if env_override:
            return env_override
        return _DEFAULT_WHISPER_URL

    return _DEFAULT_WHISPER_URL


def transcribe_audio(
    audio: bytes | bytearray | memoryview | str | os.PathLike[str] | BinaryIO,
    *,
    url: str | None = None,
    model: str | None = None,
    language: str | None = None,
    temperature: float | None = None,
    extra_params: Mapping[str, Any] | None = None,
    timeout: float = 30.0,
) -> WhisperResult:
    """Send *audio* to a Whisper server and return the transcription result."""

    audio_bytes = _coerce_audio_bytes(audio)
    _stage_audio_payload(audio_bytes)
    audio_payload = base64.b64encode(audio_bytes).decode("ascii")
    if not audio_payload.isascii():  # pragma: no cover - defensive guard
        raise RuntimeError("Encoded audio payload must be ASCII")

    resolved_url = _resolve_whisper_url(url)

    payload: dict[str, Any] = {
        "audio": audio_payload,
    }
    if model is not None:
        if not isinstance(model, str):
            raise TypeError("model must be a string when provided")
        payload["model"] = model
    if language is not None:
        if not isinstance(language, str):
            raise TypeError("language must be a string when provided")
        payload["language"] = language
    if temperature is not None:
        if isinstance(temperature, bool):
            raise TypeError("temperature must be a finite number")
        try:
            numeric_temperature = float(temperature)
        except (TypeError, ValueError) as exc:
            raise TypeError("temperature must be a finite number") from exc
        if not math.isfinite(numeric_temperature):
            raise ValueError("temperature must be a finite number")
        payload["temperature"] = numeric_temperature
    if extra_params is not None:
        if not isinstance(extra_params, Mapping):
            message = "extra_params must be a mapping if provided"
            raise TypeError(message)
        if any(key == "audio" for key in extra_params):
            message = "extra_params must not override the audio payload"
            raise ValueError(message)
        payload.update(extra_params)

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json, text/plain",
    }
    headers.update(_build_authorisation_header())

    req = request.Request(
        resolved_url,
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            encoding = response.headers.get_content_charset("utf-8")
            if not raw:
                raise RuntimeError("Whisper server returned an empty response")

            text_body = raw.decode(encoding, errors="replace")
            content_type = response.headers.get_content_type()

            transcript_text: str | None = None
            transcript_language: str | None = None

            is_json = content_type == "application/json"
            if is_json or text_body.lstrip().startswith(("{", "[")):
                try:
                    parsed = json.loads(text_body)
                except json.JSONDecodeError as exc:
                    message = "Whisper server returned invalid JSON"
                    raise RuntimeError(message) from exc
                extracted = _extract_transcript(parsed)
                transcript_text, transcript_language = extracted
                if transcript_text is None:
                    raise RuntimeError(_ERR_NO_TRANSCRIPT)
            else:
                transcript_text = text_body

            return WhisperResult(
                text=transcript_text,
                language=transcript_language,
                status=response.status,
                headers=dict(response.headers.items()),
                raw=raw,
                encoding=encoding,
            )
    except error.HTTPError as exc:  # pragma: no cover - network failure guard
        message = f"Whisper request failed with HTTP status {exc.code}"
        raise RuntimeError(message) from exc
    except error.URLError as exc:
        message = f"Failed to reach Whisper server: {exc.reason}"
        raise RuntimeError(message) from exc


class WhisperSpeechToText(SpeechToTextInterface):
    """Speech-to-text adapter that delegates to :func:`transcribe_audio`."""

    def __init__(self, *, default_url: str | None = None) -> None:
        self._default_url = default_url

    def transcribe(
        self,
        audio: AudioInput,
        /,
        *,
        url: str | None = None,
        model: str | None = None,
        language: str | None = None,
        temperature: float | None = None,
        extra_params: Mapping[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> WhisperResult:
        if url is not None:
            resolved_url: str | None = url
        elif self._default_url is not None:
            resolved_url = self._default_url
        else:
            resolved_url = None
        return transcribe_audio(
            audio,
            url=resolved_url,
            model=model,
            language=language,
            temperature=temperature,
            extra_params=extra_params,
            timeout=timeout,
        )
