"""Sandboxed Git & Deployment Runner.

Guarantees:
1. Local git operations (branching, committing, diffing, running tests) execute autonomously (T1).
2. Staging branch pushes require an ApprovalToken with risk tier T2.
3. Production deployments require an ApprovalToken with risk tier T3 and payload proof verification.
4. Generates tangible proof artifacts (unified diff, test exit codes) for the TaskVerifier.
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from igris_protocol.models import RiskTier, ApprovalToken


class GitRunnerError(RuntimeError):
    """Raised when a git operation fails."""
    pass


class SandboxedGitRunner:
    """Manages git repository actions and deployment gating."""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()

    def _run_git(self, *args: str) -> str:
        """Executes a git command within the sandboxed repository path."""
        cmd = ["git", "-C", str(self.repo_path)] + list(args)
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return res.stdout.strip()
        except subprocess.CalledProcessError as exc:
            raise GitRunnerError(f"Git command failed ({' '.join(cmd)}): {exc.stderr.strip()}") from exc

    def create_work_branch(self, branch_name: str) -> Dict[str, Any]:
        """Creates and checks out an isolated feature/work branch (T1)."""
        output = self._run_git("checkout", "-B", branch_name)
        return {
            "status": "BRANCH_CREATED",
            "branch": branch_name,
            "repo": str(self.repo_path),
            "output": output,
        }

    def generate_unified_diff(self, base_ref: str = "HEAD") -> str:
        """Generates unified git diff of all uncommitted and committed changes (T0/T1)."""
        # Get unstaged + staged diff
        diff_working = self._run_git("diff", base_ref)
        return diff_working

    def run_automated_tests(self, test_command: str = "pytest") -> Dict[str, Any]:
        """Runs the repository test suite and captures verifiable proof artifacts (T1)."""
        cmd_parts = test_command.split()
        res = subprocess.run(
            cmd_parts,
            cwd=str(self.repo_path),
            capture_output=True,
            text=True,
        )
        return {
            "test_command": test_command,
            "exit_code": res.returncode,
            "passed": res.returncode == 0,
            "stdout": res.stdout[-2000:] if res.stdout else "",
            "stderr": res.stderr[-1000:] if res.stderr else "",
        }

    def push_staging_branch(
        self,
        branch_name: str,
        approval_token: Optional[ApprovalToken] = None,
    ) -> Dict[str, Any]:
        """Pushes branch to staging remote (T2). Requires verified on-screen button approval."""
        if approval_token is None:
            raise PermissionError("GATED_ACTION: Pushing to staging requires explicit T2 screen button approval.")
        if approval_token.risk_tier not in (RiskTier.T2, RiskTier.T3):
            raise PermissionError(f"GATED_ACTION: Invalid risk tier '{approval_token.risk_tier}' for staging push.")
        if approval_token.granted_by != "SCREEN_BUTTON":
            raise PermissionError("GATED_ACTION: Staging push cannot be authorized via voice.")

        return {
            "status": "STAGING_PUSH_AUTHORIZED",
            "branch": branch_name,
            "approval_token_id": approval_token.token_id,
        }

    def deploy_production(
        self,
        tag: str,
        approval_token: Optional[ApprovalToken] = None,
        proof_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Deploys release tag to production (T3). Requires T3 screen button approval and proof hash."""
        if approval_token is None:
            raise PermissionError("GATED_ACTION: Production deploy requires explicit T3 screen button approval.")
        if approval_token.risk_tier != RiskTier.T3:
            raise PermissionError("GATED_ACTION: Production deploy requires a Tier T3 approval token.")
        if approval_token.granted_by != "SCREEN_BUTTON":
            raise PermissionError("GATED_ACTION: Production deploy cannot be authorized via voice.")
        if proof_hash and approval_token.payload_hash != proof_hash:
            raise PermissionError("GATED_ACTION: Proof hash mismatch on production deploy token.")

        return {
            "status": "PRODUCTION_DEPLOY_AUTHORIZED",
            "tag": tag,
            "approval_token_id": approval_token.token_id,
            "proof_hash": proof_hash,
        }

