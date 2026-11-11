"""Tests for Speech-to-Text (STT) transcription engine."""

from unittest.mock import MagicMock, patch
import pytest
from igris.voice.stt import (
    TranscriptionResult,
    TranscriptionSegment,
    WhisperTranscriber,
)


def test_transcription_result_model():
    """Verify transcription result properties."""
    seg1 = TranscriptionSegment(start=0.0, end=1.5, text="Hello Igris", confidence=0.98)
    res = TranscriptionResult(
        full_text="Hello Igris",
        language="en",
        duration_seconds=1.5,
        segments=[seg1],
    )
    assert not res.is_empty
    assert res.full_text == "Hello Igris"
    assert len(res.segments) == 1
    assert res.segments[0].confidence == 0.98

    empty_res = TranscriptionResult(full_text="   ", language="en")
    assert empty_res.is_empty


def test_whisper_transcribe_empty_pcm():
    """Verify empty audio yields empty result without loading model."""
    transcriber = WhisperTranscriber()
    res = transcriber.transcribe_pcm(b"")
    assert res.is_empty
    assert res.duration_seconds == 0.0


def test_whisper_transcription_mocked():
    """Verify transcription processing with mocked Faster-Whisper model."""
    transcriber = WhisperTranscriber(model_size="base")

    # Mock Faster-Whisper return generator
    mock_seg = MagicMock()
    mock_seg.start = 0.5
    mock_seg.end = 2.0
    mock_seg.text = "open terminal"
    mock_seg.avg_logprob = -0.15

    mock_info = MagicMock()
    mock_info.language = "en"

    mock_model = MagicMock()
    mock_model.transcribe.return_value = ([mock_seg], mock_info)
    transcriber._model = mock_model

    # 16000 samples of 16-bit PCM = 32000 bytes
    dummy_pcm = b"\x00" * 32000
    res = transcriber.transcribe_pcm(dummy_pcm)

    assert not res.is_empty
    assert res.full_text == "open terminal"
    assert res.language == "en"
    assert len(res.segments) == 1
    assert res.segments[0].text == "open terminal"
    assert res.segments[0].confidence == -0.15

