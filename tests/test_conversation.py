from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from sigma.audio.interfaces import ConversationAudio
from sigma.audio.ptt import PassthroughPushToTalk
from sigma.conversation import ConversationResult, run_conversation
from sigma.llm_client import LLMResponse
from sigma.whisper_client import WhisperResult


def _whisper_result() -> WhisperResult:
    return WhisperResult(
        text="Hello there",
        language="en",
        status=200,
        headers={},
        raw=b"{}",
        encoding="utf-8",
    )


def _llm_result() -> LLMResponse:
    return LLMResponse(
        name="Local",
        url="http://example.com",
        text="Sigma online",
        status=200,
        headers={},
        raw=b"{}",
        encoding="utf-8",
    )


def test_run_conversation_basic_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded: Dict[str, Dict[str, Any]] = {}

    whisper_response = _whisper_result()
    llm_response = _llm_result()

    def fake_transcribe(
        self,
        audio: Any,
        *,
        url: str | None,
        model: str | None,
        language: str | None,
        temperature: float | None,
        extra_params: Dict[str, Any] | None,
        timeout: float,
    ) -> WhisperResult:
        recorded["transcribe"] = {
            "audio": audio,
            "url": url,
            "model": model,
            "language": language,
            "temperature": temperature,
            "extra_params": extra_params,
            "timeout": timeout,
        }
        return whisper_response

    def fake_query(
        self,
        prompt: str | None,
        *,
        name: str | None,
        path: str | None,
        timeout: float | None,
        extra_payload: Dict[str, Any] | None,
    ) -> LLMResponse:
        recorded["query"] = {
            "prompt": prompt,
            "name": name,
            "path": path,
            "timeout": timeout,
            "extra_payload": extra_payload,
        }
        return llm_response

    def fake_synthesize(self, text: str, *, sample_rate: int) -> bytes:
        recorded["synthesize"] = {
            "text": text,
            "sample_rate": sample_rate,
        }
        return b"audio-bytes"

    monkeypatch.setattr(
        "sigma.whisper_client.WhisperSpeechToText.transcribe",
        fake_transcribe,
    )
    monkeypatch.setattr(
        "sigma.llm_client.ConfiguredLLMRouter.query",
        fake_query,
    )
    monkeypatch.setattr(
        "sigma.tts.FormantTextToSpeech.synthesize",
        fake_synthesize,
    )

    result = run_conversation(
        b"\x00\x01",
        whisper_url="http://whisper",
        whisper_model="base.en",
        whisper_language="en",
        whisper_temperature=0.0,
        whisper_extra_params={"beam_size": 5},
        whisper_timeout=12.5,
        llm_name="Custom",
        llm_path="custom-llms.txt",
        llm_timeout=22.0,
        llm_extra_payload={"temperature": 0.3},
        prompt_template="Echo: {transcript} ({language})",
        tts_sample_rate=16_000,
    )

    assert isinstance(result, ConversationResult)
    assert result.transcript is whisper_response
    assert result.llm is llm_response
    assert result.audio == b"audio-bytes"
    assert result.audio_path is None

    expected_prompt = "Echo: Hello there (en)"
    assert result.prompt == expected_prompt

    assert recorded["transcribe"] == {
        "audio": b"\x00\x01",
        "url": "http://whisper",
        "model": "base.en",
        "language": "en",
        "temperature": 0.0,
        "extra_params": {"beam_size": 5},
        "timeout": 12.5,
    }

    assert recorded["query"] == {
        "prompt": expected_prompt,
        "name": "Custom",
        "path": "custom-llms.txt",
        "timeout": 22.0,
        "extra_payload": {"temperature": 0.3},
    }

    assert recorded["synthesize"] == {
        "text": llm_response.text,
        "sample_rate": 16_000,
    }


def test_run_conversation_writes_audio(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    whisper_response = _whisper_result()
    llm_response = _llm_result()

    monkeypatch.setattr(
        "sigma.whisper_client.WhisperSpeechToText.transcribe",
        lambda self, *args, **kwargs: whisper_response,
    )
    monkeypatch.setattr(
        "sigma.llm_client.ConfiguredLLMRouter.query",
        lambda self, *args, **kwargs: llm_response,
    )

    synth_calls: list[Dict[str, Any]] = []

    def fake_synthesize(self, text: str, *, sample_rate: int) -> bytes:
        synth_calls.append({"text": text, "sample_rate": sample_rate})
        return b"wav-data"

    monkeypatch.setattr(
        "sigma.tts.FormantTextToSpeech.synthesize",
        fake_synthesize,
    )

    destination = tmp_path / "audio" / "reply.wav"

    result = run_conversation(
        b"\x02",
        prompt="Custom prompt",
        output_path=destination,
    )

    assert destination.is_file()
    assert destination.read_bytes() == b"wav-data"
    assert result.audio == b"wav-data"
    assert result.audio_path == destination
    assert result.prompt == "Custom prompt"
    assert synth_calls == [{"text": llm_response.text, "sample_rate": 22_050}]


def test_run_conversation_supports_promptless_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    whisper_response = _whisper_result()
    llm_response = _llm_result()

    monkeypatch.setattr(
        "sigma.whisper_client.WhisperSpeechToText.transcribe",
        lambda self, *args, **_: whisper_response,
    )

    recorded: Dict[str, Dict[str, Any]] = {}

    def fake_query(
        self,
        prompt: str | None,
        *,
        name: str | None,
        path: str | None,
        timeout: float | None,
        extra_payload: Dict[str, Any] | None,
    ) -> LLMResponse:
        recorded["query"] = {
            "prompt": prompt,
            "extra_payload": extra_payload,
        }
        return llm_response

    monkeypatch.setattr(
        "sigma.llm_client.ConfiguredLLMRouter.query",
        fake_query,
    )
    monkeypatch.setattr(
        "sigma.tts.FormantTextToSpeech.synthesize",
        lambda self, *_args, **_kwargs: b"spoken",
    )

    payload = {"messages": [{"role": "user", "content": "Hi"}]}
    result = run_conversation(
        b"\x03",
        prompt_template=None,
        llm_extra_payload=payload,
    )

    assert result.prompt is None
    assert recorded["query"] == {
        "prompt": None,
        "extra_payload": payload,
    }


def test_run_conversation_with_push_to_talk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    whisper_response = _whisper_result()
    llm_response = _llm_result()

    class StubSTT:
        def transcribe(self, audio, **_: Any) -> WhisperResult:
            assert audio == b"capture"
            return whisper_response

    class StubRouter:
        def query(self, prompt, **_: Any) -> LLMResponse:
            assert prompt == whisper_response.text
            return llm_response

    class StubTTS:
        def synthesize(self, text: str, *, sample_rate: int = 22_050) -> bytes:
            assert sample_rate == 22_050
            assert text == llm_response.text
            return b"stub-audio"

    payload = ConversationAudio(data=b"capture")
    ptt = PassthroughPushToTalk(payload)

    result = run_conversation(
        None,
        push_to_talk=ptt,
        speech_to_text=StubSTT(),
        llm_router=StubRouter(),
        tts_engine=StubTTS(),
    )

    assert result.audio == b"stub-audio"
    assert result.transcript is whisper_response
    assert result.llm is llm_response
