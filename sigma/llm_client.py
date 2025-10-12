"""Helpers for querying language model endpoints."""

from __future__ import annotations

import argparse
import json
import os
import sys
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
_AUTH_TOKEN_ENV = "SIGMA_LLM_AUTH_TOKEN"
_AUTH_SCHEME_ENV = "SIGMA_LLM_AUTH_SCHEME"
_TRAILING_ONLY_KEYS = {
    "output",
    "outputs",
    "result",
    "results",
    "completion",
    "completions",
    "candidates",
    "generations",
    "generation",
}


def _extract_text_value(value: Any) -> str | None:
    """Return text extracted from *value* when present."""

    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        segment_keys = ("segments", "parts")
        text_keys = (
            "response",
            "text",
            "content",
            "output",
            "outputs",
            "output_text",
            "result",
            "results",
            "completion",
            "completions",
            "candidates",
            "generations",
            "generation",
            "generated_text",
        )
        has_segment_like = any(key in value for key in segment_keys)
        text_candidates: list[tuple[str, str]] = []
        post_fragments: list[str] = []
        segment_fragments: list[str] = []
        value_fragment: str | None = None

        for key in value:
            if key in segment_keys:
                candidate = _extract_text_value(value[key])
                if isinstance(candidate, str):
                    segment_fragments.append(candidate)
                continue
            if key == "value":
                candidate = _extract_text_value(value[key])
                if not isinstance(candidate, str):
                    continue
                if value_fragment is None:
                    value_fragment = candidate
                else:
                    post_fragments.append(candidate)
                continue
            if key in text_keys:
                candidate = _extract_text_value(value[key])
                if not isinstance(candidate, str):
                    continue
                text_candidates.append((key, candidate))

        def _pop_primary(candidates: list[tuple[str, str]]) -> str | None:
            for index, (
                candidate_key,
                _candidate_text,
            ) in enumerate(candidates):
                if candidate_key not in _TRAILING_ONLY_KEYS:
                    return candidates.pop(index)[1]
            if candidates:
                return candidates.pop(0)[1]
            return None

        if not has_segment_like:
            ordered: list[str] = []
            trailing: list[str] = []
            base_fragment = (
                value_fragment
                if value_fragment is not None
                else _pop_primary(text_candidates)
            )
            if base_fragment is not None:
                ordered.append(base_fragment)
            if text_candidates:
                non_trailing: list[str] = []
                trailing_only: list[str] = []
                for candidate_key, candidate_text in text_candidates:
                    if candidate_key in _TRAILING_ONLY_KEYS:
                        trailing_only.append(candidate_text)
                    else:
                        non_trailing.append(candidate_text)
                trailing.extend(non_trailing)
                trailing.extend(trailing_only)
            if post_fragments:
                trailing.extend(post_fragments)
            if trailing:
                ordered.extend(trailing)
            if ordered:
                return "".join(ordered)
            if text_candidates:
                joined_candidates_parts: list[str] = []
                for _candidate_key, candidate_text in text_candidates:
                    joined_candidates_parts.append(candidate_text)
                return "".join(joined_candidates_parts)
        if has_segment_like:
            ordered_fragments: list[str] = []
            trailing_fragments: list[str] = []
            base_fragment = (
                value_fragment
                if value_fragment is not None
                else _pop_primary(text_candidates)
            )
            if base_fragment is not None:
                ordered_fragments.append(base_fragment)
            if segment_fragments:
                ordered_fragments.extend(segment_fragments)
            if text_candidates:
                non_trailing: list[str] = []
                trailing_only: list[str] = []
                for candidate_key, candidate_text in text_candidates:
                    if candidate_key in _TRAILING_ONLY_KEYS:
                        trailing_only.append(candidate_text)
                    else:
                        non_trailing.append(candidate_text)
                trailing_fragments.extend(non_trailing)
                trailing_fragments.extend(trailing_only)
            if post_fragments:
                trailing_fragments.extend(post_fragments)
            if trailing_fragments:
                ordered_fragments.extend(trailing_fragments)
            if ordered_fragments:
                return "".join(ordered_fragments)
        if text_candidates:
            joined_candidates_parts: list[str] = []
            for _candidate_key, candidate_text in text_candidates:
                joined_candidates_parts.append(candidate_text)
            return "".join(joined_candidates_parts)
        # Also look inside common wrapper structures.
        for key in ("message", "messages", "delta", "data"):
            nested = value.get(key)
            if nested is not None:
                candidate = _extract_text_value(nested)
                if isinstance(candidate, str):
                    return candidate
        return None
    if isinstance(value, list):
        fragments: list[str] = []
        for item in value:
            fragment = _extract_text_value(item)
            if isinstance(fragment, str):
                fragments.append(fragment)
        if fragments:
            return "".join(fragments)
    return None


def _join_text_parts(parts: Any) -> str | None:
    """Return concatenated text extracted from iterable ``parts``."""

    return _extract_text_value(parts)


def _extract_message_content(content: Any) -> str | None:
    """Return text extracted from OpenAI-style ``message.content`` values."""

    return _extract_text_value(content)


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


def _build_authorisation_header() -> Mapping[str, str]:
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


def _extract_text(data: Any) -> str | None:
    choices: Any | None = None
    if isinstance(data, Mapping):
        trimmed = dict(data.items())
        choices = trimmed.pop("choices", None)
        trimmed.pop("messages", None)
        trailing_extras: dict[str, Any] = {}
        for key in list(trimmed.keys()):
            if key in _TRAILING_ONLY_KEYS:
                trailing_extras[key] = trimmed.pop(key)
        direct = _extract_text_value(trimmed)
        if trailing_extras:
            extras_text = _extract_text_value(trailing_extras)
        else:
            extras_text = None
        primary_choice: str | None = None
        if isinstance(choices, list):
            for choice in choices:
                text_value = _extract_text_value(choice)
                if isinstance(text_value, str):
                    primary_choice = text_value
                    break
        base_text = direct if isinstance(direct, str) and direct else None
        if (
            base_text is not None
            or primary_choice is not None
            or extras_text is not None
        ):
            fragments: list[str] = []
            if base_text is not None:
                fragments.append(base_text)
            elif primary_choice is not None:
                fragments.append(primary_choice)
            if extras_text:
                fragments.append(extras_text)
            if fragments:
                return "".join(fragments)
    else:
        direct = _extract_text_value(data)
        extras_text = None
        primary_choice = None

    if isinstance(direct, str):
        return direct

    if isinstance(data, Mapping):
        if choices is not None:
            choices_to_check = choices
        else:
            choices_to_check = data.get("choices")
        if isinstance(choices_to_check, list):
            for choice in choices_to_check:
                choice_text = _extract_text_value(choice)
                if isinstance(choice_text, str):
                    return choice_text
        messages = data.get("messages")
        if isinstance(messages, list):
            assistant_fragments: list[str] = []
            for message in messages:
                message_text: str | None = None
                if isinstance(message, Mapping):
                    role = message.get("role")
                    if role is not None and role != "assistant":
                        continue
                    if "content" in message:
                        content_value = message["content"]
                        message_text = _extract_message_content(content_value)
                    if message_text is None:
                        message_text = _extract_text_value(message)
                else:
                    message_text = _extract_text_value(message)
                if isinstance(message_text, str):
                    assistant_fragments.append(message_text)
            if assistant_fragments:
                return "".join(assistant_fragments)
            message_text = _extract_text_value(messages)
            if isinstance(message_text, str):
                return message_text
        # Handle common response containers in different API formats.
        output = data.get("output")
        if isinstance(output, list):
            output_text = _extract_text_value(output)
            if isinstance(output_text, str):
                return output_text

        # Recursively unwrap nested response keys from OpenAI, Anthropic,
        # or custom APIs.
        for key in (
            "data",
            "response",
            "output",
            "outputs",
            "result",
            "results",
            "completion",
            "completions",
            "candidates",
        ):
            if key in data:
                nested_value = data[key]
                extracted = _extract_text(nested_value)
                if isinstance(extracted, str):
                    return extracted
    if isinstance(data, list):
        return _extract_text_value(data)
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
    normalized_url = url.strip()
    parsed = parse.urlparse(normalized_url)
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
    headers.update(_build_authorisation_header())
    req = request.Request(
        normalized_url,
        data=body,
        headers=headers,
        method="POST",
    )
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
                url=normalized_url,
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


def _parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Return parsed CLI arguments for ``python -m sigma.llm_client``."""

    # fmt: off
    parser = argparse.ArgumentParser(
        prog="python -m sigma.llm_client",
        description=(
            "Send a prompt to the configured LLM endpoint "
            "and show the result."
        ),
    )
    # fmt: on
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Prompt to send. Reads from stdin when omitted.",
    )
    parser.add_argument(
        "-n",
        "--name",
        help="Endpoint name (case-insensitive). Defaults to configured entry.",
    )
    parser.add_argument(
        "-p",
        "--path",
        help="Optional llms.txt path. Expands environment variables and ~.",
    )
    parser.add_argument(
        "-e",
        "--extra",
        help="JSON object merged into the request body for provider options.",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=10.0,
        help="Request timeout in seconds (default: 10).",
    )
    parser.add_argument(
        "--show-json",
        action="store_true",
        help="Pretty-print the JSON response body when available.",
    )
    return parser.parse_args(argv)


def _read_prompt(arg_value: str | None) -> str:
    """Return the CLI prompt, reading from stdin when necessary."""

    if arg_value is not None:
        return arg_value

    data = sys.stdin.read()
    if not data:
        raise RuntimeError("Prompt is required when standard input is empty.")
    return data.rstrip("\n")


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for ``python -m sigma.llm_client``."""

    try:
        args = _parse_cli_args(argv)
        prompt = _read_prompt(args.prompt)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    extra_payload: Mapping[str, Any] | None = None
    if args.extra is not None:
        try:
            decoded = json.loads(args.extra)
        except json.JSONDecodeError as exc:
            print(f"Failed to parse --extra JSON: {exc}", file=sys.stderr)
            return 1
        if not isinstance(decoded, Mapping):
            print("--extra JSON must decode to an object", file=sys.stderr)
            return 1
        extra_payload = decoded

    try:
        result = query_llm(
            prompt,
            name=args.name,
            path=args.path,
            timeout=args.timeout,
            extra_payload=extra_payload,
        )
    except (RuntimeError, TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(result.text)
    if args.show_json:
        try:
            payload = result.json()
        except ValueError as exc:
            print(
                f"Warning: Unable to display JSON payload: {exc}",
                file=sys.stderr,
            )
        else:
            if payload is None:
                print("Warning: No JSON payload available.", file=sys.stderr)
            else:
                print(json.dumps(payload, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
