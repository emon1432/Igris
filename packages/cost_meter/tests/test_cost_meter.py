"""Unit Tests for Cost Meter & Iteration Limiter."""

import pytest
from igris_cost_meter.limiter import CostMeter, IterationLimitExceededError, BudgetExhaustedError


def test_cost_meter_iteration_limit():
    meter = CostMeter(default_budget_usd=10.0, default_max_iterations=3)
    meter.init_task("task_loop", max_iterations=3)

    meter.record_step("task_loop", step_cost_usd=0.01)
    meter.record_step("task_loop", step_cost_usd=0.01)
    meter.record_step("task_loop", step_cost_usd=0.01)

    with pytest.raises(IterationLimitExceededError):
        meter.record_step("task_loop", step_cost_usd=0.01)


def test_cost_meter_budget_exhaustion():
    meter = CostMeter(default_budget_usd=0.05, default_max_iterations=100)
    meter.init_task("task_budget", budget_usd=0.05)

    meter.record_step("task_budget", step_cost_usd=0.02)
    meter.record_step("task_budget", step_cost_usd=0.02)

    with pytest.raises(BudgetExhaustedError):
        meter.record_step("task_budget", step_cost_usd=0.02)

