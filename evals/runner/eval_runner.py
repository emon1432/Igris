"""Igris Evaluation Test Suite Runner.

Executes all core safety, security, and policy evaluation cases (P-01 to M-01)
and produces a structured verification scorecard.
"""

import sys
import subprocess
from pathlib import Path


def run_evals():
    cases_dir = Path(__file__).parent.parent / "cases"
    print("=" * 60)
    print("       IGRIS SAFETY & POLICY EVALUATION SUITE (P-01 - M-01)   ")
    print("=" * 60)
    print(f"Target Cases Directory: {cases_dir}\n")

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(cases_dir),
        "-v",
        "--tb=short",
    ]

    result = subprocess.run(cmd)
    print("\n" + "=" * 60)
    if result.returncode == 0:
        print(" [PASS] ALL EVALUATION CASES PASSED ACCORDING TO SPECIFICATION ")
    else:
        print(" [FAIL] ONE OR MORE EVALUATION CASES FAILED ")
    print("=" * 60)
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_evals())
