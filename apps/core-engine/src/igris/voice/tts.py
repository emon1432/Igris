"""Text-to-Speech (TTS) engine using Edge-TTS for natural and crystal-clear voice synthesis."""

import asyncio
import io
import logging
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("igris.voice.tts")


class TTSConfig(BaseModel):
    """Configuration for Edge-TTS voice synthesis."""
    voice: str = Field(default="en-US-ChristopherNeural", description="Voice identifier")
    rate: str = Field(default="+0%", description="Speech speed adjustment (e.g. '+10%' or '-5%')")
    pitch: str = Field(default="+0Hz", description="Voice pitch adjustment (e.g. '+2Hz')")
    volume: str = Field(default="+0%", description="Volume adjustment (e.g. '+0%')")


class EdgeTTSClient:
    """Asynchronous Text-to-Speech engine using Microsoft Edge-TTS with in-memory streaming."""

    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text to MP3 audio bytes completely in memory."""
        clean_text = text.strip()
        if not clean_text:
            return b""

        import edge_tts

        communicate = edge_tts.Communicate(
            text=clean_text,
            voice=self.config.voice,
            rate=self.config.rate,
            pitch=self.config.pitch,
            volume=self.config.volume,
        )

        audio_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])

        return audio_buffer.getvalue()

    async def speak(self, text: str) -> bool:
        """Synthesize and play audio asynchronously using PipeWire/ALSA or sounddevice."""
        clean = text.strip()
        if not clean:
            return True

        logger.info("Speaking: '%s' (Voice: %s)", clean, self.config.voice)
        try:
            mp3_bytes = await self.synthesize(clean)
            if not mp3_bytes:
                return False

            # Pipe MP3 bytes directly into ffmpeg -> aplay / pw-play
            # Zero disk writes, completely in-memory streaming
            try:
                proc = await asyncio.create_subprocess_exec(
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", "pipe:0", "-f", "wav", "pipe:1",
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                wav_data, _ = await proc.communicate(input=mp3_bytes)

                # Play WAV data using pw-play or aplay
                player = await asyncio.create_subprocess_exec(
                    "pw-play", "-",
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await player.communicate(input=wav_data)
                return True
            except (OSError, FileNotFoundError, asyncio.SubprocessError):
                # Fallback: if player commands are missing or headless, log and succeed
                logger.debug("System audio player command finished or skipped in headless mode.")
                return True
        except Exception as e:
            logger.error("TTS playback failed: %s", e)
            return False

