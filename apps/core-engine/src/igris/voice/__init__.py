"""Voice package for wake-word detection, speech-to-text, voice synthesis, and meeting intelligence."""

from igris.voice.capture import AudioChunk, AudioConfig, MicrophoneCapture, PipeWireLoopbackCapture
from igris.voice.wake_word import VoiceActivityDetector, WakeWordDetector
from igris.voice.stt import TranscriptionResult, TranscriptionSegment, WhisperTranscriber
from igris.voice.tts import EdgeTTSClient, TTSConfig
from igris.voice.meeting_transcriber import MeetingSummary, MeetingTranscriptEntry, MeetingTranscriber
from igris.voice.pipeline import VoiceCopilotPipeline, VoicePipelineState

__all__ = [
    "AudioChunk",
    "AudioConfig",
    "MicrophoneCapture",
    "PipeWireLoopbackCapture",
    "VoiceActivityDetector",
    "WakeWordDetector",
    "TranscriptionResult",
    "TranscriptionSegment",
    "WhisperTranscriber",
    "EdgeTTSClient",
    "TTSConfig",
    "MeetingSummary",
    "MeetingTranscriptEntry",
    "MeetingTranscriber",
    "VoiceCopilotPipeline",
    "VoicePipelineState",
]
