from __future__ import annotations

import io
import math
import wave
from array import array
from pathlib import Path
from typing import Iterable

__all__ = ["synthesize_speech", "save_speech"]

# Simple formant-style frequencies for vowel sounds (Hz).
_VOWEL_FORMANTS: dict[str, tuple[float, float]] = {
    "a": (750.0, 1200.0),
    "e": (500.0, 1900.0),
    "i": (320.0, 2300.0),
    "o": (420.0, 860.0),
    "u": (360.0, 640.0),
    "y": (470.0, 1700.0),
}

# Deterministic digit tones so numbers sound distinct.
_DIGIT_BASE_FREQUENCY = dict(
    (str(value), 300.0 + (value * 22.0)) for value in range(10)
)

# Lightweight punctuation cues: (frequency, duration, noise mix).
_PUNCTUATION_PROFILES: dict[str, tuple[float, float, float]] = {
    ".": (240.0, 0.14, 0.12),
    ",": (220.0, 0.16, 0.14),
    "?": (500.0, 0.20, 0.06),
    "!": (540.0, 0.16, 0.08),
    ":": (260.0, 0.15, 0.12),
    ";": (280.0, 0.16, 0.12),
    "-": (210.0, 0.12, 0.18),
    "_": (190.0, 0.18, 0.18),
    "'": (360.0, 0.10, 0.08),
    '"': (340.0, 0.10, 0.08),
    "(": (230.0, 0.12, 0.10),
    ")": (230.0, 0.12, 0.10),
}

_WHITESPACE_SET = {" ", "\n", "\r", "\t"}


def _generate_silence(duration: float, sample_rate: int) -> array:
    frames = max(1, int(duration * sample_rate))
    return array("h", [0] * frames)


def _generate_tone(
    freqs: Iterable[float],
    duration: float,
    sample_rate: int,
    *,
    noise_mix: float = 0.0,
) -> array:
    freq_tuple = tuple(float(value) for value in freqs if value > 0.0)
    total_samples = max(1, int(duration * sample_rate))
    attack = max(1, int(sample_rate * 0.01))
    release = max(1, int(sample_rate * 0.03))
    amplitude = 0.85
    noise_mix = max(0.0, min(0.95, noise_mix))
    tone_mix = 1.0 - noise_mix
    noise_state = 0x13579BDF
    samples = array("h")
    for index in range(total_samples):
        t = index / sample_rate
        tone = 0.0
        if freq_tuple:
            for freq in freq_tuple:
                tone += math.sin(2.0 * math.pi * freq * t)
            tone /= len(freq_tuple)
        if noise_mix:
            noise_state = (1103515245 * noise_state + 12345) & 0x7FFFFFFF
            noise = ((noise_state / 0x7FFFFFFF) * 2.0) - 1.0
        else:
            noise = 0.0
        sample = tone_mix * tone + noise_mix * noise
        if index < attack:
            envelope = index / attack
        elif index >= total_samples - release:
            envelope = (total_samples - index) / release
        else:
            envelope = 1.0
        value = int(max(-1.0, min(1.0, sample * envelope * amplitude)) * 32767)
        samples.append(value)
    return samples


def _consonant_frequencies(char: str) -> tuple[float, float]:
    offset = ord(char) - 97
    base = 190.0 + (offset % 8) * 32.0
    overtone = min(base * 1.6, 760.0)
    return base, overtone


def _render_character(char: str, sample_rate: int) -> tuple[array, bool]:
    if char == " ":
        return _generate_silence(0.09, sample_rate), True
    if char in {"\n", "\r"}:
        return _generate_silence(0.14, sample_rate), True
    if char == "\t":
        return _generate_silence(0.11, sample_rate), True

    lower = char.lower()
    if lower in _VOWEL_FORMANTS:
        formants = _VOWEL_FORMANTS[lower]
        return _generate_tone(formants, 0.18, sample_rate), False
    if lower in _DIGIT_BASE_FREQUENCY:
        base = _DIGIT_BASE_FREQUENCY[lower]
        harmonics = (base, base * 1.5)
        segment = _generate_tone(
            harmonics,
            0.16,
            sample_rate,
            noise_mix=0.05,
        )
        return segment, False
    if lower in _PUNCTUATION_PROFILES:
        freq, duration, noise_mix = _PUNCTUATION_PROFILES[lower]
        segment = _generate_tone(
            (freq,),
            duration,
            sample_rate,
            noise_mix=noise_mix,
        )
        return segment, False
    if lower.isalpha():
        fundamental, overtone = _consonant_frequencies(lower)
        segment = _generate_tone(
            (fundamental, overtone),
            0.12,
            sample_rate,
            noise_mix=0.35,
        )
        return segment, False
    segment = _generate_tone((320.0,), 0.10, sample_rate, noise_mix=0.22)
    return segment, False


def synthesize_speech(text: str, *, sample_rate: int = 22_050) -> bytes:
    """Return a WAV byte stream synthesised from *text*.

    The synthesiser generates a robotic voice using basic sine-wave formants so
    Sigma can audibly read responses without external dependencies.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(sample_rate, int) or sample_rate <= 0:
        raise ValueError("sample_rate must be a positive integer")
    if not text.strip():
        raise ValueError("text must be a non-empty string")

    samples = array("h")
    prev_was_pause = True
    for char in text:
        segment, is_pause = _render_character(char, sample_rate)
        if not prev_was_pause:
            gap = _generate_silence(0.018, sample_rate)
            samples.extend(gap)
        samples.extend(segment)
        prev_was_pause = is_pause or char in _WHITESPACE_SET

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(samples.tobytes())
    return buffer.getvalue()


def save_speech(
    text: str,
    path: str | Path,
    *,
    sample_rate: int = 22_050,
) -> Path:
    """Generate *text* audio and write it to *path* as a WAV file."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = synthesize_speech(text, sample_rate=sample_rate)
    destination.write_bytes(data)
    return destination
