"""Evaluation Case P-02: Triage Mode Read-Only Guarantee.

Evaluation Objective:
Ensure that when a task session is in TRIAGE mode (e.g. reading emails, checking feeds),
the orchestrator strictly loads read-only tools. Any write-capable tools (file write,
git push, SMTP email send, shell mutations) must not be loaded, and attempts to call
write tools within a TRIAGE session must fail deterministically.
"""

import pytest
from typing import List, Dict, Any


def get_available_tools_for_mode(mode: str) -> List[str]:
    """Contract specification for tool loader across operational modes."""
    read_only_tools = ["read_email", "search_repo", "view_diff", "fetch_report"]
    write_tools = ["send_email", "git_push", "execute_destructive_bash", "write_file"]

    if mode == "TRIAGE":
        return read_only_tools
    elif mode == "WORK":
        return read_only_tools + write_tools
    return []


def evaluate_triage_tool_invocation(mode: str, tool_name: str) -> Dict[str, Any]:
    """Policy engine verification for tool invocation under session mode."""
    available_tools = get_available_tools_for_mode(mode)
    if tool_name not in available_tools:
        return {
            "success": False,
            "error": f"Tool '{tool_name}' is forbidden or not loaded in {mode} mode.",
            "error_code": "FORBIDDEN_TOOL_IN_MODE",
        }
    return {"success": True, "error": None}


def test_p02_triage_mode_only_exposes_read_tools():
    """Triage mode must only load read-only tools."""
    tools = get_available_tools_for_mode("TRIAGE")
    assert "read_email" in tools
    assert "send_email" not in tools
    assert "git_push" not in tools
    assert "execute_destructive_bash" not in tools


def test_p02_triage_mode_blocks_send_email():
    """Calling send_email during Triage mode must be blocked."""
    result = evaluate_triage_tool_invocation("TRIAGE", "send_email")
    assert result["success"] is False
    assert result["error_code"] == "FORBIDDEN_TOOL_IN_MODE"


def test_p02_work_mode_exposes_full_tools():
    """Work mode exposes write tools subject to T1-T3 policies."""
    tools = get_available_tools_for_mode("WORK")
    assert "send_email" in tools
    assert "git_push" in tools
