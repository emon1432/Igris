"""Command Line Interface for Igris Autonomous OS Operator."""

import argparse
import asyncio
import logging
import sys

from igris.brain.planner import TaskOrchestrator
from igris.core.config import AppConfig
from igris.core.state import ExecutionMode
from igris.voice.capture import PipeWireLoopbackCapture
from igris.voice.meeting_transcriber import MeetingTranscriber
from igris.voice.pipeline import VoiceCopilotPipeline


def setup_logging(verbose: bool = False) -> None:
    """Configure terminal logging format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


async def async_main():
    parser = argparse.ArgumentParser(description="Igris: Universal Autonomous OS Operator")
    parser.add_argument("--mode", choices=["live", "ghost"], default="ghost", help="Execution mode (default: ghost)")
    parser.add_argument("--task", type=str, help="Single autonomous task instruction to execute")
    parser.add_argument("--voice", action="store_true", help="Start hands-free Voice Co-Pilot mode")
    parser.add_argument("--record-meeting", action="store_true", help="Capture and transcribe meeting audio via PipeWire")
    parser.add_argument("--meeting-duration", type=float, default=30.0, help="Meeting recording duration in seconds")
    parser.add_argument("--config", type=str, default="config/default_config.yaml", help="Path to config file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose debug logs")

    args = parser.parse_args()
    setup_logging(args.verbose)

    config = AppConfig.load(args.config)
    mode = ExecutionMode(args.mode)

    print("==================================================")
    print("        IGRIS AUTONOMOUS OS OPERATOR              ")
    print("==================================================")
    print(f"• Target Mode:   {mode.value.upper()}")
    print(f"• Virtual Server: {config.displays.virtual} ({config.displays.virtual_width}x{config.displays.virtual_height})")

    if args.task:
        print(f"• Initiating Task: '{args.task}'")
        orchestrator = TaskOrchestrator()
        summary = await orchestrator.execute_task(task_goal=args.task, mode=mode)

        print("\n---------------- TASK SUMMARY ----------------")
        print(f"Status:   {'SUCCESS' if summary.success else 'FAILED'}")
        print(f"Steps:    {summary.total_steps}")
        print(f"Duration: {summary.duration_seconds:.2f}s")
        print(f"Message:  {summary.final_message}")
        print("----------------------------------------------")
        sys.exit(0 if summary.success else 1)

    elif args.voice:
        print("• Starting Voice Co-Pilot Mode (Say 'Hey Igris' to speak commands)...")
        pipeline = VoiceCopilotPipeline()
        await pipeline.start()
        try:
            while pipeline.is_running:
                await asyncio.sleep(0.5)
        except (KeyboardInterrupt, asyncio.CancelledError):
            print("\n• Stopping Voice Co-Pilot Pipeline...")
            await pipeline.stop()

    elif args.record_meeting:
        print(f"• Starting PipeWire Meeting Audio Capture ({args.meeting_duration}s)...")
        pipewire = PipeWireLoopbackCapture()
        transcriber = MeetingTranscriber()
        await pipewire.start()
        transcriber.start()

        start_time = asyncio.get_event_loop().time()
        try:
            while asyncio.get_event_loop().time() - start_time < args.meeting_duration:
                chunk = await pipewire.get_chunk(timeout=0.5)
                if chunk:
                    transcriber.add_audio_chunk(chunk)
                transcriber.process_pending_audio()
        except KeyboardInterrupt:
            print("\n• Meeting recording manually interrupted.")
        finally:
            await pipewire.stop()
            transcriber.stop()

        print("\n---------------- GENERATING MEETING SUMMARY ----------------")
        summary = await transcriber.generate_summary(title="Recorded Desktop Meeting")
        print(f"Title:    {summary.title}")
        print(f"Duration: {summary.meeting_duration_minutes:.2f} mins")
        print(f"Summary:  {summary.executive_summary}")
        if summary.action_items:
            print("Action Items:")
            for item in summary.action_items:
                print(f" - {item}")
        print("------------------------------------------------------------")

    else:
        print("• Standby: Ready for incoming voice or remote socket commands.")


def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nExiting Igris.")


if __name__ == "__main__":
    main()
