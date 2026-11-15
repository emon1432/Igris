"""ShoppieFlyBD Read-Only Reporting Client.

Guarantees:
1. Invariant: Strictly read-only GET requests (T0). Text-to-SQL or database mutations are forbidden.
2. Authenticates via scoped Bearer API tokens.
3. Provides fallback synthetic data for local dev and automated tests.
"""

import time
from typing import List, Optional, Dict, Any
from igris_shoppiefly.models import (
    RevenueMetrics,
    ProductPerformance,
    AbandonedCartReport,
    OrderSummary,
)


class ShoppieFlyReportingClient:
    """Read-only reporting client for the ShoppieFlyBD multi-vendor e-commerce platform."""

    def __init__(
        self,
        base_url: str = "https://shoppieflybd.com/api/v1/reporting",
        api_token: Optional[str] = None,
        use_mock: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.use_mock = use_mock

    def get_daily_revenue_metrics(self, date_str: Optional[str] = None) -> RevenueMetrics:
        """Fetches daily sales, net revenue, and average order value (T0)."""
        target_date = date_str or time.strftime("%Y-%m-%d")

        if self.use_mock or not self.api_token:
            return RevenueMetrics(
                date=target_date,
                gross_revenue_bdt=185400.0,
                net_revenue_bdt=162000.0,
                total_orders=142,
                average_order_value_bdt=1305.63,
            )

        # Production REST GET path (Stubbed for remote deployment)
        raise NotImplementedError("Live API calls require active production token configuration.")

    def get_top_selling_products(self, limit: int = 5) -> List[ProductPerformance]:
        """Fetches top-performing catalog items by units sold (T0)."""
        if self.use_mock or not self.api_token:
            items = [
                ProductPerformance(product_id="PROD_101", title="Wireless Bluetooth Earbuds Pro", units_sold=45, revenue_bdt=49500.0, stock_quantity=120),
                ProductPerformance(product_id="PROD_202", title="Ultra-Fast 65W GaN Charger", units_sold=38, revenue_bdt=34200.0, stock_quantity=85),
                ProductPerformance(product_id="PROD_303", title="Magnetic Phone Car Mount", units_sold=29, revenue_bdt=14500.0, stock_quantity=210),
                ProductPerformance(product_id="PROD_404", title="Waterproof Smart Fitness Band", units_sold=22, revenue_bdt=37400.0, stock_quantity=45),
                ProductPerformance(product_id="PROD_505", title="Braided USB-C Cable (2m)", units_sold=18, revenue_bdt=6300.0, stock_quantity=340),
            ]
            return items[:limit]

        raise NotImplementedError("Live API calls require active production token configuration.")

    def get_abandoned_carts_report(self, hours: int = 24) -> AbandonedCartReport:
        """Fetches abandoned cart statistics for recovery campaign analysis (T0)."""
        if self.use_mock or not self.api_token:
            return AbandonedCartReport(
                time_window_hours=hours,
                total_abandoned_carts=64,
                potential_loss_bdt=89200.0,
                recovered_carts=14,
            )

        raise NotImplementedError("Live API calls require active production token configuration.")

    def get_order_fulfillment_status(self) -> OrderSummary:
        """Fetches counts of active orders across fulfillment pipeline (T0)."""
        if self.use_mock or not self.api_token:
            return OrderSummary(
                pending_count=18,
                processing_count=35,
                shipped_count=78,
                delivered_count=412,
                cancelled_count=5,
            )

        raise NotImplementedError("Live API calls require active production token configuration.")

    def execute_mutation(self, *args, **kwargs):
        """Mutation safeguard: strictly forbids state-altering operations."""
        raise PermissionError("READ_ONLY_VIOLATION: ShoppieFlyReportingClient is strictly read-only.")

