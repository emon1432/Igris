"""Tool SDK Wrapper & Mediation Layer.

CI Invariant:
The Orchestrator must never call tools directly. All tool invocations must route
strictly through this SecureToolSDK wrapper, which deterministically enforces:
1. Kill switch health check
2. Cost meter & iteration consumption
3. Pure-code policy check (T0-T3 risk tiers, mode boundaries, approval tokens)
4. Append-only ledger recording
5. Secret redaction on outputs
"""

import time
from typing import Callable, Dict, Any, Optional
from igris_protocol.models import RiskTier, TaskMode, ClientScope, ApprovalToken, LedgerEntry
from igris_policy.engine import evaluate_policy, PolicyDecision
from igris_ledger.ledger import ActionLedger
from igris_kill_switch.manager import KillSwitchManager, global_kill_switch
from igris_cost_meter.limiter import CostMeter


class ToolExecutionError(RuntimeError):
    """Raised when tool execution is denied by policy or fails execution."""
    pass


class SecureToolSDK:
    """Centralized mediation SDK executing all tools under strict policy and audit guardrails."""

    def __init__(
        self,
        ledger: Optional[ActionLedger] = None,
        kill_switch: Optional[KillSwitchManager] = None,
        cost_meter: Optional[CostMeter] = None,
        secrets_to_redact: Optional[Dict[str, str]] = None,
    ):
        self.ledger = ledger or ActionLedger()
        self.kill_switch = kill_switch or global_kill_switch
        self.cost_meter = cost_meter or CostMeter()
        self.secrets_to_redact = secrets_to_redact or {}

    def sanitize_text(self, text: str) -> str:
        """Redacts sensitive values before output is returned or logged."""
        sanitized = text
        for name, val in self.secrets_to_redact.items():
            if val and len(val) > 3:
                sanitized = sanitized.replace(val, f"[REDACTED_{name.upper()}]")
        return sanitized

    def invoke(
        self,
        action_name: str,
        tool_fn: Callable[..., Any],
        task_id: str,
        mode: TaskMode,
        input_parameters: Dict[str, Any],
        scope: Optional[ClientScope] = None,
        approval_token: Optional[ApprovalToken] = None,
        step_cost_usd: float = 0.001,
        explicit_tier: Optional[RiskTier] = None,
        payload_hash: Optional[str] = None,
        current_time: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Executes a tool under deterministic policy and audit enforcement.

        Pipeline:
        1. Assert Kill Switch is not active.
        2. Advance Cost Meter & Iteration Limiter.
        3. Evaluate Policy Engine.
        4. Execute tool in sandbox.
        5. Append execution record to immutable Action Ledger.
        6. Return sanitized result.
        """
        now = current_time if current_time is not None else time.time()

        # 1. Kill Switch Check
        self.kill_switch.assert_healthy()

        # 2. Cost Meter Step
        self.cost_meter.record_step(task_id, step_cost_usd)

        # 3. Policy Engine Evaluation
        decision: PolicyDecision = evaluate_policy(
            action_name=action_name,
            mode=mode,
            scope=scope,
            approval_token=approval_token,
            current_time=now,
            explicit_tier=explicit_tier,
            payload_hash=payload_hash,
        )

        if not decision.allowed:
            # Policy failed: Record attempted violation in ledger for audit
            self.ledger.append(
                task_id=task_id,
                tool_name=action_name,
                risk_tier=decision.risk_tier or RiskTier.T3,
                client_id=scope.client_id if scope else None,
                input_parameters=input_parameters,
                approval_token_id=approval_token.token_id if approval_token else None,
                output_summary=f"DENIED by policy: {decision.error_code} - {decision.reason}",
                timestamp=now,
            )
            raise ToolExecutionError(f"POLICY_DENIED [{decision.error_code}]: {decision.reason}")

        # 4. Tool Execution
        try:
            raw_result = tool_fn(**input_parameters)
        except Exception as exc:
            summary = f"EXECUTION_FAILED: {str(exc)}"
            self.ledger.append(
                task_id=task_id,
                tool_name=action_name,
                risk_tier=decision.risk_tier or RiskTier.T0,
                client_id=scope.client_id if scope else None,
                input_parameters=input_parameters,
                approval_token_id=approval_token.token_id if approval_token else None,
                output_summary=summary,
                timestamp=now,
            )
            raise

        # 5. Sanitize Output
        sanitized_summary = self.sanitize_text(str(raw_result))

        # 6. Append Successful Call to Immutable Ledger
        ledger_entry: LedgerEntry = self.ledger.append(
            task_id=task_id,
            tool_name=action_name,
            risk_tier=decision.risk_tier or RiskTier.T0,
            client_id=scope.client_id if scope else None,
            input_parameters=input_parameters,
            approval_token_id=approval_token.token_id if approval_token else None,
            output_summary=sanitized_summary[:500],
            timestamp=now,
        )

        return {
            "success": True,
            "action_name": action_name,
            "risk_tier": decision.risk_tier.value if decision.risk_tier else None,
            "result": raw_result,
            "ledger_entry_hash": ledger_entry.entry_hash,
            "ledger_index": ledger_entry.index,
        }

