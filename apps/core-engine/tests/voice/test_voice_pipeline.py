"""Tests for VoiceCopilotPipeline orchestrator."""

import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest
from igris.brain.planner import TaskExecutionSummary
from igris.voice.capture import AudioChunk, MicrophoneCapture
from igris.voice.pipeline import VoiceCopilotPipeline, VoicePipelineState
from igris.voice.stt import TranscriptionResult, WhisperTranscriber
from igris.voice.tts import EdgeTTSClient
from igris.voice.wake_word import WakeWordDetector


@pytest.mark.asyncio
async def test_voice_pipeline_wake_and_execute():
    """Verify voice pipeline detects wake word, executes task, and provides TTS feedback."""
    mock_orchestrator = MagicMock()
    mock_orchestrator.execute_task = AsyncMock(
        return_value=TaskExecutionSummary(
            task_goal="open terminal",
            success=True,
            total_steps=2,
            duration_seconds=1.2,
            final_message="Terminal opened successfully",
        )
    )

    mock_stt = MagicMock(spec=WhisperTranscriber)
    mock_stt.transcribe_pcm.return_value = TranscriptionResult(
        full_text="Hey Igris, open terminal",
        language="en",
    )

    mock_tts = MagicMock(spec=EdgeTTSClient)
    mock_tts.speak = AsyncMock(return_value=True)

    mic = MicrophoneCapture()
    pipeline = VoiceCopilotPipeline(
        orchestrator=mock_orchestrator,
        mic=mic,
        stt=mock_stt,
        tts=mock_tts,
    )

    # Process simulated utterance directly
    await pipeline._process_utterance(b"\x00" * 32000)

    # Check that orchestrator was called with stripped goal
    mock_orchestrator.execute_task.assert_awaited_once_with(
        task_goal="open terminal",
    )

    # Check TTS announcements (starting acknowledgment + task complete)
    assert mock_tts.speak.await_count == 2
    mock_tts.speak.assert_any_await("Understood. Starting task: open terminal")
    mock_tts.speak.assert_any_await("Task completed successfully.")
    assert pipeline.state == VoicePipelineState.LISTENING
