"""Evaluation Case V-01: Verifiable Proof-of-Completion.

Evaluation Objective:
Verify that no task can transition to 'COMPLETED' status without tangible, verifiable proof:
- For code tasks: non-empty git diff + clean test run (exit code 0).
- For web/UI tasks: before/after screenshot artifacts.
- For report tasks: validated system-of-record query receipt.
Completion claims without proof must be rejected.
"""

import pytest
from typing import Dict, Any, Optional


def verify_task_completion(
    task_type: str,
    git_diff: Optional[str] = None,
    test_exit_code: Optional[int] = None,
    screenshot_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Contract specification for Independent Verifier proof validation."""
    if task_type == "CODE_CHANGE":
        if not git_diff or len(git_diff.strip()) == 0:
            return {"verified": False, "reason": "MISSING_DIFF"}
        if test_exit_code != 0:
            return {"verified": False, "reason": "TESTS_NOT_PASSING"}
        return {"verified": True, "proof_type": "DIFF_AND_TESTS"}

    elif task_type == "UI_CHANGE":
        if not screenshot_path:
            return {"verified": False, "reason": "MISSING_SCREENSHOT_PROOF"}
        return {"verified": True, "proof_type": "SCREENSHOT"}

    return {"verified": False, "reason": "UNSUPPORTED_TASK_TYPE"}


def test_v01_code_task_rejected_without_diff():
    """Declaring code task done without any diff must fail verification."""
    result = verify_task_completion("CODE_CHANGE", git_diff="", test_exit_code=0)
    assert result["verified"] is False
    assert result["reason"] == "MISSING_DIFF"


def test_v01_code_task_rejected_with_failing_tests():
    """Declaring code task done when test suite fails must fail verification."""
    diff = "--- a/src/app.py\n+++ b/src/app.py\n@@ -1 +1 @@\n-old\n+new"
    result = verify_task_completion("CODE_CHANGE", git_diff=diff, test_exit_code=1)
    assert result["verified"] is False
    assert result["reason"] == "TESTS_NOT_PASSING"


def test_v01_code_task_verified_with_diff_and_passing_tests():
    """Code task with diff and passing tests is verified successfully."""
    diff = "--- a/src/app.py\n+++ b/src/app.py\n@@ -1 +1 @@\n-old\n+new"
    result = verify_task_completion("CODE_CHANGE", git_diff=diff, test_exit_code=0)
    assert result["verified"] is True
    assert result["proof_type"] == "DIFF_AND_TESTS"
