"""Command Line Interface for Igris."""

import argparse
import sys
from igris.core.config import AppConfig
from igris.core.state import RuntimeState, ExecutionMode


def main():
    parser = argparse.ArgumentParser(description="Igris: Universal Autonomous OS Operator")
    parser.add_argument("--mode", choices=["live", "ghost"], default="ghost", help="Execution mode (default: ghost)")
    parser.add_argument("--task", type=str, help="Single task to execute")
    parser.add_argument("--config", type=str, default="config/default_config.yaml", help="Path to config file")

    args = parser.parse_args()
    config = AppConfig.load(args.config)
    state = RuntimeState(
        current_mode=ExecutionMode(args.mode),
        active_display=config.displays.virtual if args.mode == "ghost" else config.displays.primary
    )

    print(f"✨ Igris OS Operator Initialized")
    print(f"• Execution Mode: {state.current_mode.value.upper()}")
    print(f"• Target Display: {state.active_display}")

    if args.task:
        print(f"• Executing Task: {args.task}")
    else:
        print("• Ready for voice or remote inputs.")


if __name__ == "__main__":
    main()
