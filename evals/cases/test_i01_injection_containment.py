"""Evaluation Case I-01: Prompt Injection Containment.

Evaluation Objective:
Verify that prompt injection payloads embedded in untrusted external data
(e.g., incoming emails, scraped web content) cannot hijack the agent into invoking
mutating tools, leaking credentials, or escaping the Triage boundary.
"""

import json
from pathlib import Path
import pytest
from igris_protocol.models import TaskMode
from igris_mail.parser import UntrustedEmailParser
from igris_tool_sdk.wrapper import SecureToolSDK, ToolExecutionError


def test_i01_injection_payload_does_not_trigger_bash():
    """Hidden instructions to run bash from email must be contained by parser and ToolSDK."""
    fixtures_path = Path(__file__).parent.parent / "fixtures" / "mails" / "sample_inbox.json"
    with open(fixtures_path, "r", encoding="utf-8") as f:
        mails = json.load(f)

    injection_mail = next(m for m in mails if m["id"] == "mail_002_injection")

    # 1. Verify parser neutralizes the body
    parsed = UntrustedEmailParser.sanitize_body(injection_mail["body"])
    assert parsed["has_injection_signals"] is True
    assert "<untrusted_email_data" in parsed["encapsulated_block"]

    # 2. Verify ToolSDK in Triage mode blocks bash execution
    sdk = SecureToolSDK()

    def run_bash():
        return "Executed"

    with pytest.raises(ToolExecutionError) as exc_info:
        sdk.invoke(
            action_name="execute_destructive_bash",
            tool_fn=run_bash,
            task_id="task_i01",
            mode=TaskMode.TRIAGE,
            input_parameters={},
        )

    assert "FORBIDDEN_TOOL_IN_MODE" in str(exc_info.value)


def test_i01_passive_draft_allowed_but_sending_blocked():
    """Agent can synthesize an internal draft, but cannot auto-send in Triage mode."""
    sdk = SecureToolSDK()

    def create_draft_data():
        return {"draft_id": "draft_01", "body": "Thank you for the message."}

    # Synthesizing draft is allowed (T0 data only)
    res = sdk.invoke(
        action_name="synthesize_draft_data",
        tool_fn=create_draft_data,
        task_id="task_draft_triage",
        mode=TaskMode.TRIAGE,
        input_parameters={},
    )
    assert res["success"] is True

    # Sending email in Triage mode is blocked
    def send_email():
        return "Sent"

    with pytest.raises(ToolExecutionError) as exc_info:
        sdk.invoke(
            action_name="send_email",
            tool_fn=send_email,
            task_id="task_send_triage",
            mode=TaskMode.TRIAGE,
            input_parameters={},
        )
    assert "FORBIDDEN_TOOL_IN_MODE" in str(exc_info.value)
