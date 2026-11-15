"""Unit Tests for Independent Task Verifier."""

import pytest
from igris.brain.verifier import IndependentTaskVerifier


def test_verifier_rejects_empty_diff():
    verifier = IndependentTaskVerifier()
    report = verifier.audit_code_task(
        task_id="t1",
        git_diff="",
        test_exit_code=0,
    )
    assert report.verified is False
    assert "MISSING_DIFF" in report.rejection_reason


def test_verifier_rejects_failing_tests():
    verifier = IndependentTaskVerifier()
    diff = "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new"
    report = verifier.audit_code_task(
        task_id="t2",
        git_diff=diff,
        test_exit_code=1,
    )
    assert report.verified is False
    assert "TESTS_FAILED" in report.rejection_reason


def test_verifier_accepts_clean_diff_and_passing_tests():
    verifier = IndependentTaskVerifier()
    diff = "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new"
    report = verifier.audit_code_task(
        task_id="t3",
        git_diff=diff,
        test_exit_code=0,
        test_output="3 passed in 0.05s",
    )
    assert report.verified is True
    assert report.proof_type == "DIFF_AND_TESTS"
    assert report.proof_hash is not None
    assert len(report.proof_hash) == 64

