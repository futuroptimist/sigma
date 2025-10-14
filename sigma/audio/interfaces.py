import os
import typing as t
from dataclasses import dataclass

if t.TYPE_CHECKING:  # pragma: no cover - import for typing only
    from sigma.llm_client import LLMResponse
    from sigma.whisper_client import WhisperResult

# fmt: off
AudioInput = (
    bytes
    | bytearray
    | memoryview
    | str
    | os.PathLike[str]
    | t.BinaryIO
)
# fmt: on


@dataclass(frozen=True)
class ConversationAudio:
    """Wrapper that describes captured audio payloads."""

    data: bytes
    mime_type: str = "audio/wav"


@t.runtime_checkable
class PushToTalkInterface(t.Protocol):
    """Abstraction for push-to-talk triggers."""

    def capture(self) -> ConversationAudio:
        """Block until the user captures audio and return the payload."""


@t.runtime_checkable
class SpeechToTextInterface(t.Protocol):
    """Speech-to-text abstraction that mirrors Whisper's surface area."""

    def transcribe(
        self,
        audio: AudioInput,
        /,
        *,
        url: str | None = None,
        model: str | None = None,
        language: str | None = None,
        temperature: float | None = None,
        extra_params: t.Mapping[str, t.Any] | None = None,
        timeout: float = 30.0,
    ) -> "WhisperResult": ...


@t.runtime_checkable
class LLMRouterInterface(t.Protocol):
    """Route prompts to a large language model."""

    def query(
        self,
        prompt: str | None,
        /,
        *,
        name: str | None = None,
        path: str | None = None,
        timeout: float | None = None,
        extra_payload: t.Mapping[str, t.Any] | None = None,
    ) -> "LLMResponse": ...  # noqa: E501


@t.runtime_checkable
class TextToSpeechInterface(t.Protocol):
    """Generate audio from synthesized text."""

    def synthesize(
        self, text: str, /, *, sample_rate: int = 22_050
    ) -> bytes: ...  # noqa: E501
