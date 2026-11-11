"""Command Line Interface for Igris Autonomous OS Operator."""

import argparse
import asyncio
import logging
import sys

from igris.action.virtual_display import VirtualDisplayManager
from igris.brain.planner import TaskOrchestrator
from igris.core.config import AppConfig
from igris.core.state import ExecutionMode, RuntimeState


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
    else:
        print("• Standby: Ready for incoming voice or remote socket commands.")


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
