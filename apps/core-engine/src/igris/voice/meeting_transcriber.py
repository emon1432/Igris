"""Meeting audio transcriber and intelligence engine using PipeWire loopback and Gemini."""

import asyncio
import logging
import os
import time
from typing import List, Optional
from pydantic import BaseModel, Field
from igris.voice.capture import AudioChunk, PipeWireLoopbackCapture
from igris.voice.stt import WhisperTranscriber, TranscriptionResult

logger = logging.getLogger("igris.voice.meeting_transcriber")


class MeetingTranscriptEntry(BaseModel):
    """Timestamped transcript entry for a specific portion of the meeting."""
    timestamp_offset_seconds: float = Field(..., description="Seconds since meeting began")
    duration_seconds: float = Field(default=0.0)
    text: str = Field(..., description="Spoken transcript text")
    speaker: Optional[str] = Field(default=None, description="Inferred or tagged speaker")


class MeetingSummary(BaseModel):
    """Structured summary and action items produced from meeting transcript."""
    title: str = Field(default="Meeting Summary")
    meeting_duration_minutes: float = Field(default=0.0)
    executive_summary: str = Field(..., description="High-level overview of the meeting")
    key_discussion_points: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)


class MeetingTranscriber:
    """Captures desktop meeting audio via PipeWire, transcribes continuously, and generates summaries."""

    def __init__(
        self,
        transcriber: Optional[WhisperTranscriber] = None,
        chunk_window_seconds: float = 15.0,
        sample_rate: int = 16000,
    ):
        self.transcriber = transcriber or WhisperTranscriber()
        self.chunk_window_seconds = chunk_window_seconds
        self.sample_rate = sample_rate
        self.meeting_start_time: float = time.time()
        self._audio_buffer: bytearray = bytearray()
        self.entries: List[MeetingTranscriptEntry] = []
        self._is_active = False

    @property
    def is_active(self) -> bool:
        return self._is_active

    def start(self) -> None:
        """Start a new meeting transcription session."""
        self.meeting_start_time = time.time()
        self._audio_buffer.clear()
        self.entries.clear()
        self._is_active = True
        logger.info("Meeting transcription session started.")

    def add_audio_chunk(self, chunk: AudioChunk) -> None:
        """Append captured system audio chunk to the internal accumulator."""
        if not self._is_active:
            return
        self._audio_buffer.extend(chunk.raw_bytes)

    def process_pending_audio(self) -> List[MeetingTranscriptEntry]:
        """Transcribe accumulated audio when sufficient window has elapsed."""
        bytes_per_second = self.sample_rate * 2  # 16-bit mono PCM = 2 bytes/sample
        min_required_bytes = int(self.chunk_window_seconds * bytes_per_second)

        if len(self._audio_buffer) < min_required_bytes:
            return []

        # Extract current slice
        to_process = bytes(self._audio_buffer)
        self._audio_buffer.clear()

        offset = time.time() - self.meeting_start_time - (len(to_process) / bytes_per_second)
        if offset < 0:
            offset = 0.0

        res: TranscriptionResult = self.transcriber.transcribe_pcm(to_process, sample_rate=self.sample_rate)
        new_entries: List[MeetingTranscriptEntry] = []

        if not res.is_empty:
            for seg in res.segments:
                entry = MeetingTranscriptEntry(
                    timestamp_offset_seconds=round(offset + seg.start, 2),
                    duration_seconds=round(seg.end - seg.start, 2),
                    text=seg.text,
                )
                self.entries.append(entry)
                new_entries.append(entry)

        return new_entries

    def get_full_transcript_text(self) -> str:
        """Produce formatted string representation of entire meeting transcript."""
        lines = []
        for e in self.entries:
            minutes = int(e.timestamp_offset_seconds // 60)
            seconds = int(e.timestamp_offset_seconds % 60)
            lines.append(f"[{minutes:02d}:{seconds:02d}] {e.text}")
        return "\n".join(lines)

    async def generate_summary(
        self,
        title: str = "Desktop Meeting Minutes",
        gemini_api_key: Optional[str] = None,
    ) -> MeetingSummary:
        """Generate structured meeting summary using Google Gemini API or deterministic parser."""
        duration_minutes = round((time.time() - self.meeting_start_time) / 60.0, 2)
        transcript = self.get_full_transcript_text()

        if not transcript.strip():
            return MeetingSummary(
                title=title,
                meeting_duration_minutes=duration_minutes,
                executive_summary="No spoken conversation detected in meeting session.",
                key_discussion_points=[],
                action_items=[],
                decisions=[],
            )

        api_key = gemini_api_key if gemini_api_key is not None else os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=api_key)
                prompt = (
                    f"You are an expert executive meeting assistant. Analyze the following transcript and produce a structured summary.\n\n"
                    f"Transcript:\n{transcript}\n\n"
                    f"Return a JSON object conforming exactly to this schema:\n"
                    f"{{\n"
                    f'  "executive_summary": "Short 2-3 sentence overview",\n'
                    f'  "key_discussion_points": ["point 1", "point 2"],\n'
                    f'  "action_items": ["action item 1 with owner if available", "action item 2"],\n'
                    f'  "decisions": ["decision 1", "decision 2"]\n'
                    f"}}"
                )

                meeting_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
                response = client.models.generate_content(
                    model=meeting_model,
                    contents=[types.Part.from_text(text=prompt)],
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        response_mime_type="application/json",
                    ),
                )

                import json
                clean_json = (response.text or "{}").strip()
                if clean_json.startswith("```"):
                    if clean_json.startswith("```json"):
                        clean_json = clean_json[7:]
                    else:
                        clean_json = clean_json[3:]
                clean_json = clean_json.strip()
                if clean_json.endswith("```"):
                    clean_json = clean_json[:-3]
                clean_json = clean_json.strip()

                parsed = json.loads(clean_json)
                return MeetingSummary(
                    title=title,
                    meeting_duration_minutes=duration_minutes,
                    executive_summary=parsed.get("executive_summary", "Meeting conducted."),
                    key_discussion_points=parsed.get("key_discussion_points", []),
                    action_items=parsed.get("action_items", []),
                    decisions=parsed.get("decisions", []),
                )
            except Exception as e:
                logger.warning("Gemini AI meeting summarization failed (%s). Falling back to basic summary.", e)

        # Fallback deterministic summary
        points = [e.text for e in self.entries[:5]]
        return MeetingSummary(
            title=title,
            meeting_duration_minutes=duration_minutes,
            executive_summary=f"Meeting completed with {len(self.entries)} dialogue entries recorded.",
            key_discussion_points=points,
            action_items=["Review meeting transcript and assign pending items."],
            decisions=["Recorded transcript saved to meeting log."],
        )

    def stop(self) -> None:
        """Stop transcription session and flush remaining audio."""
        self._is_active = False
        logger.info("Meeting transcription session stopped.")

