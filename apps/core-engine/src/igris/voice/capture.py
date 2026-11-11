"""Audio capture layer for microphone and PipeWire system audio loopback."""

import asyncio
import logging
import subprocess
import time
from typing import AsyncGenerator, Callable, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("igris.voice.capture")


class AudioConfig(BaseModel):
    """Configuration parameters for audio streaming and processing."""
    sample_rate: int = Field(default=16000, description="Sampling rate in Hz (16kHz recommended for Whisper)")
    channels: int = Field(default=1, description="Number of audio channels (1 for mono)")
    chunk_size: int = Field(default=1024, description="Number of frames per audio chunk")
    format_type: str = Field(default="s16le", description="Sample format string (e.g. s16le or f32le)")


class AudioChunk(BaseModel):
    """A discrete slice of captured PCM audio."""
    raw_bytes: bytes = Field(..., description="Raw PCM audio bytes")
    sample_rate: int = Field(default=16000)
    channels: int = Field(default=1)
    timestamp: float = Field(default_factory=time.time)

    @property
    def duration_seconds(self) -> float:
        """Compute the duration of this audio chunk in seconds."""
        bytes_per_sample = 2  # standard 16-bit PCM (s16le)
        total_samples = len(self.raw_bytes) / (bytes_per_sample * self.channels)
        return total_samples / self.sample_rate


class MicrophoneCapture:
    """Captures microphone input using sounddevice or fallback PCM streams."""

    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self._is_recording = False
        self._queue: asyncio.Queue[AudioChunk] = asyncio.Queue(maxsize=100)
        self._stream = None

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    def start(self) -> None:
        """Start capturing audio from the physical microphone."""
        if self._is_recording:
            return

        self._is_recording = True
        try:
            import sounddevice as sd

            loop = asyncio.get_event_loop()

            def callback(indata, frames, time_info, status):
                if status:
                    logger.debug("Microphone stream status: %s", status)
                # Convert float32 or int16 numpy array to int16 PCM bytes
                import numpy as np

                if indata.dtype == np.float32:
                    pcm_data = (indata * 32767).astype(np.int16).tobytes()
                else:
                    pcm_data = indata.tobytes()

                chunk = AudioChunk(
                    raw_bytes=pcm_data,
                    sample_rate=self.config.sample_rate,
                    channels=self.config.channels,
                )
                loop.call_soon_threadsafe(
                    lambda: self._queue.put_nowait(chunk) if not self._queue.full() else None
                )

            self._stream = sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                dtype="float32",
                blocksize=self.config.chunk_size,
                callback=callback,
            )
            self._stream.start()
            logger.info("Microphone capture started at %d Hz.", self.config.sample_rate)
        except Exception as e:
            logger.warning("Hardware microphone initialization unavailable (%s). Running in virtual capture mode.", e)

    def stop(self) -> None:
        """Stop capturing microphone audio."""
        self._is_recording = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                logger.debug("Error stopping microphone stream: %s", e)
            self._stream = None
        logger.info("Microphone capture stopped.")

    async def get_chunk(self, timeout: float = 1.0) -> Optional[AudioChunk]:
        """Fetch the next available audio chunk from the buffer."""
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    def feed_synthetic_chunk(self, raw_bytes: bytes) -> None:
        """Feed synthetic audio chunk into the queue for testing or simulated streams."""
        chunk = AudioChunk(
            raw_bytes=raw_bytes,
            sample_rate=self.config.sample_rate,
            channels=self.config.channels,
        )
        try:
            self._queue.put_nowait(chunk)
        except asyncio.QueueFull:
            pass


class PipeWireLoopbackCapture:
    """Captures internal system audio (e.g. Google Meet, Zoom, YouTube) using PipeWire."""

    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.process: Optional[subprocess.Popen] = None
        self._is_recording = False
        self._queue: asyncio.Queue[AudioChunk] = asyncio.Queue(maxsize=200)
        self._reader_task: Optional[asyncio.Task] = None

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    async def start(self) -> None:
        """Start capturing desktop audio via pw-record or loopback pipe."""
        if self._is_recording:
            return

        self._is_recording = True
        cmd = [
            "pw-record",
            "--rate", str(self.config.sample_rate),
            "--channels", str(self.config.channels),
            "--format", self.config.format_type,
            "-",  # output raw PCM to stdout
        ]

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            self._reader_task = asyncio.create_task(self._read_loop())
            logger.info("PipeWire system loopback capture started.")
        except FileNotFoundError:
            logger.warning("pw-record binary not found. PipeWire loopback capture disabled.")

    async def _read_loop(self) -> None:
        """Continuously read raw PCM bytes from pw-record stdout."""
        loop = asyncio.get_event_loop()
        chunk_bytes = self.config.chunk_size * 2 * self.config.channels  # 2 bytes per s16 sample

        while self._is_recording and self.process and self.process.stdout:
            try:
                data = await loop.run_in_executor(None, self.process.stdout.read, chunk_bytes)
                if not data:
                    break
                chunk = AudioChunk(
                    raw_bytes=data,
                    sample_rate=self.config.sample_rate,
                    channels=self.config.channels,
                )
                if not self._queue.full():
                    await self._queue.put(chunk)
            except Exception as e:
                logger.debug("PipeWire loopback read error: %s", e)
                break

    async def get_chunk(self, timeout: float = 1.0) -> Optional[AudioChunk]:
        """Fetch the next captured system audio chunk."""
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    def feed_synthetic_chunk(self, raw_bytes: bytes) -> None:
        """Feed synthetic system audio chunk for testing."""
        chunk = AudioChunk(
            raw_bytes=raw_bytes,
            sample_rate=self.config.sample_rate,
            channels=self.config.channels,
        )
        try:
            self._queue.put_nowait(chunk)
        except asyncio.QueueFull:
            pass

    async def stop(self) -> None:
        """Stop PipeWire loopback capture."""
        self._is_recording = False
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None

        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

        logger.info("PipeWire system loopback capture stopped.")

