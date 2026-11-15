"""Unit Tests for Telegram Bridge Service and Inline Approval Buttons."""

import pytest
from igris_protocol.models import RiskTier
from igris.remote.approval_manager import ApprovalManager
from igris_telegram.bot import TelegramBridgeService


def test_telegram_send_alert():
    service = TelegramBridgeService(default_chat_id="chat_1234")
    notif = service.send_alert("Build succeeded on staging", priority="HIGH")

    assert notif.chat_id == "chat_1234"
    assert "staging" in notif.text
    assert notif.priority == "HIGH"
    assert len(service.get_sent_alerts()) == 1


def test_telegram_prompt_approval_and_callback():
    appr_mgr = ApprovalManager()
    service = TelegramBridgeService(default_chat_id="chat_1234")

    # Staged T2 action
    req = appr_mgr.create_request(
        task_id="t_tg",
        action_type="deploy_staging",
        risk_tier=RiskTier.T2,
        payload_text="git diff changes for v1.1",
    )

    prompt = service.prompt_approval(req)
    assert prompt.request_id == req.request_id
    assert "IGRIS ACTION APPROVAL REQUIRED" in prompt.formatted_message
    assert len(prompt.inline_buttons) == 1
    assert prompt.inline_buttons[0][0]["callback_data"] == f"appr:{req.request_id}:APPROVE"
    assert prompt.inline_buttons[0][1]["callback_data"] == f"appr:{req.request_id}:REJECT"

    # Simulate operator tapping the Approve inline button
    callback_data = f"appr:{req.request_id}:APPROVE"
    res = service.handle_callback_query(callback_data, appr_mgr)

    assert res["status"] == "CALLBACK_RESOLVED"
    assert res["decision"] == "APPROVE"
    assert res["token_id"] is not None

    # Check that ApprovalToken was issued with SCREEN_BUTTON
    token = appr_mgr.get_token(res["token_id"])
    assert token.granted_by == "SCREEN_BUTTON"


def test_telegram_invalid_callback_format():
    service = TelegramBridgeService()
    appr_mgr = ApprovalManager()

    with pytest.raises(ValueError) as exc_info:
        service.handle_callback_query("invalid_format_string", appr_mgr)

    assert "Invalid callback data format" in str(exc_info.value)

