"""Wake-word detection and Voice Activity Detection (VAD) for Igris voice pipeline."""

import logging
import math
import struct
import time
from typing import List, Optional
from igris.voice.capture import AudioChunk

logger = logging.getLogger("igris.voice.wake_word")


class VoiceActivityDetector:
    """Energy-based Voice Activity Detector (VAD) for real-time speech boundary detection."""

    def __init__(
        self,
        energy_threshold: float = 300.0,
        silence_timeout_seconds: float = 1.2,
        min_speech_duration_seconds: float = 0.3,
    ):
        self.energy_threshold = energy_threshold
        self.silence_timeout_seconds = silence_timeout_seconds
        self.min_speech_duration_seconds = min_speech_duration_seconds
        self._is_speaking = False
        self._speech_start_time: Optional[float] = None
        self._last_speech_time: Optional[float] = None
        self._accumulated_speech_chunks: List[AudioChunk] = []

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking

    @staticmethod
    def calculate_rms(raw_bytes: bytes) -> float:
        """Calculate Root Mean Square (RMS) energy of 16-bit PCM audio."""
        if not raw_bytes or len(raw_bytes) < 2:
            return 0.0

        # Unpack 16-bit signed integers (little-endian)
        num_samples = len(raw_bytes) // 2
        fmt = f"<{num_samples}h"
        try:
            samples = struct.unpack(fmt, raw_bytes[:num_samples * 2])
        except struct.error:
            return 0.0

        if not samples:
            return 0.0

        sum_squares = sum(s * s for s in samples)
        mean_squares = sum_squares / num_samples
        return math.sqrt(mean_squares)

    def process_chunk(self, chunk: AudioChunk) -> bool:
        """Process an incoming audio chunk and return True if currently speaking."""
        rms = self.calculate_rms(chunk.raw_bytes)
        now = time.time()

        if rms >= self.energy_threshold:
            if not self._is_speaking:
                self._is_speaking = True
                self._speech_start_time = now
                logger.debug("Speech activity started (RMS: %.1f)", rms)
            self._last_speech_time = now
            self._accumulated_speech_chunks.append(chunk)
            return True
        else:
            if self._is_speaking:
                # Keep accumulating slight pauses between words
                self._accumulated_speech_chunks.append(chunk)
            return False

    def is_utterance_complete(self) -> bool:
        """Check if an ongoing speech utterance has completed after silence threshold."""
        if not self._is_speaking or self._last_speech_time is None or self._speech_start_time is None:
            return False

        now = time.time()
        silence_duration = now - self._last_speech_time
        total_duration = sum(c.duration_seconds for c in self._accumulated_speech_chunks)

        if silence_duration >= self.silence_timeout_seconds and total_duration >= self.min_speech_duration_seconds:
            logger.debug(
                "Utterance complete (duration: %.2fs, silence: %.2fs).",
                total_duration,
                silence_duration,
            )
            return True

        return False

    def get_and_reset_utterance(self) -> bytes:
        """Extract accumulated speech PCM bytes and reset VAD state."""
        combined_bytes = b"".join(c.raw_bytes for c in self._accumulated_speech_chunks)
        self.reset()
        return combined_bytes

    def reset(self) -> None:
        """Reset internal state."""
        self._is_speaking = False
        self._speech_start_time = None
        self._last_speech_time = None
        self._accumulated_speech_chunks.clear()


class WakeWordDetector:
    """Monitors incoming audio stream and matches activation phrases."""

    DEFAULT_WAKE_WORDS = ["hey igris", "igris", "hello igris", "ok igris"]

    def __init__(
        self,
        wake_words: Optional[List[str]] = None,
        vad: Optional[VoiceActivityDetector] = None,
    ):
        self.wake_words = [w.lower().strip() for w in (wake_words or self.DEFAULT_WAKE_WORDS)]
        self.vad = vad or VoiceActivityDetector()

    def matches_wake_phrase(self, text: str) -> bool:
        """Check if transcribed text contains any of the target wake phrases."""
        clean = text.lower().strip()
        for phrase in self.wake_words:
            if phrase in clean:
                return True
        return False

    def strip_wake_phrase(self, text: str) -> str:
        """Remove matched wake phrase from transcribed command string while preserving original casing."""
        lower_text = text.lower()
        for phrase in self.wake_words:
            if phrase in lower_text:
                idx = lower_text.find(phrase)
                after = text[idx + len(phrase):].strip(" ,.:;!?")
                return after.strip()
        return text.strip()
