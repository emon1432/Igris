"""Unit Tests for Local PC Operator Tool."""

from unittest.mock import MagicMock
import pytest
from igris.perception.accessibility import AccessibleElement, BoundingBox
from igris_local_pc.operator import LocalPCOperator


@pytest.fixture
def mock_operator():
    mock_inspector = MagicMock()
    mock_driver = MagicMock()

    mock_inspector.query_elements.return_value = [
        AccessibleElement(
            role="push_button",
            name="Submit Order",
            description="",
            bounds=BoundingBox(x=100, y=200, width=80, height=40),
            states=["visible", "enabled"],
            actions=["click"],
        ),
        AccessibleElement(
            role="push_button",
            name="Cancel",
            description="",
            bounds=BoundingBox(x=200, y=200, width=60, height=40),
            states=["visible", "enabled"],
            actions=["click"],
        ),
    ]

    return LocalPCOperator(inspector=mock_inspector, input_driver=mock_driver)


def test_operator_find_button_center(mock_operator):
    center = mock_operator.find_button_center("Submit Order")
    assert center is not None
    # 100 + 80 // 2 = 140; 200 + 40 // 2 = 220
    assert center["x"] == 140
    assert center["y"] == 220


def test_operator_inspect_ui_tree(mock_operator):
    elements = mock_operator.inspect_ui_tree()
    assert len(elements) == 2
    assert elements[0]["name"] == "Submit Order"


def test_operator_click_and_type(mock_operator):
    click_res = mock_operator.click_virtual_coordinate(140, 220, display=":99")
    assert click_res["status"] == "CLICK_DISPATCHED"
    assert click_res["display"] == ":99"
    mock_operator.input_driver.click.assert_called_once_with(140, 220, display=":99")

    type_res = mock_operator.type_virtual_text("hello igris", display=":99")
    assert type_res["status"] == "TEXT_TYPED"
    mock_operator.input_driver.type_text.assert_called_once_with("hello igris", display=":99")

