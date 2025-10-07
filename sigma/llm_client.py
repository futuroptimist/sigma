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


def _join_text_parts(parts: Any) -> str | None:
    """Return concatenated text extracted from iterable ``parts``."""

    if isinstance(parts, str):
        return parts
    if isinstance(parts, Mapping):
        return _extract_message_content(parts)
    if not isinstance(parts, list):
        nested = _extract_text(parts)
        return nested if isinstance(nested, str) else None

    fragments: list[str] = []
    for part in parts:
        if isinstance(part, str):
            fragments.append(part)
            continue
        if isinstance(part, Mapping):
            text_value = part.get("text")
            if isinstance(text_value, str):
                fragments.append(text_value)
                continue
            nested = part.get("content")
            nested_text = _join_text_parts(nested)
            if isinstance(nested_text, str):
                fragments.append(nested_text)
                continue
        elif isinstance(part, list):
            nested_text = _join_text_parts(part)
            if isinstance(nested_text, str):
                fragments.append(nested_text)
                continue
        else:
            nested_text = _extract_text(part)
            if isinstance(nested_text, str):
                fragments.append(nested_text)
                continue
    if fragments:
        return "".join(fragments)
    return None


def _extract_message_content(content: Any) -> str | None:
    """Return text extracted from OpenAI-style ``message.content`` values."""

    if isinstance(content, str):
        return content
    if isinstance(content, Mapping):
        direct_text = content.get("text")
        if isinstance(direct_text, str):
            return direct_text
        nested_content = content.get("content")
        if nested_content is not None:
            return _extract_message_content(nested_content)
        return None
    if isinstance(content, list):
        return _join_text_parts(content)
    nested = _extract_text(content)
    return nested if isinstance(nested, str) else None


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
        payload.pop("prompt", None)
        payload["prompt"] = _ensure_prompt(prompt)
    elif "prompt" in payload:
        payload["prompt"] = _ensure_prompt(payload["prompt"])

    if not payload:
        raise ValueError(
            "Payload must include at least one field; provide prompt or "
            "extra_payload"
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
        direct_content = _extract_message_content(data.get("content"))
        if isinstance(direct_content, str):
            return direct_content
        message_value = data.get("message")
        if message_value is not None:
            message_text = _extract_text(message_value)
            if isinstance(message_text, str):
                return message_text
        choices = data.get("choices")
        if isinstance(choices, list):
            for choice in choices:
                if not isinstance(choice, Mapping):
                    continue
                text_value = choice.get("text")
                if isinstance(text_value, str):
                    return text_value
                message = choice.get("message")
                if message is not None:
                    content_text = _extract_text(message)
                    if isinstance(content_text, str):
                        return content_text
        data_field = data.get("data")
        if data_field is not None:
            nested = _extract_text(data_field)
            if isinstance(nested, str):
                return nested
    if isinstance(data, list):
        combined = _join_text_parts(data)
        if isinstance(combined, str):
            return combined
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
            is_json_content = content_type in _JSON_CONTENT_TYPES
            json_error: json.JSONDecodeError | None = None
            if raw:
                stripped = text_body.lstrip()
                json_like = stripped.startswith(("{", "["))
                if is_json_content or json_like:
                    try:
                        parsed_json = json.loads(text_body)
                    except json.JSONDecodeError as exc:
                        json_error = exc
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
                should_raise = is_json_content
                if should_raise:
                    detail = "invalid JSON"
                    if not raw:
                        detail = "an empty JSON response"
                    message = "LLM endpoint '{name}' returned {detail}".format(
                        name=display_name,
                        detail=detail,
                    )
                    if json_error is not None:
                        raise RuntimeError(message) from json_error
                    raise RuntimeError(message)
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
