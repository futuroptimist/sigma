"""Helpers for querying language model endpoints."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping
from urllib import error, parse, request

from llms import resolve_llm_endpoint

__all__ = ["LLMResponse", "query_llm"]


@dataclass(frozen=True)
class LLMResponse:
    """Response returned by :func:`query_llm`."""

    name: str
    url: str
    text: str
    status: int
    headers: Mapping[str, str]
    raw: bytes
    encoding: str

    def json(self) -> Any:
        """Return the decoded JSON payload from the response."""

        if not self.raw:
            return None
        try:
            decoded = self.raw.decode(self.encoding)
        except UnicodeDecodeError as exc:  # pragma: no cover
            message = "Response payload is not valid UTF-8 JSON"
            raise ValueError(message) from exc
        try:
            return json.loads(decoded)
        except json.JSONDecodeError as exc:
            raise ValueError("Response payload is not valid JSON") from exc


_SUPPORTED_SCHEMES = {"http", "https"}
_JSON_CONTENT_TYPES = {"application/json", "text/json"}


def _ensure_prompt(prompt: str) -> str:
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a string")
    stripped = prompt.strip()
    if not stripped:
        raise ValueError("prompt must be a non-empty string")
    return prompt


def _prepare_payload(
    prompt: str | None,
    extra_payload: Mapping[str, Any] | None,
) -> bytes:
    if extra_payload is not None:
        if not isinstance(extra_payload, Mapping):
            raise TypeError("extra_payload must be a mapping if provided")
        payload: MutableMapping[str, Any] = dict(extra_payload)
    else:
        payload = {}

    if prompt is not None:
        prompt_value = _ensure_prompt(prompt)
        payload.setdefault("prompt", prompt_value)

    if "prompt" in payload:
        payload["prompt"] = _ensure_prompt(payload["prompt"])

    if not payload:
        raise ValueError(
            "Payload must include at least one field; provide prompt or extra_payload"
        )
    try:
        return json.dumps(payload, ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        message = "extra_payload contains non-serialisable values"
        raise TypeError(message) from exc


def _extract_text(data: Any) -> str | None:
    if isinstance(data, str):
        return data
    if isinstance(data, Mapping):
        for key in ("response", "text"):
            value = data.get(key)
            if isinstance(value, str):
                return value
        choices = data.get("choices")
        if isinstance(choices, list):
            for choice in choices:
                if not isinstance(choice, Mapping):
                    continue
                text_value = choice.get("text")
                if isinstance(text_value, str):
                    return text_value
                message = choice.get("message")
                if isinstance(message, Mapping):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content
        data_field = data.get("data")
        if data_field is not None:
            nested = _extract_text(data_field)
            if isinstance(nested, str):
                return nested
    if isinstance(data, list):
        for item in data:
            text_value = _extract_text(item)
            if isinstance(text_value, str):
                return text_value
    return None


def query_llm(
    prompt: str | None,
    *,
    name: str | None = None,
    path: str | os.PathLike[str] | None = None,
    timeout: float = 10.0,
    extra_payload: Mapping[str, Any] | None = None,
) -> LLMResponse:
    """Send *prompt* to an HTTP LLM endpoint and return the parsed response."""

    display_name, url = resolve_llm_endpoint(name, path=path)
    parsed = parse.urlparse(url)
    if parsed.scheme.lower() not in _SUPPORTED_SCHEMES:
        message = (
            f"LLM endpoint '{display_name}' uses unsupported scheme "
            f"'{parsed.scheme}'"
        )
        raise RuntimeError(message)

    body = _prepare_payload(prompt, extra_payload)
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json, text/plain",
    }
    req = request.Request(url, data=body, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            encoding = response.headers.get_content_charset("utf-8")
            content_type = response.headers.get_content_type()
            text_body = raw.decode(encoding, errors="replace")
            parsed_json: Any | None = None
            if raw:
                stripped = text_body.lstrip()
                json_like = stripped.startswith(("{", "["))
                if content_type in _JSON_CONTENT_TYPES or json_like:
                    try:
                        parsed_json = json.loads(text_body)
                    except json.JSONDecodeError:
                        parsed_json = None
            if parsed_json is not None:
                text_value = _extract_text(parsed_json)
                if text_value is None:
                    raise RuntimeError(
                        "LLM endpoint "
                        f"'{display_name}' returned JSON without a recognised "
                        "text field"
                    )
            else:
                text_value = text_body
            return LLMResponse(
                name=display_name,
                url=url,
                text=text_value,
                status=response.status,
                headers=dict(response.headers.items()),
                raw=raw,
                encoding=encoding,
            )
    except error.HTTPError as exc:  # pragma: no cover
        template = "LLM request to '{name}' failed with HTTP status {code}"
        message = template.format(name=display_name, code=exc.code)
        raise RuntimeError(message) from exc
    except error.URLError as exc:
        message = "Failed to reach LLM endpoint '{name}': {reason}".format(
            name=display_name,
            reason=exc.reason,
        )
        raise RuntimeError(message) from exc
