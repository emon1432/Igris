"""Tests for MeetingTranscriber and Meeting Intelligence."""

from unittest.mock import MagicMock
import pytest
from igris.voice.capture import AudioChunk
from igris.voice.meeting_transcriber import MeetingTranscriber, MeetingTranscriptEntry
from igris.voice.stt import TranscriptionResult, TranscriptionSegment


@pytest.mark.asyncio
async def test_meeting_transcriber_lifecycle():
    """Verify meeting transcriber buffering, transcription, and summary generation."""
    mock_transcriber = MagicMock()
    # Mock STT output
    mock_seg = TranscriptionSegment(start=1.0, end=4.0, text="We should refactor the perception engine", confidence=0.95)
    mock_transcriber.transcribe_pcm.return_value = TranscriptionResult(
        full_text="We should refactor the perception engine",
        language="en",
        segments=[mock_seg],
    )

    mt = MeetingTranscriber(
        transcriber=mock_transcriber,
        chunk_window_seconds=0.1,  # short window for test
        sample_rate=16000,
    )
    mt.start()
    assert mt.is_active

    # Feed 0.2s of audio (3200 samples = 6400 bytes)
    chunk = AudioChunk(raw_bytes=b"\x00" * 6400, sample_rate=16000)
    mt.add_audio_chunk(chunk)

    entries = mt.process_pending_audio()
    assert len(entries) == 1
    assert "refactor the perception engine" in entries[0].text

    full_text = mt.get_full_transcript_text()
    assert "refactor the perception engine" in full_text

    # Generate summary without Gemini API (deterministic fallback)
    summary = await mt.generate_summary(title="Sprint Planning Meeting", gemini_api_key="")
    assert summary.title == "Sprint Planning Meeting"
    assert len(summary.key_discussion_points) >= 1
    assert "refactor the perception engine" in summary.key_discussion_points[0]
    assert len(summary.action_items) >= 1

    mt.stop()
    assert not mt.is_active

