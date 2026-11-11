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


def test_vlm_client_cascade_fallback_on_api_error(monkeypatch):
    """Verify that when primary model fails, VLMClient falls back to next model."""
    from unittest.mock import MagicMock
    from PIL import Image
    from igris.perception.screen import ScreenFrame

    client = VLMClient(
        api_key="mock_key",
        model_name="failing-model",
        fallback_models=["working-model"],
    )

    calls = []

    def mock_generate_content(model, contents, config):
        calls.append(model)
        if model == "failing-model":
            raise RuntimeError("503 Service Unavailable")
        mock_resp = MagicMock()
        mock_resp.text = '{"action_type": "click", "normalized_x": 100, "normalized_y": 200, "reasoning": "Fallback ok"}'
        return mock_resp

    mock_genai_client = MagicMock()
    mock_genai_client.models.generate_content = mock_generate_content
    monkeypatch.setattr(client, "_get_client", lambda: mock_genai_client)

    img = Image.new("RGB", (100, 100), color="blue")
    frame = ScreenFrame(
        width=100,
        height=100,
        display=":0",
        duration_ms=5.0,
        raw_image=img,
    )
    action = client.predict_action(frame, "test goal")

    assert calls == ["failing-model", "working-model"]
    assert action.action_type == "click"
    assert action.normalized_x == 100
    assert action.reasoning == "Fallback ok"


