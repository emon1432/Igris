"""Evaluation Case C-01: Cost Meter & Budget Limiter.

Evaluation Objective:
Verify that the orchestrator enforces strict iteration and monetary budget limits.
If a task reaches its maximum permitted iteration limit or exceeds allocated dollar spend,
the execution loop is deterministically halted with a runtime error.
"""

import pytest
from igris_cost_meter.limiter import CostMeter, IterationLimitExceededError, BudgetExhaustedError


def test_c01_loop_halts_on_iteration_limit():
    """Execution must halt with IterationLimitExceededError when iteration limit is reached."""
    meter = CostMeter(default_budget_usd=10.00, default_max_iterations=3)
    meter.init_task("task_001", max_iterations=3)

    assert meter.record_step("task_001", step_cost_usd=0.01)["iteration"] == 1
    assert meter.record_step("task_001", step_cost_usd=0.01)["iteration"] == 2
    assert meter.record_step("task_001", step_cost_usd=0.01)["iteration"] == 3

    with pytest.raises(IterationLimitExceededError) as exc_info:
        meter.record_step("task_001", step_cost_usd=0.01)

    assert "exceeded max iteration limit" in str(exc_info.value)


def test_c01_loop_halts_on_budget_exhaustion():
    """Execution must halt with BudgetExhaustedError when dollar spend limit is exceeded."""
    meter = CostMeter(default_budget_usd=0.05, default_max_iterations=50)
    meter.init_task("task_002", budget_usd=0.05)

    meter.record_step("task_002", step_cost_usd=0.02)
    meter.record_step("task_002", step_cost_usd=0.02)

    with pytest.raises(BudgetExhaustedError) as exc_info:
        meter.record_step("task_002", step_cost_usd=0.02)

    assert "exhausted allocated budget" in str(exc_info.value)
