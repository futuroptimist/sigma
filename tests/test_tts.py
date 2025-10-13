import io
import wave
from pathlib import Path

import pytest

from sigma.tts import save_speech, synthesize_speech


def _read_wav_meta(data: bytes) -> tuple[int, int, int, int]:
    with wave.open(io.BytesIO(data), "rb") as wav_file:
        return (
            wav_file.getnchannels(),
            wav_file.getsampwidth(),
            wav_file.getframerate(),
            wav_file.getnframes(),
        )


def test_synthesize_speech_returns_valid_wav() -> None:
    data = synthesize_speech("Sigma ready")
    channels, sample_width, rate, frames = _read_wav_meta(data)
    assert channels == 1
    assert sample_width == 2
    assert rate == 22_050
    assert frames > 2_000


def test_synthesize_speech_accepts_custom_sample_rate() -> None:
    data = synthesize_speech("Hello", sample_rate=16_000)
    _, _, rate, frames = _read_wav_meta(data)
    assert rate == 16_000
    assert frames > 0


def test_synthesize_speech_handles_mixed_characters() -> None:
    data = synthesize_speech("R2-D2 online!")
    _, _, _, frames = _read_wav_meta(data)
    assert frames > 2_000


def test_synthesize_speech_rejects_empty_text() -> None:
    with pytest.raises(ValueError):
        synthesize_speech("   ")


def test_save_speech_writes_wav_file(tmp_path: Path) -> None:
    destination = tmp_path / "reply.wav"
    result_path = save_speech("Sigma acknowledges", destination)
    assert result_path == destination
    assert destination.is_file()
    header = destination.read_bytes()[:4]
    assert header == b"RIFF"
