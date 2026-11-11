"""Speech-to-Text (STT) engine using Faster-Whisper for low-latency local transcription."""

import io
import logging
import time
from typing import List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("igris.voice.stt")


class TranscriptionSegment(BaseModel):
    """A timestamped segment of transcribed audio."""
    start: float = Field(..., description="Start timestamp in seconds")
    end: float = Field(..., description="End timestamp in seconds")
    text: str = Field(..., description="Transcribed textual phrase")
    confidence: float = Field(default=1.0, description="Average log probability or confidence score")


class TranscriptionResult(BaseModel):
    """Complete transcription output with metadata."""
    full_text: str = Field(..., description="Full transcribed text")
    language: str = Field(default="en", description="Detected or specified language code")
    duration_seconds: float = Field(default=0.0, description="Total audio duration transcribed")
    segments: List[TranscriptionSegment] = Field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not bool(self.full_text.strip())


class WhisperTranscriber:
    """High-performance local Speech-to-Text engine using Faster-Whisper (CTranslate2)."""

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        cpu_threads: int = 4,
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.cpu_threads = cpu_threads
        self._model = None

    def _ensure_model_loaded(self) -> None:
        """Lazy load Faster-Whisper model into memory."""
        if self._model is not None:
            return

        try:
            from faster_whisper import WhisperModel

            logger.info(
                "Loading Faster-Whisper model '%s' (device: %s, compute: %s)...",
                self.model_size,
                self.device,
                self.compute_type,
            )
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=self.cpu_threads,
            )
            logger.info("Faster-Whisper model '%s' loaded successfully.", self.model_size)
        except Exception as e:
            logger.error("Failed to load Faster-Whisper model: %s", e)
            raise RuntimeError(f"Could not initialize Faster-Whisper engine: {e}")

    def transcribe_pcm(
        self,
        pcm_bytes: bytes,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        """Transcribe raw 16-bit PCM mono audio bytes."""
        if not pcm_bytes:
            return TranscriptionResult(full_text="", language=language or "en", duration_seconds=0.0)

        import numpy as np

        # Convert raw s16le bytes to float32 normalized array
        audio_int16 = np.frombuffer(pcm_bytes, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0
        duration = len(audio_float32) / sample_rate

        self._ensure_model_loaded()

        start_time = time.time()
        segments_gen, info = self._model.transcribe(
            audio_float32,
            language=language,
            beam_size=5,
            vad_filter=True,
        )

        segments: List[TranscriptionSegment] = []
        collected_texts: List[str] = []

        for seg in segments_gen:
            clean_text = seg.text.strip()
            if clean_text:
                collected_texts.append(clean_text)
                segments.append(
                    TranscriptionSegment(
                        start=seg.start,
                        end=seg.end,
                        text=clean_text,
                        confidence=float(getattr(seg, "avg_logprob", 1.0)),
                    )
                )

        full_text = " ".join(collected_texts).strip()
        elapsed = time.time() - start_time
        detected_lang = getattr(info, "language", language or "en")

        logger.info(
            "Transcribed %.2fs of audio in %.2fs (Lang: %s): '%s'",
            duration,
            elapsed,
            detected_lang,
            full_text,
        )

        return TranscriptionResult(
            full_text=full_text,
            language=detected_lang,
            duration_seconds=duration,
            segments=segments,
        )

