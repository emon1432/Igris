"""Evaluation Case P-02: Triage Mode Read-Only Guarantee.

Evaluation Objective:
Ensure that when a task session is in TRIAGE mode (e.g. reading emails, checking feeds),
the Policy Engine strictly permits only T0 read-only tools. Any write-capable tools (file write,
git push, SMTP email send, destructive bash) must fail deterministically.
"""

import pytest
from igris_protocol.models import RiskTier, TaskMode, ClientScope
from igris_policy.engine import evaluate_policy


def test_p02_triage_mode_allows_read_tools():
    """Triage mode permits read-only tools."""
    for tool in ["read_email", "search_repo", "view_diff", "fetch_report"]:
        decision = evaluate_policy(tool, mode=TaskMode.TRIAGE)
        assert decision.allowed is True
        assert decision.risk_tier == RiskTier.T0


def test_p02_triage_mode_blocks_send_email():
    """Calling send_email during Triage mode must be blocked deterministically."""
    decision = evaluate_policy("send_email", mode=TaskMode.TRIAGE)
    assert decision.allowed is False
    assert decision.error_code == "FORBIDDEN_TOOL_IN_MODE"


def test_p02_triage_mode_blocks_destructive_bash():
    """Calling destructive bash commands during Triage mode must be blocked."""
    decision = evaluate_policy("execute_destructive_bash", mode=TaskMode.TRIAGE)
    assert decision.allowed is False
    assert decision.error_code == "FORBIDDEN_TOOL_IN_MODE"


def test_p02_work_mode_permits_write_tools_in_sandbox():
    """Work mode permits local write tools within an isolated client scope."""
    scope = ClientScope(client_id="acme", project_id="web")
    decision = evaluate_policy("write_file", mode=TaskMode.WORK, scope=scope)
    assert decision.allowed is True
    assert decision.risk_tier == RiskTier.T1
