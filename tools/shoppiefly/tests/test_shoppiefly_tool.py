"""Unit Tests for ShoppieFlyBD Read-Only Reporting Client."""

import pytest
from igris_shoppiefly.client import ShoppieFlyReportingClient


def test_shoppiefly_revenue_metrics():
    client = ShoppieFlyReportingClient(use_mock=True)
    metrics = client.get_daily_revenue_metrics("2026-11-15")

    assert metrics.date == "2026-11-15"
    assert metrics.gross_revenue_bdt > 0
    assert metrics.total_orders > 0
    assert metrics.average_order_value_bdt > 0


def test_shoppiefly_top_products():
    client = ShoppieFlyReportingClient(use_mock=True)
    products = client.get_top_selling_products(limit=3)

    assert len(products) == 3
    assert products[0].units_sold >= products[1].units_sold
    assert products[0].stock_quantity > 0


def test_shoppiefly_abandoned_carts():
    client = ShoppieFlyReportingClient(use_mock=True)
    report = client.get_abandoned_carts_report(hours=24)

    assert report.total_abandoned_carts > 0
    assert report.potential_loss_bdt > 0
    assert report.time_window_hours == 24


def test_shoppiefly_order_summary():
    client = ShoppieFlyReportingClient(use_mock=True)
    summary = client.get_order_fulfillment_status()

    assert summary.pending_count >= 0
    assert summary.processing_count >= 0
    assert summary.delivered_count > 0


def test_shoppiefly_mutation_strictly_forbidden():
    client = ShoppieFlyReportingClient(use_mock=True)

    with pytest.raises(PermissionError) as exc_info:
        client.execute_mutation("UPDATE orders SET status='delivered'")

    assert "READ_ONLY_VIOLATION" in str(exc_info.value)

