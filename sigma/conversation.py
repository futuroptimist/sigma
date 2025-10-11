"""High-level helpers that orchestrate speech → LLM → speech interactions."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Mapping

from .llm_client import LLMResponse, query_llm
from .tts import synthesize_speech
from .whisper_client import WhisperResult, transcribe_audio

__all__ = ["ConversationResult", "run_conversation"]


@dataclass(frozen=True)
class ConversationResult:
    """Aggregate result produced by :func:`run_conversation`."""

    transcript: WhisperResult
    prompt: str | None
    llm: LLMResponse
    audio: bytes
    audio_path: Path | None


def run_conversation(
    audio: bytes | bytearray | memoryview | str | os.PathLike[str] | BinaryIO,
    *,
    prompt: str | None = None,
    prompt_template: str | None = "{transcript}",
    whisper_url: str | None = None,
    whisper_model: str | None = None,
    whisper_language: str | None = None,
    whisper_temperature: float | None = None,
    whisper_extra_params: Mapping[str, Any] | None = None,
    whisper_timeout: float = 30.0,
    llm_name: str | None = None,
    llm_path: str | os.PathLike[str] | None = None,
    llm_timeout: float = 10.0,
    llm_extra_payload: Mapping[str, Any] | None = None,
    tts_sample_rate: int = 22_050,
    output_path: str | os.PathLike[str] | None = None,
) -> ConversationResult:
    """Transcribe *audio*, query an LLM, and synthesise a spoken reply.

    The helper streams audio through
    :func:`sigma.whisper_client.transcribe_audio`, forwards the
    resulting transcript to :func:`sigma.llm_client.query_llm`, and
    renders the reply with :func:`sigma.tts.synthesize_speech`. By
    default the Whisper transcript
    becomes the LLM prompt; override ``prompt`` to supply a custom value or set
    ``prompt_template`` to ``None`` when the payload is provided entirely via
    ``llm_extra_payload`` (for example chat-style ``messages`` arrays).

    Additional keyword arguments are passed to the underlying helpers so the
    caller can pick Whisper models, select different LLM endpoints, or adjust
    the text-to-speech sample rate. When *output_path* is provided,
    the generated WAV data is also written to disk and the resolved
    :class:`~pathlib.Path` is
    exposed on the returned :class:`ConversationResult`.
    """

    transcribe_kwargs: dict[str, Any] = {"timeout": whisper_timeout}
    if whisper_url is not None:
        transcribe_kwargs["url"] = whisper_url
    if whisper_model is not None:
        transcribe_kwargs["model"] = whisper_model
    if whisper_language is not None:
        transcribe_kwargs["language"] = whisper_language
    if whisper_temperature is not None:
        transcribe_kwargs["temperature"] = whisper_temperature
    if whisper_extra_params is not None:
        transcribe_kwargs["extra_params"] = whisper_extra_params

    transcript = transcribe_audio(audio, **transcribe_kwargs)

    if prompt is not None:
        resolved_prompt = prompt
    elif prompt_template is None:
        resolved_prompt = None
    else:
        if not isinstance(prompt_template, str):
            raise TypeError("prompt_template must be a string when provided")
        format_kwargs = {
            "transcript": transcript.text,
            "language": transcript.language or "",
        }
        try:
            resolved_prompt = prompt_template.format(**format_kwargs)
        except (IndexError, KeyError) as exc:
            message = (
                "prompt_template references unknown placeholders; "
                "available keys: transcript, language"
            )
            raise ValueError(message) from exc

    llm_response = query_llm(
        resolved_prompt,
        name=llm_name,
        path=llm_path,
        timeout=llm_timeout,
        extra_payload=llm_extra_payload,
    )

    audio_bytes = synthesize_speech(
        llm_response.text,
        sample_rate=tts_sample_rate,
    )

    audio_path: Path | None = None
    if output_path is not None:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(audio_bytes)
        audio_path = destination

    return ConversationResult(
        transcript=transcript,
        prompt=resolved_prompt,
        llm=llm_response,
        audio=audio_bytes,
        audio_path=audio_path,
    )
