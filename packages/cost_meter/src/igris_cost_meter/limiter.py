"""Cost Meter & Iteration Limiter Subsystem.

Guarantees:
1. Every task execution step consumes iterations and tracks token/dollar cost.
2. If a task exceeds its allocated maximum iterations, execution is halted deterministically.
3. If spend exceeds the allocated dollar budget, execution is halted deterministically.
"""

from typing import Dict, Any, Optional


class IterationLimitExceededError(RuntimeError):
    """Raised when a task exceeds its maximum allowed reasoning iterations."""
    pass


class BudgetExhaustedError(RuntimeError):
    """Raised when a task exceeds its allocated financial spend budget."""
    pass


class TaskBudgetState:
    """Tracks state and consumption for a specific task."""

    def __init__(self, task_id: str, budget_usd: float = 1.00, max_iterations: int = 25):
        self.task_id = task_id
        self.budget_usd = budget_usd
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.current_spend_usd = 0.0

    def record_step(self, step_cost_usd: float = 0.0) -> Dict[str, Any]:
        """Records an execution step and validates budget boundaries."""
        self.current_iteration += 1
        self.current_spend_usd += step_cost_usd

        if self.current_iteration > self.max_iterations:
            raise IterationLimitExceededError(
                f"Task '{self.task_id}' exceeded max iteration limit ({self.max_iterations})."
            )

        if self.current_spend_usd >= self.budget_usd:
            raise BudgetExhaustedError(
                f"Task '{self.task_id}' exhausted allocated budget (${self.budget_usd:.2f}). "
                f"Current spend: ${self.current_spend_usd:.4f}."
            )

        return {
            "task_id": self.task_id,
            "iteration": self.current_iteration,
            "spend_usd": self.current_spend_usd,
            "remaining_budget_usd": max(0.0, self.budget_usd - self.current_spend_usd),
        }


class CostMeter:
    """Manages budgets across active tasks."""

    def __init__(self, default_budget_usd: float = 1.00, default_max_iterations: int = 25):
        self.default_budget_usd = default_budget_usd
        self.default_max_iterations = default_max_iterations
        self._tasks: Dict[str, TaskBudgetState] = {}

    def init_task(
        self,
        task_id: str,
        budget_usd: Optional[float] = None,
        max_iterations: Optional[int] = None,
    ) -> TaskBudgetState:
        """Initializes budget tracking for a task."""
        state = TaskBudgetState(
            task_id=task_id,
            budget_usd=budget_usd if budget_usd is not None else self.default_budget_usd,
            max_iterations=max_iterations if max_iterations is not None else self.default_max_iterations,
        )
        self._tasks[task_id] = state
        return state

    def record_step(self, task_id: str, step_cost_usd: float = 0.0) -> Dict[str, Any]:
        """Records a step for a task, creating a default budget if not explicitly initialized."""
        if task_id not in self._tasks:
            self.init_task(task_id)
        return self._tasks[task_id].record_step(step_cost_usd)

    def get_task_spend(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Returns spend metrics for a task."""
        state = self._tasks.get(task_id)
        if not state:
            return None
        return {
            "task_id": state.task_id,
            "iteration": state.current_iteration,
            "max_iterations": state.max_iterations,
            "spend_usd": state.current_spend_usd,
            "budget_usd": state.budget_usd,
        }

