"""Voice Co-Pilot pipeline connecting Wake-word, STT, ReAct Task Orchestrator, and TTS."""

import asyncio
import logging
from enum import Enum
from typing import Callable, Optional
from igris.brain.planner import TaskOrchestrator
from igris.voice.capture import AudioChunk, MicrophoneCapture
from igris.voice.stt import WhisperTranscriber
from igris.voice.tts import EdgeTTSClient
from igris.voice.wake_word import VoiceActivityDetector, WakeWordDetector

logger = logging.getLogger("igris.voice.pipeline")


class VoicePipelineState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    EXECUTING = "executing"
    SPEAKING = "speaking"
    STOPPED = "stopped"


class VoiceCopilotPipeline:
    """Orchestrates hands-free voice operations: Wake-word -> STT -> ReAct Loop -> TTS."""

    def __init__(
        self,
        orchestrator: Optional[TaskOrchestrator] = None,
        mic: Optional[MicrophoneCapture] = None,
        stt: Optional[WhisperTranscriber] = None,
        tts: Optional[EdgeTTSClient] = None,
        wake_detector: Optional[WakeWordDetector] = None,
    ):
        self.orchestrator = orchestrator or TaskOrchestrator()
        self.mic = mic or MicrophoneCapture()
        self.stt = stt or WhisperTranscriber()
        self.tts = tts or EdgeTTSClient()
        self.wake_detector = wake_detector or WakeWordDetector()
        self.vad = self.wake_detector.vad
        self.state: VoicePipelineState = VoicePipelineState.IDLE
        self._is_running = False
        self._loop_task: Optional[asyncio.Task] = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    async def start(self) -> None:
        """Start background voice co-pilot pipeline."""
        if self._is_running:
            return

        self._is_running = True
        self.state = VoicePipelineState.LISTENING
        self.mic.start()
        self._loop_task = asyncio.create_task(self._pipeline_loop())
        logger.info("Voice Co-Pilot Pipeline active. Awaiting wake-word 'Hey Igris'...")

    async def _pipeline_loop(self) -> None:
        """Main listening and execution event loop."""
        try:
            while self._is_running:
                chunk = await self.mic.get_chunk(timeout=0.2)
                if not chunk:
                    await asyncio.sleep(0.01)
                    continue

                # Process chunk with VAD
                self.vad.process_chunk(chunk)

                # Check if utterance boundary detected
                if self.vad.is_utterance_complete():
                    pcm_utterance = self.vad.get_and_reset_utterance()
                    if pcm_utterance:
                        await self._process_utterance(pcm_utterance)
        except asyncio.CancelledError:
            logger.debug("Voice pipeline loop cancelled.")
            raise

    async def _process_utterance(self, pcm_data: bytes) -> None:
        """Transcribe utterance, verify wake phrase, and trigger task."""
        self.state = VoicePipelineState.TRANSCRIBING
        result = self.stt.transcribe_pcm(pcm_data)

        if result.is_empty:
            self.state = VoicePipelineState.LISTENING
            return

        spoken_text = result.full_text.strip()
        logger.info("Heard speech: '%s'", spoken_text)

        # Check for wake phrase or direct command
        if not self.wake_detector.matches_wake_phrase(spoken_text):
            logger.debug("Speech did not match wake phrase. Ignoring.")
            self.state = VoicePipelineState.LISTENING
            return

        command = self.wake_detector.strip_wake_phrase(spoken_text)
        if not command:
            # Wake word only (e.g. user said "Hey Igris")
            print("\n" + "=" * 50)
            print("✨ [WAKE-WORD DETECTED] 'Hey Igris'")
            print("🔊 Igris: 'Yes, master, how can I help you?'")
            print("=" * 50 + "\n")
            self.state = VoicePipelineState.SPEAKING
            await self.tts.speak("Yes, master, how can I help you?")
            self.state = VoicePipelineState.LISTENING
            return

        print("\n" + "=" * 50)
        print(f"✨ [VOICE COMMAND] '{command}'")
        print(f"🔊 Igris: 'Understood, master. Starting task: {command}'")
        print("=" * 50 + "\n")

        # Immediate voice feedback acknowledging task
        self.state = VoicePipelineState.SPEAKING
        await self.tts.speak(f"Understood, master. Starting task: {command}")

        # Execute task via TaskOrchestrator
        self.state = VoicePipelineState.EXECUTING
        try:
            task_result = await self.orchestrator.execute_task(
                task_goal=command,
            )

            # Post-task vocal report
            self.state = VoicePipelineState.SPEAKING
            if task_result.success:
                print("\n🔊 Igris: 'Task completed successfully, master.'\n")
                await self.tts.speak("Task completed successfully, master.")
            else:
                print(f"\n🔊 Igris: 'Task finished: {task_result.final_message}'\n")
                await self.tts.speak(f"Task finished: {task_result.final_message}")
        except Exception as e:
            logger.error("Error executing voice task: %s", e)
            self.state = VoicePipelineState.SPEAKING
            await self.tts.speak(f"An error occurred while executing the task: {e}")
        finally:
            self.state = VoicePipelineState.LISTENING

    async def stop(self) -> None:
        """Stop voice pipeline and release audio capture."""
        self._is_running = False
        self.state = VoicePipelineState.STOPPED
        self.mic.stop()
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
            self._loop_task = None
        logger.info("Voice Co-Pilot Pipeline stopped.")
