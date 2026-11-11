"""Tests for Wake-word detection and Voice Activity Detection (VAD)."""

import math
import struct
import time
import pytest
from igris.voice.capture import AudioChunk
from igris.voice.wake_word import VoiceActivityDetector, WakeWordDetector


def generate_sine_pcm(freq: float = 440.0, duration: float = 0.5, amplitude: float = 10000.0) -> bytes:
    """Generate raw 16-bit mono PCM sine wave."""
    sample_rate = 16000
    num_samples = int(duration * sample_rate)
    samples = []
    for i in range(num_samples):
        val = int(amplitude * math.sin(2.0 * math.pi * freq * (i / sample_rate)))
        samples.append(val)
    return struct.pack(f"<{num_samples}h", *samples)


def test_vad_rms_calculation():
    """Verify RMS energy calculation on silence vs loud audio."""
    silence = b"\x00" * 2000
    rms_silence = VoiceActivityDetector.calculate_rms(silence)
    assert rms_silence == 0.0

    loud_audio = generate_sine_pcm(freq=440.0, amplitude=15000.0)
    rms_loud = VoiceActivityDetector.calculate_rms(loud_audio)
    assert rms_loud > 5000.0


def test_vad_speech_accumulation_and_timeout():
    """Verify speech detection, accumulation, and utterance completion."""
    vad = VoiceActivityDetector(
        energy_threshold=500.0,
        silence_timeout_seconds=0.2,
        min_speech_duration_seconds=0.1,
    )

    # 1. Feed silence
    silence_chunk = AudioChunk(raw_bytes=b"\x00" * 2048)
    assert not vad.process_chunk(silence_chunk)
    assert not vad.is_speaking

    # 2. Feed speech
    speech_pcm = generate_sine_pcm(duration=0.2, amplitude=8000.0)
    speech_chunk = AudioChunk(raw_bytes=speech_pcm)
    assert vad.process_chunk(speech_chunk)
    assert vad.is_speaking

    # 3. Simulate silence pause for >= 0.2s
    time.sleep(0.25)
    assert vad.is_utterance_complete()

    utterance = vad.get_and_reset_utterance()
    assert len(utterance) >= len(speech_pcm)
    assert not vad.is_speaking


def test_wake_word_phrase_matching():
    """Verify wake phrase detection and strip logic."""
    detector = WakeWordDetector(wake_words=["hey igris", "igris"])

    assert detector.matches_wake_phrase("Hey Igris, open YouTube")
    assert detector.matches_wake_phrase("igris, summarize the meeting")
    assert not detector.matches_wake_phrase("hello assistant, what time is it")

    clean_cmd = detector.strip_wake_phrase("Hey Igris, open YouTube")
    assert clean_cmd == "open YouTube"

    clean_cmd2 = detector.strip_wake_phrase("igris: take a screenshot")
    assert clean_cmd2 == "take a screenshot"

