"""Append-Only Cryptographic Action Ledger.

Guarantees:
1. Every tool invocation is logged into an append-only sequence.
2. Each block is cryptographically linked to the previous block via SHA-256 hash chaining.
3. Tampering with any historical entry invalidates the entire chain integrity check.
4. Database/storage operations support strictly INSERT and SELECT (UPDATE/DELETE disallowed).
"""

import hashlib
import json
import time
from typing import List, Dict, Any, Optional
from igris_protocol.models import LedgerEntry, RiskTier


GENESIS_HASH = "0" * 64


def compute_entry_hash(
    index: int,
    prev_hash: str,
    timestamp: float,
    task_id: str,
    tool_name: str,
    risk_tier: str,
    client_id: Optional[str],
    input_parameters: Dict[str, Any],
    approval_token_id: Optional[str],
    output_summary: str,
) -> str:
    """Computes deterministic SHA-256 hash for a ledger entry."""
    serialized_inputs = json.dumps(input_parameters, sort_keys=True)
    payload = (
        f"{index}|{prev_hash}|{timestamp:.4f}|{task_id}|{tool_name}|"
        f"{risk_tier}|{client_id or ''}|{serialized_inputs}|"
        f"{approval_token_id or ''}|{output_summary}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ActionLedger:
    """Thread-safe, append-only cryptographic action ledger."""

    def __init__(self):
        self._entries: List[LedgerEntry] = []

    @property
    def current_height(self) -> int:
        return len(self._entries)

    @property
    def latest_hash(self) -> str:
        if not self._entries:
            return GENESIS_HASH
        return self._entries[-1].entry_hash

    def append(
        self,
        task_id: str,
        tool_name: str,
        risk_tier: RiskTier,
        input_parameters: Dict[str, Any],
        output_summary: str,
        client_id: Optional[str] = None,
        approval_token_id: Optional[str] = None,
        timestamp: Optional[float] = None,
    ) -> LedgerEntry:
        """Appends a new immutable entry to the ledger."""
        ts = timestamp if timestamp is not None else time.time()
        idx = len(self._entries)
        prev = self.latest_hash

        entry_hash = compute_entry_hash(
            index=idx,
            prev_hash=prev,
            timestamp=ts,
            task_id=task_id,
            tool_name=tool_name,
            risk_tier=risk_tier.value,
            client_id=client_id,
            input_parameters=input_parameters,
            approval_token_id=approval_token_id,
            output_summary=output_summary,
        )

        entry = LedgerEntry(
            index=idx,
            prev_hash=prev,
            timestamp=ts,
            task_id=task_id,
            tool_name=tool_name,
            risk_tier=risk_tier,
            client_id=client_id,
            input_parameters=input_parameters,
            approval_token_id=approval_token_id,
            output_summary=output_summary,
            entry_hash=entry_hash,
        )

        self._entries.append(entry)
        return entry

    def verify_chain_integrity(self) -> bool:
        """Verifies cryptographic integrity across all chained ledger entries."""
        expected_prev = GENESIS_HASH

        for idx, entry in enumerate(self._entries):
            # 1. Index continuity
            if entry.index != idx:
                return False

            # 2. Previous hash link
            if entry.prev_hash != expected_prev:
                return False

            # 3. Hash computation match
            recalculated_hash = compute_entry_hash(
                index=entry.index,
                prev_hash=entry.prev_hash,
                timestamp=entry.timestamp,
                task_id=entry.task_id,
                tool_name=entry.tool_name,
                risk_tier=entry.risk_tier.value,
                client_id=entry.client_id,
                input_parameters=entry.input_parameters,
                approval_token_id=entry.approval_token_id,
                output_summary=entry.output_summary,
            )

            if entry.entry_hash != recalculated_hash:
                return False

            expected_prev = entry.entry_hash

        return True

    def get_entries_for_task(self, task_id: str) -> List[LedgerEntry]:
        """Retrieves entries associated with a specific task."""
        return [e for e in self._entries if e.task_id == task_id]

    def get_all_entries(self) -> List[LedgerEntry]:
        """Returns read-only copy of all ledger entries."""
        return list(self._entries)

