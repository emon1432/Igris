"""Tests for audio capture layer (Microphone and PipeWire loopback)."""

import asyncio
import pytest
from igris.voice.capture import AudioChunk, AudioConfig, MicrophoneCapture, PipeWireLoopbackCapture


def test_audio_config_and_chunk_duration():
    """Verify audio chunk duration calculation from raw PCM bytes."""
    config = AudioConfig(sample_rate=16000, channels=1)
    assert config.sample_rate == 16000
    assert config.channels == 1

    # 16000 samples * 2 bytes/sample (s16le) = 32000 bytes for 1.0 second
    one_second_pcm = b"\x00" * 32000
    chunk = AudioChunk(raw_bytes=one_second_pcm, sample_rate=16000, channels=1)
    assert pytest.approx(chunk.duration_seconds, 0.01) == 1.0


@pytest.mark.asyncio
async def test_microphone_synthetic_queue():
    """Verify synthetic chunk feeding and retrieval in MicrophoneCapture."""
    mic = MicrophoneCapture()
    assert not mic.is_recording

    synthetic_pcm = b"\x05\x00" * 1024
    mic.feed_synthetic_chunk(synthetic_pcm)

    chunk = await mic.get_chunk(timeout=0.5)
    assert chunk is not None
    assert chunk.raw_bytes == synthetic_pcm
    assert chunk.sample_rate == 16000


@pytest.mark.asyncio
async def test_pipewire_loopback_synthetic_queue():
    """Verify PipeWire loopback synthetic buffer and lifecycle."""
    pw = PipeWireLoopbackCapture()
    assert not pw.is_recording

    sample_pcm = b"\x10\x00" * 512
    pw.feed_synthetic_chunk(sample_pcm)

    chunk = await pw.get_chunk(timeout=0.5)
    assert chunk is not None
    assert chunk.raw_bytes == sample_pcm

    await pw.stop()
    assert not pw.is_recording

