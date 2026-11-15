"""Independent Task Verifier Subsystem.

Role & Invariant (V-01):
The Builder agent is strictly prohibited from certifying its own completion.
This Independent Task Verifier audits tangible proof packages (diffs, test logs, screenshots)
against initial prompt specifications before transitioning any task to 'COMPLETED'.
"""

import hashlib
from typing import Dict, Any, Optional
from pydantic import BaseModel


class VerificationReport(BaseModel):
    """Formal audit report issued by the Independent Task Verifier."""
    verified: bool
    task_id: str
    task_type: str
    proof_type: Optional[str] = None
    proof_hash: Optional[str] = None
    rejection_reason: Optional[str] = None


class IndependentTaskVerifier:
    """Audits proof packages to ensure work is verified before completion."""

    @staticmethod
    def compute_proof_hash(payload: str) -> str:
        """Computes cryptographic hash of proof payload."""
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def audit_code_task(
        self,
        task_id: str,
        git_diff: Optional[str],
        test_exit_code: Optional[int],
        test_output: Optional[str] = None,
        lint_exit_code: Optional[int] = None,
    ) -> VerificationReport:
        """Audits code modification task outputs."""
        # 1. Non-empty diff check
        if not git_diff or len(git_diff.strip()) == 0:
            return VerificationReport(
                verified=False,
                task_id=task_id,
                task_type="CODE_CHANGE",
                rejection_reason="MISSING_DIFF: Code modification task has no unified git diff.",
            )

        # 2. Automated tests passing check
        if test_exit_code is None:
            return VerificationReport(
                verified=False,
                task_id=task_id,
                task_type="CODE_CHANGE",
                rejection_reason="MISSING_TEST_RUN: Automated test run evidence not provided.",
            )

        if test_exit_code != 0:
            return VerificationReport(
                verified=False,
                task_id=task_id,
                task_type="CODE_CHANGE",
                rejection_reason=f"TESTS_FAILED: Automated test suite exited with code {test_exit_code}.",
            )

        # 3. Linter check (if provided)
        if lint_exit_code is not None and lint_exit_code != 0:
            return VerificationReport(
                verified=False,
                task_id=task_id,
                task_type="CODE_CHANGE",
                rejection_reason=f"LINT_FAILED: Linter exited with code {lint_exit_code}.",
            )

        proof_summary = f"{git_diff}\n---TESTS---\n{test_output or ''}"
        return VerificationReport(
            verified=True,
            task_id=task_id,
            task_type="CODE_CHANGE",
            proof_type="DIFF_AND_TESTS",
            proof_hash=self.compute_proof_hash(proof_summary),
        )

    def audit_ui_task(
        self,
        task_id: str,
        screenshot_before: Optional[str],
        screenshot_after: Optional[str],
    ) -> VerificationReport:
        """Audits UI/web modification task outputs."""
        if not screenshot_after:
            return VerificationReport(
                verified=False,
                task_id=task_id,
                task_type="UI_CHANGE",
                rejection_reason="MISSING_SCREENSHOT_PROOF: No post-execution visual frame provided.",
            )

        proof_payload = f"{screenshot_before or ''}|{screenshot_after}"
        return VerificationReport(
            verified=True,
            task_id=task_id,
            task_type="UI_CHANGE",
            proof_type="SCREENSHOT_COMPARISON",
            proof_hash=self.compute_proof_hash(proof_payload),
        )

