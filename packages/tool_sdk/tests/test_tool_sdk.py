"""Unit Tests for Secure Tool SDK Mediation Pipeline."""

import pytest
from igris_protocol.models import RiskTier, TaskMode, ClientScope, ApprovalToken
from igris_tool_sdk.wrapper import SecureToolSDK, ToolExecutionError
from igris_tool_sdk.mock_tools import mock_read_email, mock_deploy_staging, mock_send_email


def test_tool_sdk_t0_execution_and_ledger_log():
    sdk = SecureToolSDK()

    result = sdk.invoke(
        action_name="read_email",
        tool_fn=mock_read_email,
        task_id="task_t0",
        mode=TaskMode.TRIAGE,
        input_parameters={"folder": "INBOX"},
    )

    assert result["success"] is True
    assert result["risk_tier"] == "T0"
    assert sdk.ledger.current_height == 1
    assert sdk.ledger.verify_chain_integrity() is True


def test_tool_sdk_blocks_t3_in_triage():
    sdk = SecureToolSDK()

    with pytest.raises(ToolExecutionError) as exc_info:
        sdk.invoke(
            action_name="send_email",
            tool_fn=mock_send_email,
            task_id="task_triage_leak",
            mode=TaskMode.TRIAGE,
            input_parameters={"to": "client@acme.com", "subject": "Test", "body": "Hello"},
        )

    assert "FORBIDDEN_TOOL_IN_MODE" in str(exc_info.value)
    # The denied attempt must be logged in ledger
    assert sdk.ledger.current_height == 1
    assert "DENIED" in sdk.ledger.get_all_entries()[0].output_summary


def test_tool_sdk_secret_redaction():
    sdk = SecureToolSDK(secrets_to_redact={"api_token": "secret_token_val_999"})

    def tool_with_leak():
        return "Connected with secret_token_val_999 successfully."

    result = sdk.invoke(
        action_name="read_email",
        tool_fn=tool_with_leak,
        task_id="task_leak",
        mode=TaskMode.TRIAGE,
        input_parameters={},
    )

    latest_entry = sdk.ledger.get_all_entries()[-1]
    assert "secret_token_val_999" not in latest_entry.output_summary
    assert "[REDACTED_API_TOKEN]" in latest_entry.output_summary

