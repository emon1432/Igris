"""Data Models for ShoppieFlyBD Analytics & Reporting."""

from typing import List, Optional
from pydantic import BaseModel


class RevenueMetrics(BaseModel):
    """Daily revenue and transaction performance."""
    date: str
    gross_revenue_bdt: float
    net_revenue_bdt: float
    total_orders: int
    average_order_value_bdt: float


class ProductPerformance(BaseModel):
    """Item sales metrics and inventory status."""
    product_id: str
    title: str
    units_sold: int
    revenue_bdt: float
    stock_quantity: int


class AbandonedCartReport(BaseModel):
    """Abandoned checkout analysis."""
    time_window_hours: int
    total_abandoned_carts: int
    potential_loss_bdt: float
    recovered_carts: int = 0


class OrderSummary(BaseModel):
    """Real-time order pipeline status."""
    pending_count: int
    processing_count: int
    shipped_count: int
    delivered_count: int
    cancelled_count: int

