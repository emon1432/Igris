"""Evaluation Case C-01: Cost Meter & Budget Limiter.

Evaluation Objective:
Verify that the orchestrator enforces strict iteration and monetary budget limits.
If a task reaches its maximum permitted iteration limit or exceeds allocated dollar spend,
the execution loop is deterministically halted.
"""

import pytest
from typing import Dict, Any


class MockCostMeter:
    """Contract specification for Cost Meter and Loop Budgeting."""

    def __init__(self, budget_usd: float = 1.00, max_iterations: int = 10):
        self.budget_usd = budget_usd
        self.max_iterations = max_iterations
        self.current_spend_usd = 0.0
        self.current_iteration = 0

    def step(self, step_cost_usd: float) -> Dict[str, Any]:
        self.current_iteration += 1
        self.current_spend_usd += step_cost_usd

        if self.current_iteration > self.max_iterations:
            return {
                "halt": True,
                "reason": "MAX_ITERATIONS_EXCEEDED",
                "details": f"Iteration limit of {self.max_iterations} reached.",
            }

        if self.current_spend_usd >= self.budget_usd:
            return {
                "halt": True,
                "reason": "BUDGET_EXHAUSTED",
                "details": f"Budget limit of ${self.budget_usd:.2f} reached.",
            }

        return {"halt": False, "reason": None}


def test_c01_loop_halts_on_iteration_limit():
    """Execution must halt when maximum iteration threshold is passed."""
    meter = MockCostMeter(budget_usd=10.00, max_iterations=3)

    assert meter.step(0.01)["halt"] is False
    assert meter.step(0.01)["halt"] is False
    assert meter.step(0.01)["halt"] is False
    result = meter.step(0.01)
    assert result["halt"] is True
    assert result["reason"] == "MAX_ITERATIONS_EXCEEDED"


def test_c01_loop_halts_on_budget_exhaustion():
    """Execution must halt when monetary token budget is exhausted."""
    meter = MockCostMeter(budget_usd=0.05, max_iterations=50)

    assert meter.step(0.02)["halt"] is False
    assert meter.step(0.02)["halt"] is False
    result = meter.step(0.02)
    assert result["halt"] is True
    assert result["reason"] == "BUDGET_EXHAUSTED"
