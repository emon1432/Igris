"""Evaluation Case V-01: Verifiable Proof-of-Completion.

Evaluation Objective:
Verify that no task can be marked 'COMPLETED' without tangible, verifiable proof audited
by the IndependentTaskVerifier. Completion claims lacking diffs or with failing tests must be rejected.
"""

import pytest
from igris.brain.verifier import IndependentTaskVerifier


def test_v01_code_task_rejected_without_diff():
    """Declaring code task done without any diff must fail verification."""
    verifier = IndependentTaskVerifier()
    report = verifier.audit_code_task(
        task_id="task_no_diff",
        git_diff="",
        test_exit_code=0,
    )
    assert report.verified is False
    assert "MISSING_DIFF" in report.rejection_reason


def test_v01_code_task_rejected_with_failing_tests():
    """Declaring code task done when test suite fails must fail verification."""
    verifier = IndependentTaskVerifier()
    diff = "--- a/src/app.py\n+++ b/src/app.py\n@@ -1 +1 @@\n-old\n+new"
    report = verifier.audit_code_task(
        task_id="task_fail_tests",
        git_diff=diff,
        test_exit_code=1,
    )
    assert report.verified is False
    assert "TESTS_FAILED" in report.rejection_reason


def test_v01_code_task_verified_with_diff_and_passing_tests():
    """Code task with diff and passing tests is verified successfully."""
    verifier = IndependentTaskVerifier()
    diff = "--- a/src/app.py\n+++ b/src/app.py\n@@ -1 +1 @@\n-old\n+new"
    report = verifier.audit_code_task(
        task_id="task_verified",
        git_diff=diff,
        test_exit_code=0,
        test_output="10 tests passed",
    )
    assert report.verified is True
    assert report.proof_type == "DIFF_AND_TESTS"
    assert report.proof_hash is not None
