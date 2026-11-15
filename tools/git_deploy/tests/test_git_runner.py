"""Unit Tests for Sandboxed Git Runner & Deployment Gating."""

import subprocess
import pytest
from igris_protocol.models import RiskTier, ApprovalToken
from igris_git_tool.git_runner import SandboxedGitRunner


@pytest.fixture
def temp_git_repo(tmp_path):
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    subprocess.run(["git", "init"], cwd=str(repo_dir), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=str(repo_dir), check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(repo_dir), check=True)

    test_file = repo_dir / "app.py"
    test_file.write_text("print('hello world')\n")
    subprocess.run(["git", "add", "."], cwd=str(repo_dir), check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=str(repo_dir), check=True)

    return SandboxedGitRunner(str(repo_dir)), repo_dir


def test_git_branch_and_diff(temp_git_repo):
    runner, repo_dir = temp_git_repo

    # Create work branch
    res = runner.create_work_branch("feature/phase-2-test")
    assert res["status"] == "BRANCH_CREATED"
    assert res["branch"] == "feature/phase-2-test"

    # Make a change
    (repo_dir / "app.py").write_text("print('hello phase 2')\n")

    # Generate unified diff
    diff = runner.generate_unified_diff()
    assert "-print('hello world')" in diff
    assert "+print('hello phase 2')" in diff


def test_git_staging_push_requires_t2_button_approval(temp_git_repo):
    runner, _ = temp_git_repo

    # No token -> fail
    with pytest.raises(PermissionError) as exc_info:
        runner.push_staging_branch("feature/phase-2-test", approval_token=None)
    assert "GATED_ACTION" in str(exc_info.value)

    # Voice token -> fail
    voice_token = ApprovalToken(
        token_id="tok_v",
        task_id="t1",
        action_type="push_staging",
        risk_tier=RiskTier.T2,
        payload_hash="hash",
        granted_at=100.0,
        granted_by="VOICE",
        expires_at=200.0,
    )
    with pytest.raises(PermissionError) as exc_info:
        runner.push_staging_branch("feature/phase-2-test", approval_token=voice_token)
    assert "cannot be authorized via voice" in str(exc_info.value)

    # Screen button token -> pass
    screen_token = ApprovalToken(
        token_id="tok_s",
        task_id="t1",
        action_type="push_staging",
        risk_tier=RiskTier.T2,
        payload_hash="hash",
        granted_at=100.0,
        granted_by="SCREEN_BUTTON",
        expires_at=200.0,
    )
    res = runner.push_staging_branch("feature/phase-2-test", approval_token=screen_token)
    assert res["status"] == "STAGING_PUSH_AUTHORIZED"

