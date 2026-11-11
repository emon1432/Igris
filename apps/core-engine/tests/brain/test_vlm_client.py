"""Tests for VLMClient and VisualAction schema."""

from igris.brain.vlm_client import VisualAction, VLMClient


def test_visual_action_schema():
    """Verify VisualAction validation and fields."""
    action = VisualAction(
        action_type="click",
        normalized_x=450,
        normalized_y=320,
        reasoning="Click search button",
        task_completed=False,
    )

    assert action.action_type == "click"
    assert action.normalized_x == 450
    assert action.normalized_y == 320
    assert not action.task_completed


def test_vlm_client_response_parsing():
    """Verify JSON parsing and markdown fence stripping."""
    client = VLMClient(api_key="mock_key")

    raw_json = """```json
    {
        "action_type": "type",
        "normalized_x": 500,
        "normalized_y": 250,
        "text_input": "ShoppieFly Cart",
        "reasoning": "Entering search keyword",
        "task_completed": false
    }
    ```"""

    action = client._parse_response(raw_json)
    assert action.action_type == "type"
    assert action.normalized_x == 500
    assert action.normalized_y == 250
    assert action.text_input == "ShoppieFly Cart"
    assert not action.task_completed


def test_vlm_client_fallback_on_invalid_json():
    """Verify fallback VisualAction when JSON is unparseable."""
    client = VLMClient(api_key="mock_key")

    action = client._parse_response("I think you should click the blue button.")
    assert action.action_type == "wait"
    assert action.normalized_x == 500
    assert "fallback" in action.reasoning.lower()

